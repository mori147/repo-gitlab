import os
import subprocess

def add(path, url, remote="gitlab"):
    # 获取已有的 remote 列表
    print("add ", path)
    result = subprocess.run(
        ["/usr/bin/git", "remote"],
        cwd=path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    if not result.stdout:
        raise result.stderr
    remotes = result.stdout.splitlines()

    if remote in remotes:
        print(f"Remote {remote} 已存在，跳过添加。")
        return

    # 添加 remote
    subprocess.run(
        ["git", "remote", "add", remote, url],
        cwd=path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    print("Remote 'gitlab' 添加成功。")
