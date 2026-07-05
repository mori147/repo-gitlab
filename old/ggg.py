import json
import os
import subprocess

from config import s20

PROJECT_PATH = config.PROJECT_PATH
MANIFEST_PATH = config.MANIFEST_PATH
REPO_OBJECTS_PATH = config.REPO_OBJECTS_PATH


def git_commit_detail(hash):
    # 1. 定义 Git 输出格式（JSON 结构）
    git_format = json.dumps({
        "commit": "%H",
        "author": "%an",
        "date": "%ad",
        "message": "%s"
    })
    # 2. 执行 git show 获取提交信息和修改的文件列表
    # --name-only 参数用于只输出文件名
    result = subprocess.run(
        ["git", "show", hash, "--name-only", f"--format={git_format}"],
        cwd=PROJECT_PATH,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    lines = result.stdout.strip().split('\n')
    if not lines:
        return None

    # 第一行是提交信息的 JSON 对象
    commit_info = json.loads(lines[0])
    # 后续行是修改的文件列表
    files = lines[1:]
    # 3. 提取修改的文件所属的目录并去重
    folders = set()
    for f in files:
        if f.strip():
            folder = os.path.dirname(f)
            if folder:
                folders.add(folder)
            else:
                folders.add(".")

    # 4. 处理每个修改的文件夹
    for folder in folders:
        if folder == ".":  # 忽略根目录
            continue

        full_path = os.path.join(PROJECT_PATH, folder)
        if not os.path.isdir(full_path):
            continue

        # 进入该路径，先判断 git reflog 是否存在
        # 使用 subprocess.run 执行命令，并通过异常捕获判断是否存在
        try:
            res = subprocess.run(
                ["git", "reflog"],
                cwd=full_path,
                encoding="utf-8",
                capture_output=True,
                check=True
            )
            print(res.stdout)
            # 存在就抛出异常
            raise Exception(f"Git reflog 已存在于 {full_path}，操作终止。")
        except subprocess.CalledProcessError:
            # 不存在就执行 git commit，使用主目录的 message
            print(f"在子目录 {full_path} 中执行提交...")
            # 这里的 git commit 需要该目录已经是 git 仓库，虽然 reflog 不存在可能是因为刚初始化或链接断开
            try:
                return
                subprocess.run(["git", "add", "."], cwd=full_path, check=True)
                subprocess.run(["git", "commit", "-m", commit_info['message']], cwd=full_path, check=True)
            except subprocess.CalledProcessError as e:
                print(f"子目录提交失败（可能不是 Git 仓库 or 无变动）: {e}")

    return commit_info


def get_root_status(project_path=None):
    # 1. 定义 Git 输出格式（类似 JSON 结构）
    # %H: 哈希, %gD: reflog选择器(如 HEAD@{0}), %gs: 动作说明
    git_format = json.dumps({
        "commit": "%H",
        "selector": "%gD",
        "message": "%gs"
    })
    # 2. 使用列表传参，避开 shell=True 的引号嵌套问题
    result = subprocess.run(
        ["git", "reflog", f"--format={git_format}"],
        cwd=PROJECT_PATH,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )

    # 3. 处理输出：从最后一条开始（最旧的开始处理）
    reflog_list = []
    lines = result.stdout.strip().split('\n')
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            res = json.loads(line)
            reflog_list.append(res)
            # 对每个记录执行详细处理
            git_commit_detail(res['commit'])
        except Exception as e:
            print(f"处理 reflog 行失败: {e}")

    return reflog_list


if __name__ == '__main__':
    # 获取最近的 reflog
    status = get_root_status(PROJECT_PATH)
