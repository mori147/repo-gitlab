from config import s20
import subprocess
from gitcmd.remote import add
from gitcmd.push import push
from gitcmd.fetch import fetch
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
    if not status(ppp): return
    fetch(ppp, name, remote)
    add(ppp, config.GITLAB_URL + name)
    lfs(ppp, name, remote)
    push(ppp, remote)


def github(path, name, remote, groups):
    ppp = os.path.join(config.PROJECT_PATH, path)
    action(ppp, name, remote)

def test():
    # github(
    #     "device/qcom/sepolicy-legacy-um",
    #     "LineageOS/android_device_qcom_sepolicy_vndr",
    #     None,
    #     None
    # )

    # github(
    #     "packages/apps/Updater",
    #     "LineageOS/android_packages_apps_Updater",
    #     None,
    #     None
    # )

    github(
        "prebuilts/kernel-build-tools",
        "kernel/prebuilts/build-tools",
        "aosp",
        None
    )


if __name__ == "__main__":
    test()
    # parse(config.LINEAGE, github)
    # parse(config.MANIFEST_PATH, aosp)
