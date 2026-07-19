import os
import subprocess
import xml.etree.ElementTree as ET

from gitcmd.checkGitEmpty import is_project_empty
from gitcmd.fetch import fetch
from gitcmd.remote import add

import gitlab
from gitlab import GitlabGetError

import config.lineageos20 as configure

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
        # 过滤掉 group 中的 notdefault
        groups = project.get('groups', '').split(",")
        # 检查 'notdefault' 是否在 groups 中
        if "notdefault" in groups: continue  # 如果在，则跳过当前项目
        path = project.get('path')
        name = project.get('name')
        ppp = os.path.join(configure.PROJECT_PATH, path)
        if same_last_commit(name):
            print(ppp)
            with open("/tmp/aosp/log/change.log", "a", encoding="utf-8") as f:
                f.write(ppp + "\n")


def same_last_commit(name):
    try:
        project = gl.projects.get(name)
        b1 = project.branches.get("hxos16.0.1")
        b2 = project.branches.get("hxos16.0.note10")
        return b1.commit['id'] != b2.commit['id']
    except GitlabGetError as e:
        if e.response_code == 404:
            print(404, name)


def re_commit(tag_commit, revision, path):
    # 1. 用 tag_commit 获取文件列表
    ls_tree = subprocess.Popen(
        f'/usr/bin/git ls-tree -r {tag_commit}',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    files = []
    if ls_tree.stdout:
        for line in ls_tree.stdout:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 3)
            if len(parts) >= 4:
                files.append(parts[3])
    ls_tree.wait()

    if not files:
        print(f"{path} (empty tree) 跳过")
        return

    # 2. 使用 ls --full-time 查看每个文件的修改时间，记录最小和最大
    min_time_str = None
    max_time_str = None

    for f in files:
        ls_proc = subprocess.Popen(
            f'/usr/bin/ls --full-time "{f}"',
            shell=True,
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
        ls_output = ""
        if ls_proc.stdout:
            ls_output = ls_proc.stdout.read().strip()
        ls_proc.wait()

        if not ls_output or ls_output.startswith("ls:"):
            print(f"ls 失败: {path}/{f}")
            continue

        parts = ls_output.split()
        # ls --full-time 格式: 权限 链接数 用户 组 大小 日期 时间 [时区] 文件名
        # 日期格式: YYYY-MM-DD
        if len(parts) >= 7:
            date_str = parts[5]
            time_str = parts[6]
            # 验证 date_str 是合法日期格式
            if len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
                continue
            tz_str = parts[7] if len(parts) > 7 and (parts[7].startswith('+') or parts[7].startswith('-')) else "+0000"

            full_ts = f"{date_str} {time_str} {tz_str}"

            if min_time_str is None or full_ts < min_time_str:
                min_time_str = full_ts
            if max_time_str is None or full_ts > max_time_str:
                max_time_str = full_ts

    if min_time_str is None:
        print(f"{path} (无有效时间戳) 跳过")
        return

    # 3. 转换为 ISO 8601 格式，修改 commit 信息
    def to_iso8601(ts_str):
        # ts_str 格式: "2024-01-15 10:30:45.000000000 +0800"
        parts = ts_str.split()
        date_part = parts[0]
        time_part = parts[1].split('.')[0]  # 去掉小数秒部分
        tz_part = parts[2] if len(parts) > 2 else "+0000"
        # 时区转换: +0800 -> +08:00
        tz_iso = f"{tz_part[:3]}:{tz_part[3:]}"
        return f"{date_part}T{time_part}{tz_iso}"

    iso_min = to_iso8601(min_time_str)
    iso_max = to_iso8601(max_time_str)

    print(f"{path} 最早={iso_min} 最晚={iso_max}")

    # 修改 commit 信息: author date = 最早时间, committer date = 最晚时间, msg = AOSP tag
    commit_msg = f"[AOSP sync] {revision}"
    env = os.environ.copy()
    env["GIT_COMMITTER_DATE"] = iso_max
    amend_proc = subprocess.Popen(
        f'/usr/bin/git commit --amend --date="{iso_min}" -m "{commit_msg}"',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if amend_proc.stdout:
        for line in amend_proc.stdout:
            print(line, end="", flush=True)
    amend_proc.wait()

    # 先删除 GitLab 远程的自定义分支，再推送
    branch_ref = f"refs/heads/{configure.SELF_TAG}"
    del_proc = subprocess.Popen(
        f'/usr/bin/git push gitlab :{branch_ref}',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    if del_proc.stdout:
        for line in del_proc.stdout:
            print(line, end="", flush=True)
    del_proc.wait()

    push_proc = subprocess.Popen(
        f'/usr/bin/git push gitlab HEAD:{branch_ref}',
        shell=True,
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    if push_proc.stdout:
        for line in push_proc.stdout:
            print(line, end="", flush=True)
    push_proc.wait()


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
        # re_commit(tag_commit, revision, path)


if __name__ == "__main__":
    parse(ROOT.joinpath("manifests/roomservice.xml"), aosp)
