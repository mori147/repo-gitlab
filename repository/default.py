from parse import parse
import config
import subprocess, os
from gitcmd.remote import add
from gitcmd.push import push
from gitcmd.fetch import fetch, __setfetchUrl__
from gitcmd.lfs import change
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
        print(result.stdout)
        return False
    return True


def action(ppp, name, remote):
    # if not status(ppp): return
    if remote is None: remote = "github"
    fetch(ppp, name, remote)
    add(ppp, config.GITLAB_URL + name)
    change(ppp, name)
    push(ppp, remote)


def ddd(path, name, remote, groups):
    ppp = os.path.join(config.PROJECT_PATH, path)
    action(ppp, name, remote)


def test():
    # ddd("external/armnn", "platform/external/armnn/", "aosp", None)
    ddd("build/soong", "LineageOS/android_build_soong", None, None)


if __name__ == "__main__":
    parse(config.MANIFEST_PATH, ddd)
    # test()
