import os

# --- 配置区 ---
GITLAB_URL = 'http://59.51.13.80:8180'  # 如果是私有部署，请更改 URL
PRIVATE_TOKEN = 'glpat-7lc83uLEy0USxj1t8-_AI286MQp1OjEH.01.0w0po1ts4'
GROUP_ID = 1234567  # 你的 GitLab Group ID (在 Group 首页可以找到)

_disk_big = "/mnt/storage"

PROJECT_PATH = os.path.join(_disk_big, "lineageos")
MANIFEST_PATH = PROJECT_PATH + "/.repo/manifests/default.xml"
REPO_OBJECTS_PATH = os.path.join(PROJECT_PATH, ".repo/projects")
OLD_BAK_PATH = os.path.join(_disk_big, "old")
WORK_BAK_PATH = os.path.join(_disk_big, "work")
