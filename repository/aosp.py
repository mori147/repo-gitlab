from parse import parse
import subprocess
from gitcmd.remote import add
from gitcmd.push import push
from gitcmd.fetch import fetch
from gitcmd.lfs import change
import os
import socket

print(os.getcwd())
print(socket.gethostname())

def action(ppp, name, remote):
    fetch(ppp, name, remote)
    add(ppp, config.GITLAB_URL + name)
    change(ppp, name)
    push(ppp, remote)


def aosp(path, name, remote, groups):
    if remote != "aosp": return
    ppp = os.path.join(config.PROJECT_PATH, path)
    result = subprocess.run(
        ["/usr/bin/git", "branch"],
        cwd=ppp,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    # if result.stdout != "* (no branch)": return
    action(ppp, name, remote)

if __name__ == "__main__":
    parse(config.MANIFEST_PATH, aosp)
