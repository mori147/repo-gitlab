import subprocess
import os
import xml.etree.ElementTree as ET
import config
import shutil
import stat
from concurrent.futures import ThreadPoolExecutor

# 从配置中获取路径
MANIFEST_PATH = config.MANIFEST_PATH
PROJECT_PATH = config.PROJECT_PATH
GITLAB_URL = config.GITLAB_URL

# 统一的 Git 环境变量，禁止交互式弹窗
GIT_ENV = os.environ.copy()
GIT_ENV["GIT_TERMINAL_PROMPT"] = "0"
GIT_ENV["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"


def remove_read_only(func, path, excinfo):
    """处理删除文件时的权限错误 (适用于 Linux 和 Windows)"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def handle_lfs_config(path, name):
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
	url = http://59.51.13.80:8180/{name}.git/info/lfs
""")

        # 提交更改
        subprocess.run(["git", "add", ".lfsconfig"], cwd=path, check=True, env=GIT_ENV)
        status = subprocess.run(["git", "status", "--porcelain", ".lfsconfig"], cwd=path, capture_output=True,
                                text=True, check=True, env=GIT_ENV)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", "update .lfsconfig for gitlab"], cwd=path, check=True, env=GIT_ENV)


def reinit_repo(path, name, url):
    """当遇到无法同步的限制（Shallow 或 Auth）时，直接重建仓库"""
    print(f"正在重建仓库 {name} (路径: {path})...")
    git_dir = os.path.join(path, ".git")
    if os.path.exists(git_dir):
        # Ubuntu 下使用 rm -rf 更直接，或者使用 shutil.rmtree
        if os.path.isdir(git_dir):
            shutil.rmtree(git_dir, onerror=remove_read_only)
        else:
            os.remove(git_dir)

    subprocess.run(["git", "init"], cwd=path, check=True, env=GIT_ENV)
    subprocess.run(["git", "add", "."], cwd=path, check=True, env=GIT_ENV)
    subprocess.run(["git", "commit", "-m", "2026-4-3"], cwd=path, check=True, env=GIT_ENV)
    subprocess.run(["git", "remote", "add", "gitlab", url], cwd=path, check=True, env=GIT_ENV)
    subprocess.run(["git", "checkout", "-b", "lineage-23.2"], cwd=path, check=True, env=GIT_ENV)

    # 重新初始化时也需要检查并更新 LFS 配置
    handle_lfs_config(path, name)

    subprocess.run(["git", "push", "gitlab", "lineage-23.2", "--force"], cwd=path, check=True, env=GIT_ENV)


def unshallow(path):
    """判断是否为 shallow 仓库，如果是则执行 unshallow"""
    result = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=path,
        capture_output=True,
        text=True,
        env=GIT_ENV
    )

    if result.stdout.strip() == "true":
        print(f"检测到 shallow 仓库 {path}，正在查找原始 remote 执行 unshallow...")
        
        # 获取所有 remote
        remotes_res = subprocess.run(["git", "remote"], cwd=path, capture_output=True, text=True, env=GIT_ENV)
        remotes = remotes_res.stdout.splitlines()

        # 优先查找常见的上游 remote 名
        target_remote = None
        for r in ["lineage", "aosp", "github", "origin"]:
            if r in remotes:
                target_remote = r
                break
        
        # 如果没找到，则使用列表里第一个且不为 gitlab 的 remote
        if not target_remote:
            for r in remotes:
                if r != "gitlab":
                    target_remote = r
                    break
        
        if target_remote:
            print(f"正在从 {target_remote} 执行 unshallow...")
            subprocess.run(["git", "fetch", "--unshallow", target_remote], cwd=path, check=True, env=GIT_ENV)
        else:
            # 实在没有别的 remote 就尝试按默认模式执行
            subprocess.run(["git", "fetch", "--unshallow"], cwd=path, check=True, env=GIT_ENV)
            raise Exception("remote")


def checkStatus(path):
    """检查本地仓库状态并提交更改"""
    if not os.path.exists(os.path.join(path, ".git")):
        print(f"警告: {path} 不是一个 Git 仓库。")
        return False

    # 针对 Ubuntu 环境修复 .git 目录、文件或软连接的权限
    git_path = os.path.join(path, ".git")
    if os.path.lexists(git_path):
        targets = [git_path]

        # 1. 处理 OS 层面的软连接 (Symlink)
        if os.path.islink(git_path):
            target = os.readlink(git_path)
            if not os.path.isabs(target):
                target = os.path.abspath(os.path.join(path, target))
            targets.append(target)

        # 2. 处理 Gitfile 模式 (gitdir: ...)
        elif os.path.isfile(git_path):
            try:
                with open(git_path, 'r') as f:
                    content = f.read().strip()
                    if content.startswith("gitdir:"):
                        gitdir = content.split("gitdir:")[1].strip()
                        if not os.path.isabs(gitdir):
                            gitdir = os.path.abspath(os.path.join(path, gitdir))
                        targets.append(gitdir)
            except:
                pass

        # 3. 统一修复所有关联目录的权限
        for t in targets:
            if os.path.exists(t):
                # 递归赋予读写执行权限
                print("修复", t)
                subprocess.run(["chmod", "-R", "755", t], capture_output=True)

    # 检查是否有未提交的更改
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
        env=GIT_ENV
    )

    if not result.stdout: return True
    print(f"正在提交 {path} 的更改...")
    subprocess.run(["git", "add", "."], cwd=path, check=True, env=GIT_ENV)
    subprocess.run(["git", "commit", "-m", "2026-4-3"], cwd=path, check=True, env=GIT_ENV)

    return checkStatus(path)


def gitTag(path, commit_hash):
    """检查并推送标签"""
    # 改用 git rev-parse hexinos16.0.1 验证
    # 获取此标签当前指向的 Commit Hash
    tag_check = subprocess.run(
        ["git", "rev-parse", "--short", "hexinos16.0.1^{commit}"],
        cwd=path,
        capture_output=True,
        text=True,
        env=GIT_ENV
    )
    current_tag_hash = tag_check.stdout.strip() if tag_check.returncode == 0 else None

    # 如果标签不存在，或者指向的哈希与我们要推送的哈希不一致，则重新打标签
    if current_tag_hash != commit_hash:
        print(f"正在为 {path} 强制更新标签 hexinos16.0.1 (当前: {current_tag_hash}, 目标: {commit_hash})")

        # 1. 强制在指定的 commit_hash 上创建带注释的标签
        subprocess.run(["git", "tag", "-a", "hexinos16.0.1", commit_hash, "-m", "hexinos16.0.1", "-f"], cwd=path,
                       check=True, env=GIT_ENV)

        # 2. 推送特定标签
        subprocess.run(["git", "push", "gitlab", "hexinos16.0.1", "--force"], cwd=path, check=True, env=GIT_ENV)

        # 3. 同步所有分支与标签
        print(f"正在同步所有分支与标签至 gitlab...")
        subprocess.run(["git", "push", "gitlab", "--all", "--force"], cwd=path, check=True, env=GIT_ENV)
        subprocess.run(["git", "push", "gitlab", "--tags", "--force"], cwd=path, check=True, env=GIT_ENV)

        # 4. 同步所有 LFS 对象
        if os.path.exists(os.path.join(path, ".lfsconfig")):
            print(f"正在同步 {path} 的 LFS 对象至 gitlab...")
            subprocess.run(["git", "lfs", "push", "gitlab", "--all"], cwd=path, check=True, env=GIT_ENV)

        print(f"标签 hexinos16.0.1 ({commit_hash}) 及全库同步成功。")


def gitPush(path, name):
    """设置远程仓库并推送"""
    url = f"{GITLAB_URL}/{name}.git"
    print(f"正在同步项目: {name} -> {url}")

    # 配置远程仓库
    subprocess.run(["git", "remote", "remove", "gitlab"], cwd=path, stderr=subprocess.DEVNULL, env=GIT_ENV)
    subprocess.run(["git", "remote", "add", "gitlab", url], cwd=path, check=True, env=GIT_ENV)

    # 切换分支
    subprocess.run(["git", "checkout", "-b", "lineage-23.2"], cwd=path, stderr=subprocess.DEVNULL, env=GIT_ENV)
    subprocess.run(["git", "push", "-u", "gitlab", "lineage-23.2"], cwd=path, stderr=subprocess.DEVNULL, env=GIT_ENV)

    # 修改 LFS 配置
    handle_lfs_config(path, name)

    unshallow(path)

    # 尝试推送
    res = subprocess.run(["git", "push", "gitlab", "lineage-23.2", "--force"], cwd=path, capture_output=True, text=True,
                         env=GIT_ENV)

    if res.returncode != 0:
        err_msg = res.stderr.lower()
        if "error: failed to push some refs to" in err_msg:
            # raise Exception(res.stderr)
            pass
        elif "shallow update not allowed" in err_msg or "terminal prompts disabled" in err_msg or "password:" in err_msg:
            # reinit_repo(path, name, url)
            raise Exception(res.stderr)
        else:
            # 其他错误正常抛出供分析
            raise Exception(res.stderr)

    # 获取推送后的 commit hash
    hash_res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=path, capture_output=True, text=True,
                              check=True, env=GIT_ENV)
    pushed_hash = hash_res.stdout.strip()

    print(f"项目 {name} 通过分支 lineage-23.2 推送成功 (Hash: {pushed_hash})")
    gitTag(path, pushed_hash)


def process_project(project_info):
    """处理单个项目的并发任务"""
    abs_path, name, count_str = project_info
    print(f"\n--- 处理任务 {count_str} ---")
    try:
        if checkStatus(abs_path):
            gitPush(abs_path, name)
            print(f"项目 {name} 同步完成。")
    except Exception as e:
        print(f"!!! 任务 {count_str} ({name}) 处理过程中出现致命错误: {e}")
        raise e


def parse_and_process():
    """解析 MANIFEST 并并发处理每个项目"""
    if not os.path.exists(MANIFEST_PATH):
        print(f"错误: 找不到清单文件 {MANIFEST_PATH}")
        return

    print(f"正在解析清单: {MANIFEST_PATH}")
    tree = ET.parse(MANIFEST_PATH)
    root = tree.getroot()

    tasks = []
    count = 0
    for project in root.findall('project'):
        groups = project.get('groups', '').split(",")
        if "notdefault" in groups:
            continue

        name = project.get('name')
        rel_path = project.get('path')

        if not name or not rel_path:
            continue

        abs_path = os.path.join(PROJECT_PATH, rel_path)

        if os.path.exists(abs_path):
            count += 1
            tasks.append((abs_path, name, str(count)))
        else:
            print(f"路过: 本地路径不存在 {abs_path}")

    print(f"开始并发处理，线程数: 4")
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_project, tasks)

    print(f"\n并发处理完成！共提交了 {len(tasks)} 个任务。")


if __name__ == '__main__':
    parse_and_process()
