import sqlite3

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    schema = '''CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  author_name TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  body TEXT NOT NULL,
  post_id INTEGER NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

INSERT INTO user (username, email, password)
VALUES ('Dev', 'Dev@flaskboard.com', 'scrypt:32768:8:1$QgTQwtm4xufZJPiw$dd5b2ff21ce3dfcd90d3ec13e0361cd0fa3b8c9f9635d2ed2e1c3902415b7e3c821d4a9cec2e6a3738f3a4b5b79c5a52b6373bd0d88b2042eb1b8f4048874fba');

CREATE TABLE IF NOT EXISTS emails (
  email TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS admin (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
  name TEXT NOT NULL
);

INSERT INTO topics (name)
VALUES ('General');

INSERT INTO topics (name)
VALUES ('Testing');

CREATE TABLE IF NOT EXISTS post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  topic TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

INSERT INTO post (author_id, title, body, topic)
VALUES (1,'Test post','This is an auto generated test post','Testing');'''
    f = current_app.open_resource('schema.sql')
    print(f.read(),flush=True)

    db.executescript(f.read().decode('utf8'))
    db.executescript(schema)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')
