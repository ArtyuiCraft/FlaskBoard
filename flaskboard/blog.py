from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("blog", __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, p.title, p.body, p.created, p.topic, u.username, p.author_id'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY p.created DESC'
    ).fetchall()
    topics = db.execute(
        'SELECT name FROM topics'
    ).fetchall()
    return render_template('blog/index.html', posts=posts, topics=topics)

@bp.route('/topic/<topic_name>')
def posts_by_topic(topic_name):
    db = get_db()
    posts = db.execute(
        'SELECT p.id, p.title, p.body, p.created, p.topic, u.username, p.author_id'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.topic = ?'
        ' ORDER BY p.created DESC',
        (topic_name,)
    ).fetchall()
    return render_template('blog/posts_by_topic.html', posts=posts, topic_name=topic_name)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if g.user["username"] != "Dev":
        admin = (
            get_db()
            .execute("SELECT 1 FROM admin WHERE username = ?", (g.user["username"],)).fetchone()
        )
    else:
        admin = True

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if not admin:
        if check_author and post["author_id"] != g.user["id"]:
            abort(403)

    return post

def get_comments(post_id):
    db = get_db()
    return db.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,))

@bp.route("/post/<int:post_id>", methods=('GET', 'POST'))
def post(post_id):
    db = get_db()
    post = get_post(post_id,False)
    comments = get_comments(post_id)
    if request.method == "POST":
        body = request.form["body"]
        error = None

        if body.strip(" ") == "":
            error = "empty comment"

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO comments (author_name,author_id, body, post_id) VALUES (?, ?, ?, ?)",
                (g.user['username'], g.user["id"], body ,post_id),
            )
            db.commit()
    return render_template("blog/post.html", user = g.user, post = post, comments = comments)

@bp.route("/user/<int:user_id>/delete", methods=("POST",))
@login_required
def deleteuser(user_id):
    db = get_db()
    db.execute("DELETE FROM user WHERE id = ?", (user_id,))
    db.commit()
    return redirect(url_for("blog.index"))

@bp.route('/user/<int:user_id>')
def user_profile(user_id):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch user information
    cursor.execute('SELECT * FROM user WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    # Fetch user's posts
    cursor.execute('SELECT * FROM post WHERE author_id = ?', (user_id,))
    posts = cursor.fetchall()

    conn.close()

    return render_template('blog/user_profile.html', user=user, posts=posts)

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    db = get_db()
    topics = db.execute(
        'SELECT name FROM topics'
    ).fetchall()

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        topic = request.form["topic"]
        error = None

        if topic == "changelog" and g.user["username"] != "Dev":
            error = "Access denied to: changelog"

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id, topic) VALUES (?, ?, ?, ?)",
                (title, body, g.user["id"], topic),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html", topics=[topic[0] for topic in topics])


@bp.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    if request.method == 'POST':
        name = request.form['name']
        error = None

        if not name:
            error = "Topic name is required"

        if error != None:
            flash(error)
        else:
            conn = get_db()
            conn.execute('INSERT INTO topics (name) VALUES (?)', (name,))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('blog/newtopic.html')

@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/post/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.execute("DELETE FROM comments WHERE post_id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))
