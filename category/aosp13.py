from parse import parse
import subprocess
from gitcmd.remote import add
from gitcmd.push import push
from gitcmd.fetch import fetch
from gitcmd.lfs import change
from gitcmd.status import status
from gitcmd.checkGitEmpty import is_project_empty
import os
import socket

import config.lineageos20 as configure

print(os.getcwd())
print(socket.gethostname())

import multiprocessing


def mult(ppp, name, remote):
    fetch(ppp, name, remote)
    add(ppp, configure.GITLAB_URL + name)
    change(ppp, name)

    p = multiprocessing.Process(target=push, args=(ppp, remote, configure.SELF_TAG))
    p.start()


def action(ppp, name, remote):
    if "cuttlefish_prebuilts" in name:
        mmm = multiprocessing.Process(target=mult, args=(ppp, name, remote))
        mmm.start()
        return

    fetch(ppp, name, remote)
    add(ppp, configure.GITLAB_URL + name)
    change(ppp, name)
    p = multiprocessing.Process(target=push, args=(ppp, remote, configure.SELF_TAG))
    p.start()


def actionByHave(ppp, name, remote):
    fetch(ppp, name, "gitlab")
    add(ppp, configure.GITLAB_URL + name)
    change(ppp, name)
    push(ppp, remote, configure.SELF_TAG)


skip = {
    "c": False
}


def aosp(path, name, remote, groups):
    if remote is None: remote = "github"
    if remote == "aosp": return
    ppp = os.path.join(configure.PROJECT_PATH, path)
    if skip['c']:
        if ppp == "/data/aaa/lineageos20/system/sepolicy":
            skip['c'] = False
        else:
            return
    if not status(ppp):
        raise Exception(remote, ppp)
    if not is_project_empty(name, remote):
        actionByHave(ppp, name, remote)
        return
    action(ppp, name, remote)


if __name__ == "__main__":
    parse(configure.MANIFEST_PATH, aosp)
