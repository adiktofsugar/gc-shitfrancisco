"""`main` is the top level module for your Flask application."""
import time
import yaml
from flask import Flask, render_template, abort, redirect, url_for, request, json
from google.appengine.ext import ndb

app = Flask(__name__)

class Post(ndb.Model):
    message = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

@app.route('/')
def index():
    posts = Post.query().order(Post.date).fetch()
    return render_template('index.html', posts=\
        json.JSONEncoder().encode([\
            dict(post.to_dict(), id=post.key.urlsafe()) for post in posts]))

@app.route('/posts', methods=['POST'])
def create_post():
    message = request.get_json(force=True)["message"]
    post = Post(message=message)
    post.put()
    return json.jsonify(**post.to_dict())

@app.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    post_key = ndb.Key(urlsafe=post_id)
    post_key.delete()
    return ('null', 200, {'Content-type': 'application/json'})

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
