import xml.etree.ElementTree as ET
import gitlab
import config.lineageos20 as configure
import os

# GitLab 配置
GITLAB_URL = configure.GITLAB_URL
PRIVATE_TOKEN = configure.PRIVATE_TOKEN  # + '456'
GROUP_ID = configure.GROUP_ID

# contrib


MANIFEST_PATH = "roomservice.xml"

# 初始化 GitLab 实例
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

print(gl.__dict__)


# exit(0)

def check_subgroup(parent_group, group_name):
    full_path = f"{parent_group.full_path}/{group_name}"
    target_group = None
    try:
        # 直接通过全路径尝试获取
        target_group = gl.groups.get(full_path)
        return
    except Exception:
        # 如果获取失败（通常是 404），则表示组不存在
        pass
    new_subgroup = gl.groups.create({
        'name': group_name,
        'path': group_name,
        'parent_id': parent_group.id, 'visibility': 'internal'
    })
    return new_subgroup


def get_or_create_subgroup(gl, parent_group, group_name):
    """获取或创建一个子组 (使用全路径确保精确嵌套)"""
    full_path = f"{parent_group.full_path}/{group_name}"
    target_group = None
    try:
        # 直接通过全路径尝试获取
        target_group = gl.groups.get(full_path)
    except Exception:
        # 如果获取失败（通常是 404），则表示组不存在
        pass

    if target_group:
        # 检查并修复可见性
        if target_group.visibility != 'internal':
            print(f"Updating subgroup visibility to internal: {target_group.full_path}")
            target_group.visibility = 'internal'
            target_group.save()
        return target_group

    # 如果没找到，创建一个新的子组
    print(f"Creating subgroup: {group_name} under {parent_group.full_path} parent_id", parent_group.id, )
    return check_subgroup(parent_group, group_name)


def create_project(gl, group_id, project_name, full_project_name):
    """创建或修复项目"""
    # 检查项目是否已经存在
    group = gl.groups.get(group_id)
    existing_projects = group.projects.list(search=project_name)
    target_project = None
    for p in existing_projects:
        if p.path == project_name:
            target_project = gl.projects.get(p.id)
            break

    if target_project:
        # 检查并修复可见性
        if target_project.visibility != 'internal':
            print(f"Updating project visibility to internal: {target_project.path_with_namespace}")
            target_project.visibility = 'internal'
            target_project.save()
        return target_project

    # 创建项目：名称与路径同步
    print(f"正在组 {group.full_path} 下创建项目: {project_name}")
    try:
        new_project = gl.projects.create({
            'name': project_name,
            'path': project_name,
            'description': full_project_name,
            'namespace_id': group_id,
            'visibility': 'internal'
        })
        return new_project
    except Exception as e:
        print(f"创建项目 {project_name} 失败: {e}")
        return None


def check_root_group(gl, root_name):
    """检查顶级根组（如 platform, kernel）是否存在，不存在则直接在顶层创建"""
    target_group = None
    try:
        # 直接按全路径在顶层匹配 (top level groups only)
        target_group = gl.groups.get(root_name)
    except Exception:
        pass

    if target_group:
        # 检查并修复可见性
        if target_group.visibility != 'internal' and target_group.visibility != 'public':
            print(f"Updating root group visibility to internal: {target_group.full_path}")
            # print(f"Updating root group current visibility: {target_group.visibility}")
            target_group.visibility = 'internal'
            target_group.save()
        return target_group

    # 如果没找到，在 GitLab 最顶层创建一个新的顶级组
    print(f"正在 GitLab 顶层创建新的根组: {root_name}")
    try:
        return gl.groups.create({'name': root_name, 'path': root_name, 'visibility': 'internal'})
    except Exception as e:
        print(f"创建顶级根组 '{root_name}' 失败: {e}")
        return None


def create_subgroups_by_name(gl, full_project_name):
    """根据带斜杠的项目名称递归创建子组，并实现顶级根目录切换控制"""
    parts = full_project_name.split('/')
    if len(parts) < 2:
        raise Exception(f"项目名称 '{full_project_name}' 格式错误：缺少斜杠 '/'，无法确定根一级子目录。程序已强行停止。")

    # 第一部分直接作为 GitLab 的顶级根组 (不再受制于统一 Root Group)
    root_name = parts[0]
    print(f"执行顶级分流，切换路径根部为: {root_name}")

    current_group = check_root_group(gl, root_name)
    if not current_group:
        raise Exception(f"无法获取或创建顶级目录 '{root_name}'。")

    # 后续部分（除去项目最后一段）作为深层嵌套的子组
    subgroup_names = parts[1:-1]
    for sg_name in subgroup_names:
        current_group = get_or_create_subgroup(gl, current_group, sg_name)

    return current_group


def deal(project):
    groups = project.get('groups', '').split(",")
    # if "notdefault" in groups: return

    name = project.get('name')
    if not name:
        return
    # 1. 快速检查项目是否已存在（全路径匹配，最高效的方式）
    try:
        p_obj = gl.projects.get(name)
        # 如果存在，检查并完善可见性属性
        changed = False
        if p_obj.visibility != 'internal' and p_obj.visibility != 'public':
            print(f"快速修复存量项目可见性: {p_obj.path_with_namespace}")
            p_obj.visibility = 'internal'
            changed = True
        # 性能关键：直接跳过后续昂贵的子组递归寻访

        # 2. 无脑放行：关闭 CI 阻塞
        if p_obj.only_allow_merge_if_pipeline_succeeds:
            p_obj.only_allow_merge_if_pipeline_succeeds = False
            changed = True

        if p_obj.only_allow_merge_if_all_status_checks_passed:
            p_obj.only_allow_merge_if_all_status_checks_passed = False
            changed = True

        if changed:
            p_obj.save()
        print(name, "已经创建成功")
        return
    except Exception:
        # 项目不存在，进入下方的顶级分流递归创建流程
        pass

    # 2. 直接执行顶级分流路径逻辑
    try:
        # 找到目标子组
        target_group = create_subgroups_by_name(gl, name)

        # 2. 获取项目名称（路径的最后一部分）
        project_path = name.split('/')[-1]

        # 3. 对项目及其层级执行幂等处理：若已存在则自动检查并修复可见性 (Visibility)，若不存在则在目标命名空间下执行创建
        res = create_project(gl, target_group.id, project_path, name)

    except Exception as e:
        print(f"处理项目 '{name}' 时出错: {e}")
        # 如果是致命错误（如格式不规范），这里会由 create_subgroups_by_name 抛出并在此导致循环终止（视用户需求而定）
        # 当前逻辑：如果是 raise Exception 抛出的，程序会按原计划停止
        raise e


def parse_and_create():
    """解析 XML 清单并在 GitLab 中创建相应的项目结构"""
    if not os.path.exists(MANIFEST_PATH):
        print(f"错误：在 {MANIFEST_PATH} 未找到清单文件。")
        return

    tree = ET.parse(MANIFEST_PATH)
    root = tree.getroot()

    # 统计信息
    count = 0
    skipped = 0

    print("正在启动自动化同步处理流程...")

    # 顶级分流模式下，已移除统一的 root_group 获取逻辑
    # 程序直接依据项目名在 GitLab 顶层进行动态切换

    # 遍历 xml 中的所有 project 标签
    for project in root.findall('project'):
        deal(project)
    # 过滤掉 group 中的 notdefault

    print(f"自动化处理完成。成功同步/验证了 {count} 个项目，失败 {skipped} 个。")


def debug():
    # path="tools/tradefederation/contrib" name="platform/tools/tradefederation/contrib"
    deal({
        "path": "vendor/samsung/universal9830-common",
        "name": "hxy/vendor/samsung/universal9830-common"
    })


if __name__ == '__main__':
    parse_and_create()
    # debug()
