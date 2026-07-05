import json
import subprocess

from config import s20

PROJECT_PATH = config.PROJECT_PATH
MANIFEST_PATH = config.MANIFEST_PATH
REPO_OBJECTS_PATH = config.REPO_OBJECTS_PATH
OLD_BAK_PATH = config.OLD_BAK_PATH
WORK_BAK_PATH = config.WORK_BAK_PATH


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
    # 判断变化类型
    # 类型为修改，复制最早一次的文件到 OLD_BAK_PATH
    result = subprocess.run(
        ["git", "show", hash, "--name-only", f"--format={git_format}"],
        cwd=PROJECT_PATH,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )


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
