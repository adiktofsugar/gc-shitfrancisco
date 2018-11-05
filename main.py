"""`main` is the top level module for your Flask application."""
import time
from datetime import datetime
from rfc3339 import rfc3339
import yaml
from flask import Flask, render_template, abort, redirect, url_for, request, json, make_response
from google.appengine.ext import ndb

app = Flask(__name__)

MAX_TITLE_LEN = 15
class Post(ndb.Model):
    message = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.ComputedProperty(lambda self: "%s..." % self.message[0:MAX_TITLE_LEN] if len(self.message) > MAX_TITLE_LEN else self.message)
    rfc_date = ndb.ComputedProperty(lambda self: rfc3339(self.date, utc=True))

@app.route('/')
def index():
    posts = Post.query().order(Post.date).fetch()
    return render_template('index.html', posts=\
        json.JSONEncoder().encode([\
            dict(post.to_dict(), id=post.key.urlsafe()) for post in posts]))

@app.route('/feed')
def feed_index():
    # http://validator.w3.org/feed/
    # https://stackoverflow.com/questions/8507301/generating-rss-feed-under-google-app-engine
    # http://www.atomenabled.org/developers/syndication/
    posts = Post.query().order(Post.date).fetch()
    updated = rfc3339(datetime.now(), utc=True)
    if len(posts) > 0:
        updated = rfc3339(posts[0].date, utc=True)
        print "posts len is > 0, updated is %s" % str(updated)
    response = make_response(render_template('feed/index.xml',
        posts=[dict(post.to_dict(), id=post.key.urlsafe()) for post in posts],
        updated=updated
    ))
    response.headers["content-type"] = "application/atom+xml"
    return response

@app.route('/feed/posts/<post_id>', methods=['GET'])
def feed_post(post_id):
    post_key = ndb.Key(urlsafe=post_id)
    post = post_key.get()
    return render_template("feed/post.html", post=dict(post.to_dict()), id=post.key.urlsafe())

@app.route('/posts', methods=['GET'])
def list_posts():
    posts = Post.query().order(Post.date).fetch()
    return json.jsonify({
        "posts": [p.to_dict() for p in posts]
    });

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
