import subprocess


def main():
    print("Creating the db and the PullRequest table")
    subprocess.run(["python3", "create_db.py"], cwd=".")
    subprocess.run(["python3", "create_pr_table.py"], cwd=".")


if __name__ == "__main__":
    main()
