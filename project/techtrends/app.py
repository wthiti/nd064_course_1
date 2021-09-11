import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from logging.config import dictConfig

db_connection = 0


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global db_connection
    db_connection += 1
    return connection


def close_db_connection(connection):
    connection.close()
    global db_connection
    db_connection -= 1


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    close_db_connection(connection)
    return post


# Function to get a number of post
def get_post_count():
    connection = get_db_connection()
    count = connection.execute('SELECT count(1) as posts_count FROM posts').fetchone()
    close_db_connection(connection)
    return count

# https://flask.palletsprojects.com/en/2.0.x/logging/
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    close_db_connection(connection)
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning('GET Article ID %s NOT FOUND', post_id)
        return render_template('404.html'), 404
    else:
        app.logger.info('GET Article %s', post['title'])
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('GET About Us page')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            close_db_connection(connection)

            app.logger.info('CREATE Article %s', title)
            return redirect(url_for('index'))

    return render_template('create.html')


# health check
@app.route('/healthz')
def healthz():
    return jsonify(result='OK - healthy')


# metrics
@app.route('/metrics')
def metrics():
    post_count = get_post_count()
    global db_connection
    return jsonify(db_connection_count=db_connection, post_count=post_count['posts_count'])


# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
