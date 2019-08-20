from git import Repo
import os
import subprocess

github_username = "pccproject-bot"
github_password_filename = "/home/pcc/github_password.txt"
github_password = None

def load_github_password():
    global github_password
    github_password = subprocess.check_output(["cat", github_password_filename]).decode("utf-8").replace("\n", "")

class BuildableRepo:

    _repo_name_map = {}

    def __init__(self, short_name, full_name, src_dir="", app_dir=""):
        self.short_name = short_name
        self.full_name = full_name
        self.src_dir = src_dir
        self.app_dir = app_dir

        BuildableRepo._repo_name_map[self.short_name] = self

    def build(self, dir_path):
        build_result = subprocess.check_output(["make"], cwd=os.path.join(dir_path, self.src_dir)).decode("utf-8")

    def get_by_short_name(short_name):
        return BuildableRepo._repo_name_map[short_name]

_tmp_repo = BuildableRepo("PCC_EXPR", "meng-tong/PCC_EXPR")
_tmp_repo = BuildableRepo("PCC", "netarch/PCC", src_dir="src")
_tmp_repo = BuildableRepo("PCC-Uspace", "PCCProject/PCC-Uspace", src_dir="src")
_tmp_repo = BuildableRepo("PCC-Tester", "PCCProject/PCC-Tester")

def github_url(repo):
    if github_password is None:
        load_github_password()
    return "https://%s:%s@github.com/%s.git" % (github_username, github_password,
        BuildableRepo.get_by_short_name(repo).full_name)

def pull_from_repo(repo, dir_path):
    return subprocess.check_output(["git", "pull", github_url(repo)],
        cwd=dir_path).decode("utf-8")

def get_repo_checksum(dir_path):
    return subprocess.check_output(["git", "log", "-1", "--format=\"%H\""],
        cwd=dir_path).decode("utf-8").replace("\"", "").replace("\n", "")

def pull_repo_to_dir(repo, branch, dir_path, checksum=None):
    os.system("rm -rf %s" % dir_path)
    os.system("mkdir -p %s" % dir_path)
    Repo.clone_from(github_url(repo), dir_path)
    checkout_token = branch
    if (checksum is not None):
        checkout_token = checksum
    subprocess.check_output(["git", "checkout", checkout_token], cwd=dir_path)

def build_repo_in_dir(repo_name, branch, dir_path, checksum=None):
    pull_repo_to_dir(repo_name, branch, dir_path, checksum=checksum)
    repo = BuildableRepo.get_by_short_name(repo_name)
    repo.build(dir_path)

def build_as_needed(repo_name, branch, build_dir, checksum=None):
    if (not dir_has_repo(repo_name, branch, build_dir, checksum=checksum)):
    	build_repo_in_dir(repo_name, branch, build_dir, checksum=checksum)
    return get_repo_checksum(build_dir)

def dir_repo_name_matches(dir_path, repo_name):
    expected_name = BuildableRepo.get_by_short_name(repo_name).full_name
    url = subprocess.check_output(
	["git", "config", "--get", "remote.origin.url"],
        cwd=dir_path).decode("utf-8")
    name_start = url.find("github.com/") + len("github.com/")
    name_end = -5
    name = url[name_start:name_end]
    print("Repo name %s (expected %s)" % (name, expected_name))
    print("URL: %s" % url)
    return name == expected_name

def dir_has_repo(repo, branch, dir_path, checksum=None):
    if (not dir_repo_name_matches(dir_path, repo)):
        return False
    
    # If we have no checksum, we will pull the most recent ver of this branch.
    # If there's no change in checksum, then we were already up to date.
    if (checksum is None):
        checksum = get_repo_checksum(dir_path)
        subprocess.check_output(["git", "checkout", branch], cwd=dir_path)
        subprocess.check_output(["git", "pull"], cwd=dir_path)
    return get_repo_checksum(dir_path) == checksum
