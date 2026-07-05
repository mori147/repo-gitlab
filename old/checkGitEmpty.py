import subprocess
import xml.etree.ElementTree as ET
import gitlab
from config import s20
import os

# GitLab 配置
GITLAB_URL = config.GITLAB_URL
PRIVATE_TOKEN = config.PRIVATE_TOKEN
# 模仿 createGitProject.py 的逻辑
if os.path.exists("default.xml"):
    MANIFEST_PATH = "default.xml"
else:
    MANIFEST_PATH = config.MANIFEST_PATH

# 初始化 GitLab 实例
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)


def is_project_empty(gl_project):
    """检查项目是否为空（没有提交记录）"""
    try:
        # 获取最近的一个提交
        commits = gl_project.commits.list(page=1, per_page=1)
        return len(commits) == 0
    except Exception:
        # 如果无法获取提交，通常视为为空
        return True


def parse_and_check():
    """解析 XML 清单并在 GitLab 中检查项目状态"""
    if not os.path.exists(MANIFEST_PATH):
        print(f"错误：在 {MANIFEST_PATH} 未找到清单文件。")
        return

    print(f"正在解析清单文件: {MANIFEST_PATH}")
    tree = ET.parse(MANIFEST_PATH)
    root = tree.getroot()

    # 统计信息
    total = 0
    success = 0
    empty_count = 0
    missing_count = 0

    empty_projects = []
    missing_projects = []

    print("正在启动项目上传状态检查...")

    # 遍历 xml 中的所有 project 标签
    for project in root.findall('project'):
        # 过滤掉 group 中的 notdefault
        groups = project.get('groups', '').split(",")
        if "notdefault" in groups:
            continue

        name = project.get('name')
        if not name:
            continue
        path = project.get('path')

        total += 1

        # 检查项目状态
        try:
            # 尝试获取项目对象
            p_obj = gl.projects.get(name)

            # 检查项目是否为空
            if is_project_empty(p_obj):
                print(f"[EMPTY] 项目已创建但无内容: {name}")
                empty_count += 1
                empty_projects.append(path + "###" + name)
            else:
                # print(f"[OK] 项目上传成功: {name}")
                subprocess.run(
                    ["rm", "-rf", "./*"],
                    cwd=os.path.join(config.PROJECT_PATH, path),
                    capture_output=True,
                    text=True,
                )
                success += 1

        except gitlab.exceptions.GitlabGetError as eee:
            print(eee)
            print(f"[MISSING] 项目尚未在 GitLab 创建: {name}")
            missing_count += 1
            missing_projects.append(path + "###" + name)
        except Exception as e:
            print(f"[ERROR] 检查项目 {name} 时出错: {e}")

            missing_count += 1
            missing_projects.append(f"{name} (错误: {e})")

    # 输出最终报告
    print("\n" + "=" * 40)
    print("上传状态检查汇总报告")
    print("=" * 40)
    print(f"清单有效项目总数: {total}")
    print(f"成功上传 (有提交): {success}")
    print(f"已创建但为空:     {empty_count}")
    print(f"未创建或检查失败: {missing_count}")
    print("-" * 40)

    if success == total:
        print("恭喜！所有项目均已成功上传且包含内容。")
    else:
        print(f"同步完成度: {(success / total * 100):.2f}%")

    if empty_projects:
        print("\n[!] 以下项目已在 GitLab 创建，但尚未成功推送代码 (空仓库):")
        for p in empty_projects:
            print(f"  - {p}")

    with open("./log/empty_projects.txt", 'w') as f:
        f.write('\n'.join(empty_projects))

    with open("./log/missing_projects.txt", 'w') as f:
        f.write('\n'.join(missing_projects))

    if missing_projects:
        print("\n[!] 以下项目在 GitLab 上未找到或访问异常:")
        for p in missing_projects:
            print(f"  - {p}")
    print("=" * 40)


if __name__ == '__main__':
    parse_and_check()
