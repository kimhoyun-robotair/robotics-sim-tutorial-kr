"""Cobotta URDF에 gripper_center를 추가하고 6축 RMPflow 설정을 만듭니다."""
import argparse
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True, help='원본 template_rmpflow_config.yaml')
    parser.add_argument('--urdf', type=Path, required=True, help='원본 Cobotta Pro 900 URDF')
    parser.add_argument('--descriptor', type=Path, required=True, help='robot_description.yaml')
    parser.add_argument('--output', type=Path, required=True, help='새 출력 디렉터리')
    parser.add_argument('--conservative', action='store_true', help='베이스/두 번째 링크를 넓게 보호')
    args = parser.parse_args()
    import yaml
    with args.template.open() as stream:
        config = yaml.safe_load(stream)
    with args.descriptor.open() as stream:
        descriptor = yaml.safe_load(stream)
    if len(descriptor['cspace']) != 6:
        raise ValueError('Cobotta Pro 900 cspace에는 6개 관절이 있어야 합니다')
    tree = ET.parse(args.urdf)
    robot = tree.getroot()
    if robot.find("link[@name='onrobot_rg6_base_link']") is None:
        raise ValueError('그리퍼 기준 link onrobot_rg6_base_link가 없습니다')
    if robot.find("link[@name='gripper_center']") is not None:
        raise ValueError('원본에 gripper_center가 이미 존재합니다. 원본 URDF를 사용하세요')
    ET.SubElement(robot, 'link', {'name': 'gripper_center'})
    joint = ET.SubElement(robot, 'joint', {'name': 'gripper_center_joint', 'type': 'fixed'})
    ET.SubElement(joint, 'origin', {'rpy': '0 0 0', 'xyz': '0 0 0.24'})
    ET.SubElement(joint, 'parent', {'link': 'onrobot_rg6_base_link'})
    ET.SubElement(joint, 'child', {'link': 'gripper_center'})
    config = deepcopy(config)
    config['joint_limit_buffers'] = [0.01] * 6
    config['rmp_params']['joint_velocity_cap_rmp'].update(max_velocity=1.0, velocity_damping_region=0.3)
    if args.conservative:
        config['body_cylinders'] = [
            {'name': 'base', 'pt1': [0, 0, 0.12], 'pt2': [0, 0, 0], 'radius': 0.08},
            {'name': 'second_link', 'pt1': [0, 0, 0.12], 'pt2': [0, 0, 0.12], 'radius': 0.16}]
        config['body_collision_controllers'] = [{'name': name, 'radius': radius} for name, radius in
            [('J5', 0.05), ('J6', 0.05), ('right_inner_finger', 0.02), ('left_inner_finger', 0.02),
             ('right_inner_knuckle', 0.02), ('left_inner_knuckle', 0.02)]]
    else:
        config['body_cylinders'] = [{'name': 'base', 'pt1': [0, 0, 0.333], 'pt2': [0, 0, 0], 'radius': 0.05}]
        config['body_collision_controllers'] = [{'name': 'right_inner_finger', 'radius': 0.05}]
    frames = {link.attrib['name'] for link in robot.findall('link')}
    for controller in config['body_collision_controllers']:
        if controller['name'] not in frames:
            raise ValueError('URDF에 없는 collision controller frame: ' + controller['name'])
    args.output.mkdir(parents=True, exist_ok=False)
    ET.indent(tree, space='  ')
    tree.write(args.output / 'cobotta_gripper_frame.urdf', encoding='utf-8', xml_declaration=True)
    (args.output / 'robot_description.yaml').write_text(yaml.safe_dump(descriptor, sort_keys=False))
    (args.output / 'rmpflow.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    print('설정 생성:', args.output.resolve())
    print('End Effector Frame: gripper_center; USD 및 URDF mesh 경로는 원본 자산을 유지하세요.')


if __name__ == '__main__':
    main()
