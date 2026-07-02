import os
import subprocess

from gitcmd.branch import switch


def push3(path):
    # 复制当前环境，并强制关闭 Python 的输出缓存
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    aaa = subprocess.Popen(
        '/usr/bin/git push gitlab --mirror -f',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=env,  # 传入新环境变量
    )
    # 实时迭代输出
    if 1 and aaa.stdout:
        for line in aaa.stdout:
            # flush=True 确保这一行立刻被刷新到你的控制台上
            print(line, end="", flush=True)
    aaa.wait()
    # switch(path)
    print("push down")


def push(path, remote):
    print("********** push **************", path, remote)
    # 复制当前环境，并强制关闭 Python 的输出缓存
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    aaa = subprocess.Popen(
        f'/usr/bin/git push gitlab "refs/remotes/{remote}/*:refs/heads/*"',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=env,  # 传入新环境变量
    )
    # 实时迭代输出
    if 1 and aaa.stdout:
        for line in aaa.stdout:
            # flush=True 确保这一行立刻被刷新到你的控制台上
            print(line, end="", flush=True)
    aaa.wait()
    print("********** push **************")
    if remote != "aosp":
        switch(path)
    bbb = subprocess.Popen(
        '/usr/bin/git push gitlab --tags -f',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=env,  # 传入新环境变量
    )
    # 实时迭代输出
    if 1 and bbb.stdout:
        for line in bbb.stdout:
            # flush=True 确保这一行立刻被刷新到你的控制台上
            print(line, end="", flush=True)
    bbb.wait()
    print("【gitlab】 push down")
