
import xml.etree.ElementTree as ET
import config

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
        remote = project.get('remote')
        groups = project.get('groups')
        cb(path, name, remote, groups)
        # if remote is None:
            # print(groups)

if __name__ == "__main__":
    parse(config.MANIFEST_PATH, print)