import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.package_spark import export_spark_bundle
from tools.reef_tree import SparkUnsupportedNodeError


class PackageSparkTests(unittest.TestCase):
    def write_tree(self, root: Path, entries):
        path = root / 'tree.json'
        path.write_text(json.dumps(entries), encoding='utf-8')
        return path

    def read_zip(self, path: Path):
        with zipfile.ZipFile(path) as zf:
            return {name: zf.read(name).decode('utf-8') for name in zf.namelist()}

    def test_exports_controller_skills_commands_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree = self.write_tree(root, [
                {'id': 'r1', 'name': 'rules', 'config': {'text': 'Always cite the repository state.'}},
                {'id': 's1', 'name': 'skill', 'config': {'name': 'research', 'text': '# Research\nCheck sources.'}},
                {'id': 'c1', 'name': 'agent_command', 'config': {'name': 'review', 'text': 'Review the candidate.'}},
                {'id': 'cfg', 'name': 'config', 'config': {'target': 'primary', 'data': {'temperature': 0.2}}},
            ])
            out = root / 'bundle'
            export_spark_bundle(tree, 'demo', out)

            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['harness'], 'demo')
            self.assertEqual(manifest['skills'], ['research'])
            self.assertEqual(manifest['commands'], ['review'])
            self.assertEqual(manifest['source_configs'][0]['data'], {'temperature': 0.2})
            self.assertIn('config nodes are preserved as source information', manifest['warnings'][0])

            controller = self.read_zip(out / 'controller' / 'demo-controller.zip')
            self.assertEqual(set(controller), {'SKILL.md'})
            self.assertIn('Always cite the repository state.', controller['SKILL.md'])
            self.assertIn('research', controller['SKILL.md'])
            self.assertIn('review', controller['SKILL.md'])

            skill = self.read_zip(out / 'skills' / 'research.zip')
            self.assertEqual(set(skill), {'SKILL.md'})
            self.assertTrue(skill['SKILL.md'].startswith('---\nname: research\n'))
            self.assertIn('# Research', skill['SKILL.md'])

            command = self.read_zip(out / 'commands' / 'review.zip')
            self.assertIn('HUMAN-INVOCATION POLICY', command['SKILL.md'])
            self.assertIn('Review the candidate.', command['SKILL.md'])

    def test_preserves_existing_skill_frontmatter(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = '---\nname: styled\ndescription: Existing description\n---\nBody.\n'
            tree = self.write_tree(root, [
                {'id': 's1', 'name': 'skill', 'config': {'name': 'styled', 'text': original}},
            ])
            out = root / 'bundle'
            export_spark_bundle(tree, 'demo', out)
            skill = self.read_zip(out / 'skills' / 'styled.zip')
            self.assertEqual(skill['SKILL.md'], original)

    def test_rejects_name_collision_between_skill_and_command(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree = self.write_tree(root, [
                {'id': 's1', 'name': 'skill', 'config': {'name': 'same', 'text': 'Skill'}},
                {'id': 'c1', 'name': 'agent_command', 'config': {'name': 'same', 'text': 'Command'}},
            ])
            with self.assertRaisesRegex(ValueError, 'name collision'):
                export_spark_bundle(tree, 'demo', root / 'bundle')

    def test_refuses_executable_reef_nodes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree = self.write_tree(root, [
                {'id': 'x', 'name': 'code_extension', 'config': {'name': 'x', 'code': 'console.log(1)'}},
            ])
            with self.assertRaises(SparkUnsupportedNodeError):
                export_spark_bundle(tree, 'demo', root / 'bundle')


if __name__ == '__main__':
    unittest.main()
