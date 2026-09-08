"""Regression tests for the ROS-independent Humble tutorial validator."""

from pathlib import Path
import ast
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.validate_humble import (
    Validator,
    local_markdown_targets,
    markdown_target_exists,
    polite_tone_violations,
    remapping_target,
    resolve_markdown_target,
    translated_xml_identifiers,
    validate_launch_wrapper,
    validate_rendered_urdf,
)


VALID_URDF = """
<robot name="fixture">
  <link name="base_link"/>
  <link name="sensor_link"/>
  <joint name="sensor_joint" type="fixed">
    <parent link="base_link"/>
    <child link="sensor_link"/>
  </joint>
  <gazebo reference="sensor_link"/>
</robot>
"""


class RenderedUrdfTests(unittest.TestCase):
    def validator(self, root: Path) -> Validator:
        return Validator(root=root)

    def test_valid_tree_has_no_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            validator = self.validator(Path(temporary))
            validate_rendered_urdf(
                validator,
                "valid fixture",
                ET.fromstring(VALID_URDF),
            )
            self.assertEqual([], validator.errors)

    def test_duplicate_link_name_is_rejected(self):
        urdf = VALID_URDF.replace(
            '<link name="sensor_link"/>',
            '<link name="base_link"/>',
        )
        with tempfile.TemporaryDirectory() as temporary:
            validator = self.validator(Path(temporary))
            validate_rendered_urdf(
                validator,
                "duplicate fixture",
                ET.fromstring(urdf),
            )
            self.assertTrue(
                any("중복" in error for error in validator.errors),
                validator.errors,
            )

    def test_transmission_and_control_joint_references_are_not_definitions(self):
        urdf = VALID_URDF.replace('</robot>', '''
          <transmission name="sensor_transmission">
            <joint name="sensor_joint"><hardwareInterface>PositionJointInterface</hardwareInterface></joint>
          </transmission>
          <ros2_control name="control" type="system">
            <joint name="sensor_joint"><state_interface name="position"/></joint>
          </ros2_control>
        </robot>''')
        validator = self.validator(Path("."))
        validate_rendered_urdf(validator, "joint reference fixture", ET.fromstring(urdf))
        self.assertEqual([], validator.errors)

    def test_duplicate_root_joint_definitions_are_still_rejected(self):
        urdf = VALID_URDF.replace('</robot>', '''
          <link name="another_sensor_link"/>
          <joint name="sensor_joint" type="fixed">
            <parent link="base_link"/><child link="another_sensor_link"/>
          </joint>
        </robot>''')
        validator = self.validator(Path("."))
        validate_rendered_urdf(validator, "duplicate joint fixture", ET.fromstring(urdf))
        self.assertTrue(any("중복된 static <joint>" in error for error in validator.errors),
                        validator.errors)

    def test_missing_joint_child_link_is_rejected(self):
        urdf = VALID_URDF.replace('child link="sensor_link"', 'child link="missing_link"')
        with tempfile.TemporaryDirectory() as temporary:
            validator = self.validator(Path(temporary))
            validate_rendered_urdf(
                validator,
                "missing child fixture",
                ET.fromstring(urdf),
            )
            self.assertTrue(
                any("child link가 없습니다" in error for error in validator.errors),
                validator.errors,
            )

    def test_duplicate_sensor_names_across_fixed_links_are_rejected(self):
        urdf = VALID_URDF.replace('<gazebo reference="sensor_link"/>', '''
          <gazebo reference="base_link"><sensor name="camera" type="camera"/></gazebo>
          <gazebo reference="sensor_link"><sensor name="camera" type="camera"/></gazebo>''')
        validator = self.validator(Path("."))
        validate_rendered_urdf(validator, "fixed sensor fixture", ET.fromstring(urdf))
        self.assertTrue(any("센서 이름이 중복" in error for error in validator.errors), validator.errors)

    def test_sensor_frame_must_be_a_real_tf_link(self):
        urdf = VALID_URDF.replace('<gazebo reference="sensor_link"/>', '''
          <gazebo reference="sensor_link"><sensor name="depth" type="depth">
            <plugin name="camera" filename="libgazebo_ros_camera.so">
              <frame_name>missing_optical_link</frame_name>
            </plugin>
          </sensor></gazebo>''')
        validator = self.validator(Path("."))
        validate_rendered_urdf(validator, "missing optical fixture", ET.fromstring(urdf))
        self.assertTrue(any("frame_name에 해당하는 TF 링크가 없습니다" in error
                            for error in validator.errors), validator.errors)


class MarkdownTests(unittest.TestCase):
    def test_translated_xml_attributes_and_tags_are_rejected(self):
        text = '```xml\n<dynamics damping="0.05" 마찰="0.0"/>\n<질량 value="1"/>\n```\n'
        self.assertEqual([(2, '마찰'), (3, '질량')], list(translated_xml_identifiers(text)))

    def test_korean_xml_comments_and_values_remain_valid(self):
        text = ('```xml\n<!-- 마찰="설명" -->\n'
                '<dynamics damping="0.05" friction="0.0"/>\n'
                '<xacro:property name="설명" value="마찰=0.0"/>\n```\n')
        self.assertEqual([], list(translated_xml_identifiers(text)))

    def test_code_fence_links_are_not_audited(self):
        text = """
[real](chapter.md#section)

```markdown
[example only](does-not-exist.md)
```
"""
        self.assertEqual(["chapter.md#section"], list(local_markdown_targets(text)))

    def test_fragment_is_removed_when_resolving_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "guide.md"
            chapter = root / "chapter.md"
            source.write_text("", encoding="utf-8")
            chapter.write_text("# Section\n", encoding="utf-8")
            target = resolve_markdown_target(source, "chapter.md#section")
            self.assertEqual(chapter, target)
            self.assertTrue(markdown_target_exists(target))

    def test_polite_tone_is_rejected_in_prose(self):
        text = (
            "이 설명은 존댓말입니다.\n"
            "명령을 실행하세요.\n"
            "결과를 읽습니다.\n"
            "환경을 확인하십시오.\n"
        )
        self.assertEqual(
            [(1, "입니다"), (2, "세요"), (3, "습니다"), (4, "십시오")],
            list(polite_tone_violations(text)),
        )

    def test_plain_nida_is_not_mistaken_for_polite_bieup_nida(self):
        self.assertEqual([], list(polite_tone_violations("그 값은 정답이 아니다.")))

    def test_polite_tone_ignores_fenced_and_inline_code(self):
        text = """
본문은 ~하다체로 작성한다.
`echo '실행하세요'`

```text
이 출력은 예시입니다.
```
"""
        self.assertEqual([], list(polite_tone_violations(text)))


class PluginContractTests(unittest.TestCase):
    def test_remapping_target_accepts_private_ros_topic(self):
        plugin = ET.fromstring(
            """
            <plugin filename="libfixture.so">
              <ros><remapping>~/odom:=ground_truth/odom</remapping></ros>
            </plugin>
            """
        )
        self.assertEqual("ground_truth/odom", remapping_target(plugin, "odom"))

    def test_sensor_ackermann_launch_requires_encoder_odometry(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "ros2_ws/src/gazebo_tutorial_bringup/launch/sensors.launch.py"
        source = '''generate_robot_launch(
            default_xacro="sensor_bot.urdf.xacro", default_entity="sensor_bot",
            pass_sensor_profile=True, use_ackermann_encoder_odom=False)'''
        validator = Validator(root=root)
        validate_launch_wrapper(validator, path, ast.parse(source))
        self.assertTrue(any("encoder wheel odometry" in error for error in validator.errors),
                        validator.errors)

    def test_f1_spawn_defaults_preserve_building_editor_map_and_original_pose(self):
        root = Path(__file__).resolve().parents[1]
        launch = root / "ros2_ws/src/f1_robot_model/launch/robot_spawn.launch.py"
        tree = ast.parse(launch.read_text(encoding="utf-8"))
        defaults = {}
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
                continue
            if call.func.id != "DeclareLaunchArgument" or not call.args:
                continue
            if not isinstance(call.args[0], ast.Constant):
                continue
            for keyword in call.keywords:
                if keyword.arg == "default_value":
                    defaults[call.args[0].value] = keyword.value
        for coordinate in ("x", "y", "z", "yaw"):
            self.assertEqual(0., float(ast.literal_eval(defaults[coordinate])))
        world = defaults["world"]
        self.assertIsInstance(world, ast.Call)
        self.assertEqual(["world", "demomap_2", "model.sdf"],
                         [ast.literal_eval(part) for part in world.args[1:]])
        sensor_defaults = next(node.value for node in ast.walk(tree)
                               if isinstance(node, ast.Assign)
                               and any(isinstance(target, ast.Name) and target.id == "sensor_defaults"
                                       for target in node.targets))
        self.assertEqual({"depth_camera": "false", "lidar_3d": "false",
                          "stereo_camera": "false", "gps": "false"},
                         ast.literal_eval(sensor_defaults))


class WorkflowRegressionTests(unittest.TestCase):
    def test_ros_setup_is_sourced_before_enabling_nounset(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "humble-ci.yml").read_text(
            encoding="utf-8"
        )
        checked_blocks = 0
        for block in workflow.split("      - name: "):
            lines = [line.strip() for line in block.splitlines()]
            source_indexes = [
                index for index, line in enumerate(lines)
                if line.startswith("source ")
            ]
            if not source_indexes:
                continue
            checked_blocks += 1
            last_source = max(source_indexes)
            nounset_indexes = [
                index for index, line in enumerate(lines)
                if line == "set -u"
                or re.match(r"set -[A-Za-z]*u", line)
            ]
            self.assertTrue(nounset_indexes, block)
            self.assertGreater(min(nounset_indexes), last_source, block)
        self.assertGreater(checked_blocks, 0)


if __name__ == "__main__":
    unittest.main()
