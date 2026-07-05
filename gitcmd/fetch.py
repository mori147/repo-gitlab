import os
import subprocess


def __setfetchUrl__(path, name, remote):
    try:
        url = "https://github.com/" + name
        xxx = subprocess.run(
            ["/usr/bin/git", "remote", "set-url", remote, url],
            cwd=path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        print(xxx.stdout)
    except:
        pass



def __unshallow__(path, remote):
    env = os.environ.copy()
    env["HTTPS_PROXY"] = "http://192.168.2.112:7890"
    env["GIT_TERMINAL_PROMPT"] = "0"
    print("remote", remote)
    unshallow = subprocess.Popen(
        ["git", "fetch", remote, "--unshallow"],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 把 stderr 合并到 stdout
        text=True,
        encoding="utf-8",
        env=env
    )

    # 实时迭代输出
    if 1 and unshallow.stdout:
        for line in unshallow.stdout:
            # flush=True 确保这一行立刻被刷新到你的控制台上
            print(line, end="", flush=True)
    unshallow.wait()


def fetch(path, name, remote):
    print("fetch", path)
    __unshallow__(path, remote)
    status = subprocess.Popen(
        ["git", "status"],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 把 stderr 合并到 stdout
        text=True,
        encoding="utf-8",
    )
    # 实时迭代输出
    if 1 and status.stdout:
        for line in status.stdout:
            # flush=True 确保这一行立刻被刷新到你的控制台上
            print(line, end="", flush=True)

    # 等连带进程结束，并获取状态码
    status.wait()
    env = os.environ.copy()
    env["HTTPS_PROXY"] = "http://192.168.2.112:7890"
    env["GIT_TERMINAL_PROMPT"] = "0"

    process = subprocess.Popen(
        ["/usr/bin/git", "fetch", "--all", "--tags"],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=env
    )

    print("[fetch start]", name)
    # 实时迭代输出
    if 1 and process.stdout:
        for line in process.stdout:
            # flush=True 确保这一行立刻被刷新到你的控制台上
            print(line, end="", flush=True)

    # 等连带进程结束，并获取状态码
    returncode = process.wait()

    if returncode != 0:
        print(f"\n[错误] Git Fetch 失败，退出码: {returncode}")
    else:
        print("\n[成功] fetch拉取完成！")
    print("fetch down")
