import sys

from gitinterface import app
from gitinterface.models import User, db_session
from flask_github import GitHub
from flask import request, url_for, redirect, g, session, render_template_string, jsonify, render_template, Response
from time import sleep
import subprocess

github = GitHub(app)

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@app.route('/')
def index():
    if g.user:
        t = 'Hello! <a href="{{ url_for("user") }}">Get user</a> ' \
            '<a href="{{ url_for("logout") }}">Logout</a>'
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template_string(t)


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize(scope="repo")
    else:
        return 'Already logged in'


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)
    user.github_access_token = access_token
    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/user')
def user():
    return jsonify(github.get('user'))


#full name vakue is the name of the repo
@app.route('/repo')
def repo():
    repo_dict = github.get('/orgs/JohnPaulConcierge/repos?type=private')
    return render_template('show_repos.html', entities=repo_dict)


@app.route('/repo/<name>/<repo>')
def get_branches(name, repo):
    branches_dict = github.get('/repos/' + name + '/' + repo + '/branches')
    return render_template('show_branches.html', entities=branches_dict, repo=repo)

@app.route('/repo/<repo>/branch/<branch>')
def deploy_branch(repo, branch):
    def inner():
        process = subprocess.call(['bash', 'run.sh', repo, branch], stdout=subprocess.PIPE, shell=True)
        for line in iter(process.stdout.readline,''):
            yield line.rstrip()
        #return proc.communicate()[0].decode('utf-8')
    return Response(inner(), mimetype='text/html')  # text/html is required for most browsers to show the partial page immediately