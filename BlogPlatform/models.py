"""
Database models for the Blog Platform.

Relationships:
    - One User  -> Many BlogPosts
    - One User  -> Many Comments
    - One BlogPost -> Many Comments
"""

from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship(
        "BlogPost", backref="author", lazy="dynamic", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", backref="author", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "bio": self.bio,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.username}>"


# Association table for post likes (many-to-many between User and BlogPost)
post_likes = db.Table(
    "post_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("post_id", db.Integer, db.ForeignKey("blog_posts.id"), primary_key=True),
)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General", index=True)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    comments = db.relationship(
        "Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan"
    )
    liked_by = db.relationship(
        "User", secondary=post_likes, backref=db.backref("liked_posts", lazy="dynamic")
    )

    @property
    def like_count(self):
        return len(self.liked_by)

    @property
    def comment_count(self):
        return self.comments.count()

    def to_dict(self, current_user_id=None):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "image_filename": self.image_filename,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author.username,
            "author_id": self.user_id,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "liked_by_current_user": (
                current_user_id in [u.id for u in self.liked_by]
                if current_user_id
                else False
            ),
        }

    def __repr__(self):
        return f"<BlogPost {self.title}>"


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author.username,
            "author_id": self.user_id,
            "post_id": self.post_id,
        }

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"
