from github import Github


def get_repo(g):
    for repo in g.get_user().get_repos():

        #print(dir(repo))
        if repo.name == "99minutos-fullstack-interview-test":
            return repo
