import os
import subprocess
import xml.etree.ElementTree as ET

from gitcmd.branch import switch
from gitcmd.checkGitEmpty import is_project_empty
from gitcmd.fetch import fetch
from gitcmd.push import push
from gitcmd.remote import add

import gitlab
from gitlab import GitlabGetError

import config.s20 as configure

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
print("ROOT", ROOT)
sys.path.insert(0, str(ROOT))

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

    # 遍历 xml 中的所有 project 标签
    for project in root.findall('project'):
        revision = project.get('revision')
        if revision is None: continue
        if revision == "main": continue
        if "lineage-23.2" not in revision: continue
        path = project.get('path')
        name = project.get('name')
        cb(name, revision)
        ppp = os.path.join(configure.PROJECT_PATH, path)
        ttt = revision.replace("lineage-23.2", configure.SELF_TAG)
        push(ppp, "github", ttt)



if __name__ == "__main__":
    parse(configure.LINEAGE, print)
