# BlogPlatform

A full-stack blog platform with comments, built with Flask, SQLAlchemy, and
vanilla JavaScript. Users can register, write posts with optional cover
images, like posts, and comment on them — with full ownership rules so
people can only edit or delete their own content.

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite via SQLAlchemy ORM
- **Auth:** Flask-Login with Werkzeug password hashing, CSRF protection via Flask-WTF
- **Frontend:** HTML5, CSS3 (custom design system, dark/light mode), vanilla JavaScript (fetch API, no frameworks)

## Features

- Registration / login / logout with hashed passwords and session auth
- Create, edit, delete blog posts (title, content, category, optional image)
- Search posts by title/category, filter by category, newest-first sorting, pagination
- Like/unlike posts
- Comment on posts; edit or delete your own comments
- User profile page with bio, email, password update, and your posts
- Dashboard listing all of your own posts with quick edit/delete
- Dark/light mode toggle (persisted via cookie)
- Responsive layout for mobile, tablet, and desktop
- Flash messages + toast notifications for all CRUD actions
- Loading spinner on form submissions
- Custom 404 page
- Client-side and server-side validation (empty fields, email format, password strength)

## Project Structure

```
BlogPlatform/
├── app.py                 # App factory, extension setup, demo data seeding
├── models.py               # SQLAlchemy models: User, BlogPost, Comment
├── routes.py                # All routes: pages, auth, posts API, comments API, profile
├── config.py                 # App configuration
├── requirements.txt
├── templates/                # Jinja2 templates
├── static/
│   ├── css/style.css          # Design system + all page styles
│   ├── js/script.js            # Theme toggle, spinner, toast helpers
│   ├── images/
│   └── uploads/                # User-uploaded post cover images
└── database.db                  # SQLite database (created automatically)
```

## Setup Instructions

1. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```
   The database (`database.db`) is created automatically on first run and
   seeded with 3 demo users and 5 demo posts.

4. **Open your browser** to `http://localhost:5000`

### Demo Login

| Username | Password |
|---|---|
| `admin` | `Password123!` |
| `jane_doe` | `Password123!` |
| `john_smith` | `Password123!` |

## REST API Reference

All endpoints under `/api` return JSON.

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| POST | `/register` | No | Register a new user |
| POST | `/login` | No | Log in |
| POST | `/logout` | Yes | Log out |
| GET | `/api/posts` | No | List posts (supports `?search=`, `?category=`, `?page=`) |
| GET | `/api/posts/<id>` | No | Get a single post |
| POST | `/api/posts` | Yes | Create a post (multipart form: title, content, category, image) |
| PUT | `/api/posts/<id>` | Yes (author only) | Update a post |
| DELETE | `/api/posts/<id>` | Yes (author only) | Delete a post |
| POST | `/api/posts/<id>/like` | Yes | Toggle like on a post |
| GET | `/api/posts/<id>/comments` | No | List comments on a post |
| POST | `/api/posts/<id>/comments` | Yes | Add a comment (JSON: `{"content": "..."}`) |
| PUT | `/api/comments/<id>` | Yes (author only) | Update a comment |
| DELETE | `/api/comments/<id>` | Yes (author only) | Delete a comment |

## Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash`/`check_password_hash` — never stored in plaintext.
- Session-based auth via Flask-Login; protected routes use `@login_required`.
- CSRF protection is enabled globally via Flask-WTF; server-rendered forms include a CSRF token. The JSON/multipart API endpoints under `/api` are same-origin fetch calls guarded by session cookies.
- All database queries go through SQLAlchemy's ORM (parameterized queries), preventing SQL injection.
- Uploaded images are validated by extension and capped at 5MB; filenames are randomized with `uuid` + `secure_filename`.
- Ownership checks ensure users can only edit/delete their own posts and comments.

## Notes

This project uses SQLite for simplicity and portability — no separate database server to install. To move to Postgres/MySQL in production, just change `SQLALCHEMY_DATABASE_URI` in `config.py` (or set the `DATABASE_URL` environment variable) and swap in the appropriate driver.
