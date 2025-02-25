from flask import Flask, render_template, jsonify, request, make_response 
from git import Repo 
from pyquery import PyQuery 
from github import Github 
import requests 
import re 
import json 
import os 
from models import * 
from get_repo import get_repo 
from create_creds import read_creds_file 
from requests.auth import HTTPBasicAuth 
 
creds = read_creds_file() 

app = Flask(__name__) 
# postgresql://<nombre_usuario>:<password>@<host>:<puerto>/<nombre_basededatos> 
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{creds['postgres_user']}:{creds['postgres_password']}@localhost:5432/{creds['db_name']}" 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 
db.init_app(app) 

# using username and password to connect with GitHub 
user = creds['github_user'] 
password = creds['github_password']
token = creds['github_token']

#g = Github(user,password) 

g = Github(token)  

repo_name = 'FGArandaRodriguez/99minutos-fullstack-interview-test' 

# Get repo from github 
repo = g.get_repo(repo_name) 
 
@app.route("/")
def index(): 
    return render_template("index.html") 
 
 
@app.route("/pullrequests") 
def pullrequests(): 
    """List all Pull requests.""" 
    url = "http://127.0.0.1:5000/api/pullrequests" 
    r = requests.get(url=url) 
    # extracting data in json format 
    json_response = r.json() 
    pull_requests = json_response['results'] 
    return render_template("pull_requests.html", pull_requests=pull_requests) 
 
 
@app.route("/close_pullrequest", methods=["POST"])
def close_pullrequest():
    """Close a Pull request"""
    # Get form information.
    pr_title = request.form.get("pr_title")
    pr_base = request.form.get("pr_base")
    pr_id = 0
    # Create the PR
    pulls = repo.get_pulls(state='open', sort='created', base=pr_base)
    for pr in pulls:
        if pr.title == pr_title:
            pr_id = pr.id
            pr.edit(state="closed")

    # Updating the state in th db
    pull_request = Pullrequest.query.get(pr_id)
    pull_request.status = "closed"
    db.session.commit()
    return render_template("success.html", pr_title=pr_title, message="Succesfully closed")


@app.route("/pullrequest_form")
def pullrequest_form():
    """Create a Pull request"""
    return render_template("pullrequest_form.html")


@app.route("/create_pullrequest", methods=["POST"])
def create_pullrequest():
    """Create a Pull request"""
    base = request.form.get("base")
    compare = request.form.get("compare")
    pr_title = request.form.get("pr_title")
    pr_body = request.form.get("pr_body")
    status = request.form.get("status")

    # Create the PR
    try:
        pr = repo.create_pull(title=pr_title, body=pr_body,
                              head=compare, base=base)
        if status == "merge":
            try:
                response = pr.merge()
                return render_template("success.html", pr_title=pr_title, message="Pull Request succesfully merged")

            except:
                return render_template("error.html", message="Ocurrio un error")
        pr_ = Pullrequest(id=pr.id, author=pr.user.login, title=pr.title,
                          description=pr.body, status=pr.state, base=pr.base.ref)
        db.session.add(pr_)
        db.session.commit()
        return render_template("success.html", pr_title=pr_title, message="Pull Request created")

    except:
        return render_template("error.html", message="Ocurrio un error")


@app.route("/branches")
def branches():
    """List all branches."""
    url = "http://127.0.0.1:5000/api/branches"
    r = requests.get(url=url)
    # extracting data in json format
    json_response = r.json()
    branches = json_response['results']
    return render_template("branches.html", branches=branches)


@app.route("/branches/<branch_id>")
def branch(branch_id):
    """List details about a single branch."""
    branch_id = branch_id
    url = "http://127.0.0.1:5000/api/branches/{}".format(branch_id)
    r = requests.get(url=url)
    # extracting data in json format
    json_response = r.json()
    commits = json_response['results']
    return render_template("branch.html", commits=commits)


@app.route("/branches/<branch_id>/commits/<commit_id>")
def commit(branch_id, commit_id):
    """List details about a single commit."""
    branch_id = branch_id
    commit_id = commit_id
    url = "http://127.0.0.1:5000/api/branches/{}".format(branch_id)
    r = requests.get(url=url)
    # extracting data in json format
    json_response = r.json()
    commits = json_response['results']
    for commit in commits:
        if commit_id == commit["id"]:
            return render_template("commit.html", commit=commit)


@app.route("/api/pullrequests")
def pullrequests_api():
    """ Return the list of pullrequests """
    # Getting the new PRs
    ids_in_db = {}
    pullrequests = Pullrequest.query.all()
    for pr in pullrequests:
        ids_in_db[pr.id] = pr.status

    for branch in repo.get_branches():
        base = branch.name
        pulls = repo.get_pulls(state='all', sort='created', base=base)
        for pr in pulls:
            if not pr.id in ids_in_db:
                pr_ = Pullrequest(id=pr.id, author=pr.user.login, title=pr.title,
                                  description=pr.body, status=pr.state, base=pr.base.ref)
                db.session.add(pr_)
                db.session.commit()
                print(
                    f"Added PR with id {pr.id} author {pr.user.login} with title {pr.title} and description {pr.body}, state {pr.state}, base {pr.base.ref}")
            else:
                if ids_in_db[pr.id] != pr.state:
                    # Updating the state in th db
                    pull_request = Pullrequest.query.get(pr.id)
                    pull_request.status = pr.state
                    db.session.commit()
                else:
                    pass

    pullrequests = Pullrequest.query.all()
    if pullrequests is None:
        return jsonify({"error": "There is not pull requests"}), 422

    else:
        pullrequests_list = []
        for pr in pullrequests:
            pr_obj = {}
            pr_obj["id"] = pr.id
            pr_obj["author"] = pr.author
            pr_obj["title"] = pr.title
            pr_obj["description"] = pr.description
            pr_obj["status"] = pr.status
            pr_obj["base"] = pr.base
            pullrequests_list.append(pr_obj)

    response = make_response(jsonify(results=pullrequests_list))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response  # jsonify(results=commits_list)


@app.route("/api/branches")
def branches_api():
    """ Return the list of branches """
    branches = repo.get_branches()

    if branches is None:
        return jsonify({"error": "There is not branches"}), 422

    else:
        branches_list = []
        for branch in branches:
            branch_obj = {}
            branch_obj["id"] = branch.name
            branches_list.append(branch_obj)

    response = make_response(jsonify(results=branches_list))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/api/branches/<branch_id>")
def branch_api(branch_id):
    branch_name = branch_id
    commits_list = []
    #base_url = f"https://api.github.com/repos/FGArandaRodriguez/99minutos-fullstack-interview-test/branches/"
    branch = repo.get_branch(branch_name)

    for c in repo.get_commits(sha=branch_name, since=repo.created_at):
        commit = repo.get_commit(sha=c.sha)
        base_url = f"https://api.github.com/repos/FGArandaRodriguez/99minutos-fullstack-interview-test/commits?sha="+ c.sha
        query = requests.get(base_url, auth = HTTPBasicAuth(user, password))
        query = query.json()

        print(query)

        current_branch = branch_name

        #validar que un diccionario traigadatos
        if query:
            pass
        else:
            raise Exception("Sorry, no has commits")
        
        if current_branch == branch_name:
            
            repo_to_get_files = g.get_user().get_repo(name="99minutos-fullstack-interview-test")
            commit_to_get_files = repo_to_get_files.get_commit(sha=c.sha)
            
            commits_list.append({
                "id": c.sha,
                "message": query[0]['commit']['message'],
                "timestamp":query[0]['commit']['committer']['date'],
                "name": query[0]['commit']['author']['name'],
                "email": query[0]['commit']['committer']['email'],
                "branch_id":branch_name,
                "files_changed": len(commit_to_get_files.files)
            })
    response = make_response(jsonify(results=commits_list))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response  # jsonify(results=commits_list)

if __name__ == '__main__':
    app.run()
