import subprocess


def main():
    print("Filling the PullRequest table")
    subprocess.run(["python3", "fill_pr_table.py"], cwd=".")
    subprocess.run(["python3", "application.py"], cwd=".")


if __name__ == "__main__":
    main()
