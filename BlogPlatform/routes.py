"""
All application routes, organized into Flask blueprints:

    pages_bp    -> Server-rendered HTML pages (home, dashboard, etc.)
    auth_bp     -> Registration / login / logout
    posts_bp    -> REST API for blog posts (JSON)
    comments_bp -> REST API for comments (JSON)
    profile_bp  -> Profile view + update
"""

import os
import re
import uuid

from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, jsonify, current_app, abort
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from models import db, User, BlogPost, Comment

pages_bp = Blueprint("pages", __name__)
auth_bp = Blueprint("auth", __name__)
posts_bp = Blueprint("posts", __name__)
comments_bp = Blueprint("comments", __name__)
profile_bp = Blueprint("profile", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def validate_password(password):
    """Require at least 8 chars, one letter, and one number."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


def save_uploaded_image(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported image type. Use PNG, JPG, JPEG, GIF, or WEBP.")
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file_storage.save(filepath)
    return filename


# --------------------------------------------------------------------------
# Page routes (HTML)
# --------------------------------------------------------------------------

@pages_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    category = request.args.get("category", "", type=str).strip()

    query = BlogPost.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(BlogPost.title.ilike(like), BlogPost.category.ilike(like))
        )
    if category:
        query = query.filter(BlogPost.category == category)

    query = query.order_by(BlogPost.created_at.desc())
    pagination = query.paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )

    popular_posts = BlogPost.query.all()
    popular_posts.sort(key=lambda p: p.like_count, reverse=True)
    popular_posts = popular_posts[:5]

    recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
    categories = [c[0] for c in db.session.query(BlogPost.category).distinct().all()]

    return render_template(
        "index.html",
        posts=pagination.items,
        pagination=pagination,
        popular_posts=popular_posts,
        recent_posts=recent_posts,
        categories=categories,
        search=search,
        selected_category=category,
    )


@pages_bp.route("/dashboard")
@login_required
def dashboard():
    posts = (
        BlogPost.query.filter_by(user_id=current_user.id)
        .order_by(BlogPost.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", posts=posts)


@pages_bp.route("/posts/create")
@login_required
def create_post_page():
    return render_template("create_post.html")


@pages_bp.route("/posts/<int:post_id>/edit")
@login_required
def edit_post_page(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        abort(404)
    if post.user_id != current_user.id:
        flash("You can only edit your own posts.", "error")
        return redirect(url_for("pages.index"))
    return render_template("edit_post.html", post=post)


@pages_bp.route("/posts/<int:post_id>")
def view_post(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        abort(404)
    comments = post.comments.order_by(Comment.created_at.desc()).all()
    return render_template("post.html", post=post, comments=comments)


@pages_bp.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("pages.index"))
    return render_template("login.html")


@pages_bp.route("/register")
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("pages.index"))
    return render_template("register.html")


# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    errors = []
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters long.")
    if not EMAIL_RE.match(email):
        errors.append("Please provide a valid email address.")
    if not validate_password(password):
        errors.append("Password must be at least 8 characters and include a letter and a number.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if User.query.filter_by(username=username).first():
        errors.append("That username is already taken.")
    if User.query.filter_by(email=email).first():
        errors.append("That email is already registered.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("pages.register_page"))

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    flash(f"Welcome to BlogPlatform, {user.username}!", "success")
    return redirect(url_for("pages.index"))


@auth_bp.route("/login", methods=["POST"])
def login():
    identifier = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    remember = bool(request.form.get("remember"))

    user = User.query.filter(
        db.or_(User.username == identifier, User.email == identifier.lower())
    ).first()

    if user is None or not user.check_password(password):
        flash("Invalid username/email or password.", "error")
        return redirect(url_for("pages.login_page"))

    login_user(user, remember=remember)
    flash(f"Welcome back, {user.username}!", "success")
    next_page = request.args.get("next")
    return redirect(next_page or url_for("pages.index"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("pages.index"))


# --------------------------------------------------------------------------
# Posts REST API
# --------------------------------------------------------------------------

@posts_bp.route("/api/posts", methods=["GET"])
def get_posts():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    category = request.args.get("category", "", type=str).strip()

    query = BlogPost.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(BlogPost.title.ilike(like), BlogPost.category.ilike(like))
        )
    if category:
        query = query.filter(BlogPost.category == category)

    query = query.order_by(BlogPost.created_at.desc())
    pagination = query.paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    uid = current_user.id if current_user.is_authenticated else None
    return jsonify({
        "posts": [p.to_dict(uid) for p in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
    })


@posts_bp.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    uid = current_user.id if current_user.is_authenticated else None
    return jsonify(post.to_dict(uid))


@posts_bp.route("/api/posts", methods=["POST"])
@login_required
def create_post():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "General").strip() or "General"
    image = request.files.get("image")

    if not title or not content:
        return jsonify({"error": "Title and content are required."}), 400
    if len(title) > 200:
        return jsonify({"error": "Title must be under 200 characters."}), 400

    filename = None
    if image and image.filename:
        try:
            filename = save_uploaded_image(image)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    post = BlogPost(
        title=title,
        content=content,
        category=category,
        image_filename=filename,
        user_id=current_user.id,
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict(current_user.id)), 201


@posts_bp.route("/api/posts/<int:post_id>", methods=["PUT"])
@login_required
def update_post(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    if post.user_id != current_user.id:
        return jsonify({"error": "You can only edit your own posts."}), 403

    title = request.form.get("title", post.title).strip()
    content = request.form.get("content", post.content).strip()
    category = request.form.get("category", post.category).strip()
    image = request.files.get("image")

    if not title or not content:
        return jsonify({"error": "Title and content are required."}), 400

    if image and image.filename:
        try:
            post.image_filename = save_uploaded_image(image)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    post.title = title
    post.content = content
    post.category = category or "General"
    db.session.commit()
    return jsonify(post.to_dict(current_user.id))


@posts_bp.route("/api/posts/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    if post.user_id != current_user.id:
        return jsonify({"error": "You can only delete your own posts."}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully."})


@posts_bp.route("/api/posts/<int:post_id>/like", methods=["POST"])
@login_required
def toggle_like(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
        liked = False
    else:
        post.liked_by.append(current_user)
        liked = True
    db.session.commit()
    return jsonify({"liked": liked, "like_count": post.like_count})


# --------------------------------------------------------------------------
# Comments REST API
# --------------------------------------------------------------------------

@comments_bp.route("/api/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    comments = post.comments.order_by(Comment.created_at.desc()).all()
    return jsonify([c.to_dict() for c in comments])


@comments_bp.route("/api/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json(silent=True) or request.form
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Comment cannot be empty."}), 400
    if len(content) > 1000:
        return jsonify({"error": "Comment is too long (max 1000 characters)."}), 400

    comment = Comment(content=content, user_id=current_user.id, post_id=post.id)
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@comments_bp.route("/api/comments/<int:comment_id>", methods=["PUT"])
@login_required
def update_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return jsonify({"error": "Comment not found"}), 404
    if comment.user_id != current_user.id:
        return jsonify({"error": "You can only edit your own comments."}), 403

    data = request.get_json(silent=True) or request.form
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Comment cannot be empty."}), 400

    comment.content = content
    db.session.commit()
    return jsonify(comment.to_dict())


@comments_bp.route("/api/comments/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return jsonify({"error": "Comment not found"}), 404
    if comment.user_id != current_user.id:
        return jsonify({"error": "You can only delete your own comments."}), 403
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted successfully."})


# --------------------------------------------------------------------------
# Profile routes
# --------------------------------------------------------------------------

@profile_bp.route("/profile")
@login_required
def profile():
    posts = (
        BlogPost.query.filter_by(user_id=current_user.id)
        .order_by(BlogPost.created_at.desc())
        .all()
    )
    return render_template("profile.html", posts=posts)


@profile_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    email = request.form.get("email", "").strip().lower()
    bio = request.form.get("bio", "").strip()
    new_password = request.form.get("new_password", "").strip()

    if not EMAIL_RE.match(email):
        flash("Please provide a valid email address.", "error")
        return redirect(url_for("profile.profile"))

    existing = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing:
        flash("That email is already in use by another account.", "error")
        return redirect(url_for("profile.profile"))

    current_user.email = email
    current_user.bio = bio[:500]

    if new_password:
        if not validate_password(new_password):
            flash("New password must be at least 8 characters and include a letter and a number.", "error")
            return redirect(url_for("profile.profile"))
        current_user.set_password(new_password)

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile.profile"))
