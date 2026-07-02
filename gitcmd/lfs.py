import os
import shutil
import subprocess


def change(path, name, s=None):
    if s:
        url = "http://192.168.2.100:8929"
    else:
        url = "https://review.lineageos.org"
    """修改 .lfsconfig 中的 LFS 地址为当前 GitLab 地址"""
    lfs_file = os.path.join(path, ".lfsconfig")
    if os.path.exists(lfs_file):
        bak_file = lfs_file + "_bak"
        if os.path.exists(bak_file): return
        shutil.copy2(lfs_file, bak_file)
        print(f"已备份并正在同步 {name} 的 .lfsconfig (备份: .lfsconfig_bak)")
        with open(lfs_file, 'w') as f:
            f.write(f"""
[lfs]
	url = {url}/{name}.git/info/lfs
""")

        # 提交更改
        subprocess.run(
            ["git", "add", ".lfsconfig"],
            cwd=path,
            check=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", ".lfsconfig"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        if status.stdout.strip():
            subprocess.run(
                ["git", "commit", "-m", "update .lfsconfig for gitlab"],
                cwd=path,
                check=True,
            )
        subprocess.run(
            ["git", "lfs", "push", "gitlab", "all"],
            cwd=path,
            check=True,
        )

def down(path, name, remote):
    env = os.environ.copy()
    change(path, name, )
    env["HTTPS_PROXY"] = "http://192.168.2.112:7890"
    env["GIT_TERMINAL_PROMPT"] = "0"
    aaa = subprocess.Popen(
        f'/usr/bin/git lfs fetch --all',
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
    print("********** down **************")
    return

def upload(path, name, remote):
    env = os.environ.copy()
    change(path, name, 1)
    aaa = subprocess.Popen(
        f'/usr/bin/git lfs push gitlab',
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
    print("********** down **************")
    return
    return

def lfs(path, name, remote):
    down(path, name, remote)
    upload(path, name, remote)