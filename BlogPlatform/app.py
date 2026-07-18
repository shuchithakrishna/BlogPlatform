"""
Application entry point.
Creates the Flask app, initializes extensions, registers blueprints,
and (on first run) seeds the database with demo data.
"""

import os
from datetime import datetime, timedelta

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash

from config import Config
from models import db, User, BlogPost, Comment

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes import auth_bp, posts_bp, comments_bp, pages_bp, profile_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(profile_bp)

    # Exempt pure JSON API endpoints from CSRF (they are same-origin fetch
    # calls guarded by session auth; forms still use CSRF tokens).
    csrf.exempt(posts_bp)
    csrf.exempt(comments_bp)

    # Custom error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("404.html", message="File too large (max 5MB)."), 413

    # Template filters
    @app.template_filter("timeago")
    def timeago(dt):
        if dt is None:
            return ""
        now = datetime.utcnow()
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "just now"
        if diff < timedelta(hours=1):
            m = int(diff.total_seconds() // 60)
            return f"{m} minute{'s' if m != 1 else ''} ago"
        if diff < timedelta(days=1):
            h = int(diff.total_seconds() // 3600)
            return f"{h} hour{'s' if h != 1 else ''} ago"
        if diff < timedelta(days=30):
            d = diff.days
            return f"{d} day{'s' if d != 1 else ''} ago"
        return dt.strftime("%b %d, %Y")

    with app.app_context():
        db.create_all()
        seed_demo_data()

    return app


def seed_demo_data():
    """Populate the database with demo users and posts on first run."""
    if User.query.first() is not None:
        return  # already seeded

    demo_users = [
        User(username="admin", email="admin@blogplatform.com", bio="Site administrator and lead writer."),
        User(username="jane_doe", email="jane@example.com", bio="Traveler, photographer, and coffee enthusiast."),
        User(username="john_smith", email="john@example.com", bio="Tech blogger covering web development and AI."),
    ]
    for u in demo_users:
        u.password_hash = generate_password_hash("Password123!")
    db.session.add_all(demo_users)
    db.session.commit()

    demo_posts = [
        BlogPost(
            title="Getting Started with Flask",
            content=(
                "Flask is a lightweight WSGI web application framework in Python. "
                "It is designed to make getting started quick and easy, with the "
                "ability to scale up to complex applications. In this post we walk "
                "through setting up your first Flask project, structuring routes, "
                "and connecting a database with SQLAlchemy."
            ),
            category="Technology",
            user_id=demo_users[2].id,
        ),
        BlogPost(
            title="Ten Tips for Better Travel Photography",
            content=(
                "Traveling opens up a world of photo opportunities. Here are ten "
                "tips I've learned over the years: shoot during golden hour, "
                "scout locations ahead of time, pack light gear, learn the local "
                "customs before pointing your camera at people, and always back "
                "up your photos daily."
            ),
            category="Travel",
            user_id=demo_users[1].id,
        ),
        BlogPost(
            title="Why We Built This Blog Platform",
            content=(
                "Welcome to our new blogging platform! We built this project to "
                "provide a clean, fast, and modern place for writers to share "
                "their ideas. Expect frequent updates, new features like dark "
                "mode, and a growing community of contributors."
            ),
            category="Announcements",
            user_id=demo_users[0].id,
        ),
        BlogPost(
            title="A Beginner's Guide to SQL Databases",
            content=(
                "Relational databases are the backbone of most web applications. "
                "This guide covers the basics of tables, primary keys, foreign "
                "keys, and how ORMs like SQLAlchemy make working with SQL from "
                "Python much more pleasant."
            ),
            category="Technology",
            user_id=demo_users[2].id,
        ),
        BlogPost(
            title="Chasing Sunsets in Santorini",
            content=(
                "There's a reason Santorini is famous for its sunsets. The white "
                "washed buildings against the deep blue Aegean Sea create a "
                "breathtaking backdrop every evening. Here's my full itinerary "
                "for three unforgettable days on the island."
            ),
            category="Travel",
            user_id=demo_users[1].id,
        ),
    ]
    db.session.add_all(demo_posts)
    db.session.commit()

    demo_comments = [
        Comment(content="Great intro post, very helpful for beginners!", user_id=demo_users[1].id, post_id=demo_posts[0].id),
        Comment(content="Looking forward to more Flask content.", user_id=demo_users[0].id, post_id=demo_posts[0].id),
        Comment(content="These tips are gold, thank you for sharing!", user_id=demo_users[2].id, post_id=demo_posts[1].id),
        Comment(content="Excited to be part of this community.", user_id=demo_users[1].id, post_id=demo_posts[2].id),
    ]
    db.session.add_all(demo_comments)
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
