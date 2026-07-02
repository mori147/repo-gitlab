from parse import parse
import config
import subprocess, os
from gitcmd.remote import add
from gitcmd.push import push
from gitcmd.fetch import fetch, __setfetchUrl__
from gitcmd.lfs import lfs
import os
import socket

print(os.getcwd())
print(socket.gethostname())


def status(ppp):
    result = subprocess.run(
        ["/usr/bin/git", "status"],
        cwd=ppp,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    if result.stdout.find("no changes added to commit") > -1:
        print("-*-"*50, result.stdout)
        return False
    return True


def action(ppp, name, remote):
    fetch(ppp, name, remote)
    # if not status(ppp): return
    add(ppp, config.GITLAB_URL + name)
    lfs(ppp, name, remote)
    push(ppp, remote)

def github(path, name, remote, groups):
    if remote == "aosp": return
    if remote is None: remote = "github"
    ppp = os.path.join(config.PROJECT_PATH, path)
    __setfetchUrl__(ppp, name, remote)
    result = subprocess.run(
        ["/usr/bin/git", "branch"],
        cwd=ppp,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    print(ppp)

    action(ppp, name, remote)


if __name__ == "__main__":
    parse(config.roomservice, github)
    # parse(config.MANIFEST_PATH, aosp)
