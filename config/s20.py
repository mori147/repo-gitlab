import os

# --- 配置区 ---
GITLAB_URL = 'http://192.168.2.100:8929/'  # 如果是私有部署，请更改 URL
PRIVATE_TOKEN = 'glpat-tFrmqXCgBzHxX6nvX_S8-286MQp1OjEH.01.0w0n6o6er'
GROUP_ID = 1234567  # 你的 GitLab Group ID (在 Group 首页可以找到)

_disk_big = "/data"

PROJECT_PATH = os.path.join(_disk_big, "s20")
LINEAGE = PROJECT_PATH + "/.repo/manifests/snippets/lineage.xml"
MANIFEST_PATH = PROJECT_PATH + "/.repo/manifests/default.xml"
# local_manifests/roomservice.xml
roomservice = PROJECT_PATH + "/.repo/local_manifests/roomservice.xml"
REPO_OBJECTS_PATH = os.path.join(PROJECT_PATH, ".repo/projects")
OLD_BAK_PATH = os.path.join(_disk_big, "../old")
WORK_BAK_PATH = os.path.join(_disk_big, "work")

SELF_TAG = "hxos16.0.1"
