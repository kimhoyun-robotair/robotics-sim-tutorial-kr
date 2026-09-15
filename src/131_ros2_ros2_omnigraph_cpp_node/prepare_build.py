"""Place the local Sphere node into a separately downloaded official C++ extension."""
import argparse
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--template', required=True, type=Path, help='Kit extension template release/107.3.0 checkout')
parser.add_argument('--ros-install', type=Path, default=Path('/opt/ros/humble'))
parser.add_argument('--interface-install', required=True, type=Path, help='ros_ws/install/tutorial_interfaces')
args = parser.parse_args()
template = args.template.resolve()
extension = template/'source/extensions/omni.example.cpp.omnigraph_node_ros'
xml_path = template/'deps/kit-sdk-deps.packman.xml'
for required in [extension/'premake5.lua',xml_path,args.ros_install/'include',args.interface_install/'lib']:
    if not required.exists():
        parser.error(f'Missing prerequisite: {required}')
replacements = [(Path(__file__).parent/'nodes'/name,extension/'plugins/nodes'/name)
                for name in ['ROS2CustomMessageNode.cpp','ROS2CustomMessageNode.ogn']]
for source,target in replacements:
    if not target.exists():
        parser.error(f'Official sample node not found: {target}')
    if target.with_suffix(target.suffix+'.original').exists():
        parser.error(f'Backup exists, refusing repeated replacement: {target}')
tree = ET.parse(xml_path)
root = tree.getroot()
for name in ['system_ros','additional_ros_workspace']:
    if root.find(f"dependency[@name='{name}']") is not None:
        parser.error(f'{name} already exists in packman XML; inspect existing configuration')
backup = xml_path.with_suffix('.xml.original')
if backup.exists():
    parser.error(f'Backup exists: {backup}')
for name,link,path in [('system_ros','system_ros',args.ros_install),
                       ('additional_ros_workspace','additional_ros',args.interface_install)]:
    dependency = ET.SubElement(root,'dependency',name=name,linkPath='../_build/target-deps/'+link,tags='${config}')
    ET.SubElement(dependency,'source',path=str(path.resolve()))
shutil.copy2(xml_path,backup)
for source,target in replacements:
    shutil.copy2(target,target.with_suffix(target.suffix+'.original'))
    shutil.copy2(source,target)
tree.write(xml_path,encoding='utf-8',xml_declaration=True)
print('Prepared local Sphere implementation and absolute ROS dependencies. Run ./build.sh in template checkout.')
