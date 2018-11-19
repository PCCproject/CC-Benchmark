from git import Repo
import os
import subprocess

github_username = "pccproject-bot"
github_password_filename = "/home/pcc/github_password.txt"
github_password = subprocess.check_output(["cat", github_password_filename]).decode("utf-8").replace("\n", "")

full_repo_name = {
    "PCC":"netarch/PCC",
    "PCC-Uspace":"PCCProject/PCC-Uspace",
    "PCC-Tester":"PCCProject/PCC-Tester"
}

def github_url(repo):
    return "https://%s:%s@github.com/%s.git" % (github_username, github_password,
        full_repo_name[repo])

def pull_from_repo(repo, dir_path):
    return subprocess.check_output(["git", "pull", github_url(repo)],
        cwd=dir_path).decode("utf-8")

def get_repo_checksum(dir_path):
    return subprocess.check_output(["git", "log", "-1", "--format=\"%H\""],
        cwd=dir_path).decode("utf-8").replace("\"", "").replace("\n", "")

def pull_repo_to_dir(repo, branch, dir_path):
    os.system("rm -rf %s" % dir_path)
    os.system("mkdir -p %s" % dir_path)
    Repo.clone_from(github_url(repo), dir_path)
    subprocess.check_output(["git", "checkout", branch], cwd=dir_path)
    return get_repo_checksum(dir_path)

def build_repo_in_dir(repo, branch, dir_path):
    checksum = pull_repo_to_dir(repo, branch, dir_path)
    build_result = subprocess.check_output(["make"], cwd=os.path.join(dir_path, "src")).decode("utf-8")
    print("Build result: %s" % build_result)
    return checksum

def dir_has_repo(repo, branch, dir_path):
    checksum = get_repo_checksum(dir_path)
    subprocess.check_output(["git", "checkout", branch], cwd=dir_path)
    new_checksum = get_repo_checksum(dir_path)
    return new_checksum == checksum
