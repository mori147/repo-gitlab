import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
# import gitlab
import os
from config import s20

MANIFEST_PATH = config.MANIFEST_PATH
PROJECT_PATH = config.PROJECT_PATH
LINEAGE = config.LINEAGE
REPO_OBJECTS_PATH = config.REPO_OBJECTS_PATH


def parse():
    # 解析 XML 清单
    tree = ET.parse(LINEAGE)
    root = tree.getroot()

    # 遍历 xml 中的所有 project 标签
    for project in root.findall('project'):
        # 过滤掉 group 中的 notdefault
        groups = project.get('groups', '').split(",")
        # 检查 'notdefault' 是否在 groups 中
        if "notdefault" in groups: continue  # 如果在，则跳过当前项目
        path = project.get('path')
        name = project.get('name')
        # 在这里检查每个项目路径的 Git 仓库
        if checkGit(os.path.join(PROJECT_PATH, path)):
            # 确定了状态为空
            print(name)
            # 继续检测
        else:
            print("=====>>", path)
            pass


def gitRefLog(path, ):
    """
    在指定路径下执行 Git 命令
    :param path: 子项目根路径（必填）
    :param git_command: 要执行的 Git 命令字符串/列表（必填）
    :return: 命令执行结果（成功返回输出，失败返回错误信息）
    """
    # 1. 定义你想要的结构（使用 Git 占位符）
    # 注意：这里是字典，用冒号
    format_dict = {
        "hash": "%h",
        "author": "%an",  # 作者姓名
        "selector": "%gD",
        "describe": "%D",
        "message": "%gs"
    }

    # 2. 转换为 JSON 字符串
    # Git 的 --format 要求外部有引号。在 list 模式下，subprocess 会处理好基础引用，
    # 但为了防止内部双引号冲突，我们需要确保生成的字符串被 Git 正确识别。
    fff = json.dumps(format_dict)

    result = subprocess.run(
        [
            "git",
            "reflog",
            "-n", "5",
            f"--format={fff}"  # 列表模式下不需要再加额外的转义引号
        ],
        shell=False,
        cwd=path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )

    # 3. 解析结果
    # 因为 git reflog 每一行都是一个 JSON，我们需要逐行解析
    log_data = [json.loads(line) for line in result.stdout.strip().split('\n') if line]

    print(json.dumps(log_data, indent=4, ensure_ascii=False))

    # 3. 返回执行成功的输出信息
    if result.stdout:
        print("------->>", path + '\n', result.stdout)
    return f"执行成功：\n{result.stdout.strip()}"


def gitStatus(path):
    print("==-->>", path)
    result = subprocess.run(
        # "git branch --show-current",
        "git status --porcelain",
        shell=True,
        cwd=path,
        check=True,  # 命令执行失败自动抛出异常
        stdout=subprocess.PIPE,  # 捕获标准输出
        stderr=subprocess.PIPE,  # 捕获标准错误
        encoding="utf-8"  # 中文不乱码
    )
    if 0 and result.stdout:
        lines = result.stdout.strip().split('\n')
        print("--->>", path)
        aaa = False
        for line in lines:
            # 1. 提取状态 (前2位) 和 路径 (3位以后)
            status = line[:2]

            # 2. 仅处理未追踪 (??) 的文件
            # if status != "??":  break
            if status == "??":
                aaa = True
            file_path = line[3:]

            print(line)

            def xxx():
                last = "." + file_path.split("/.")[-1]
                if file_path in [
                    ".project",
                    ".settings/",
                    ".gradle/"
                ]:
                    full_path = os.path.join(path, file_path)
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)  # 如果是目录，递归删除
                    else:
                        os.remove(full_path)

                print(line, '\t', file_path)

            # xxx()
        if aaa and 0:
            subprocess.run(
                # "git branch --show-current",
                "git add -A",
                shell=True,
                cwd=path,
                check=True,  # 命令执行失败自动抛出异常
                stdout=subprocess.PIPE,  # 捕获标准输出
                stderr=subprocess.PIPE,  # 捕获标准错误
                encoding="utf-8"  # 中文不乱码
            )
        return len(lines)
    else:
        gitRefLog(path)


def checkGit(path):
    # 判断路径下是否存在 .git 文件夹
    git_dir = os.path.join(path, ".git")

    if os.path.exists(git_dir):
        if os.path.islink(git_dir):
            # 如果是软连接，获取软连接的目标路径
            link_target = os.readlink(git_dir)
            git_path = os.path.join(path, link_target)
            if link_target[:2] != "..":
                os.remove(git_dir)
            if not os.path.exists(git_path):
                raise Exception(git_path)
            # print(f".git is a symbolic link pointing to: {link_target}")
        else:
            print(f".git directory exists at {git_dir}")
    else:
        # 如果 .git 不存在，创建一个软链接
        print(f"No .git directory found at {path}. Creating symbolic link...")
        link = git_dir.replace(PROJECT_PATH, REPO_OBJECTS_PATH).replace("/.git", ".git")
        if not os.path.exists(link):
            return
            raise Exception(link)
        # 计算相对路径
        relative_path = os.path.relpath(link, path)
        print(relative_path)
        # 通过os 创建软连接
        os.symlink(relative_path, git_dir, )
        pass
        # createGitLink(path)

    # 执行 Git 操作
    # execGit(path)
    return gitStatus(path)


if __name__ == '__main__':
    # 启动解析过程
    parse()
