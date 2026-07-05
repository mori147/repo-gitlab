import os
import subprocess
import xml.etree.ElementTree as ET

from gitcmd.checkGitEmpty import is_project_empty
from gitcmd.fetch import fetch
from gitcmd.remote import add

import gitlab
from gitlab import GitlabGetError

import config.lineageos20 as configure

revisions = {}
baseurl = {
    "aosp": "https://android.googlesource.com/",
    "github": "https://github.com/",
}
# 初始化 GitLab 实例
gl = gitlab.Gitlab(configure.GITLAB_URL, private_token=configure.PRIVATE_TOKEN)


def parse(xml_path, cb):
    # 解析 XML 清单
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for project in root.findall('remote'):
        name = project.get('name')
        revision = project.get('revision')
        if revision is not None:
            revisions[name] = revision
    for project in root.findall('default'):
        name = project.get('remote')
        revision = project.get('revision')
        if revision is not None:
            revisions[name] = revision

    # 遍历 xml 中的所有 project 标签
    for project in root.findall('project'):
        # 过滤掉 group 中的 notdefault
        groups = project.get('groups', '').split(",")
        # 检查 'notdefault' 是否在 groups 中
        if "notdefault" in groups: continue  # 如果在，则跳过当前项目
        path = project.get('path')
        name = project.get('name')
        remote = project.get('remote', "github")
        groups = project.get('groups')
        revision = project.get('revision', revisions[remote])
        ppp = os.path.join(configure.PROJECT_PATH, path)
        try:
            if 1 and remote == "aosp":
                cb(ppp, revision)
            if 0 and remote == "github":
                if same_last_commit(name, revision, ppp):
                    print(ppp)
        except GitlabGetError as e:
            if e.response_code == 404:
                add(ppp, baseurl[remote] + name, remote)


def same_last_commit(name, branch, path):
    if not branch.startswith("refs/heads/"):
        if branch != "lineage-20.0":
            raise Exception("branch", branch)

    branch = branch.replace("refs/heads/", "")
    project = gl.projects.get(name)
    b1 = project.branches.get(configure.SELF_TAG)
    b2 = project.branches.get(branch)
    return b1.commit['id'] != b2.commit['id']


def aosp(path, revision):
    # 把 tag 转成 commit hash
    tag_commit = subprocess.check_output(
        ["git", "rev-list", "-n", "1", revision],
        cwd=path,
        text=True,
        encoding="utf-8",
    ).strip()

    # 当前 HEAD commit
    head_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        text=True,
        encoding="utf-8",
    ).strip()
    # print(head_commit, tag_commit)
    if 1 and head_commit != tag_commit:
        print(path)
        with open("./log/change.log", "a", encoding="utf-8") as f:
            f.write(path + "\n")


if __name__ == "__main__":
    parse(configure.MANIFEST_PATH, aosp)
