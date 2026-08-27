"""Regression tests for the ROS-independent Humble tutorial validator."""

from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.validate_humble import (
    Validator,
    local_markdown_targets,
    markdown_target_exists,
    remapping_target,
    resolve_markdown_target,
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


class MarkdownTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
