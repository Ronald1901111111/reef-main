import json
import tempfile
import unittest
from pathlib import Path

from tools.reef_tree import SparkUnsupportedNodeError, TreeValidationError, load_tree, validate_spark_exportable


class ReefTreeTests(unittest.TestCase):
    def write_tree(self, data):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / 'tree.json'
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def test_loads_valid_portable_tree(self):
        path = self.write_tree([
            {'id': 'rules-1', 'name': 'rules', 'config': {'text': 'Be concise.'}},
            {'id': 'skill-1', 'name': 'skill', 'config': {'name': 'notes', 'text': '# Notes\nKeep notes.'}},
            {'id': 'cmd-1', 'name': 'agent_command', 'config': {'name': 'review', 'text': 'Review the change.'}},
            {'id': 'config-1', 'name': 'config', 'config': {'target': 'primary', 'data': {'temperature': 0.2}}},
        ])
        entries = load_tree(path)
        self.assertEqual([e.kind for e in entries], ['rules', 'skill', 'agent_command', 'config'])
        validate_spark_exportable(entries)

    def test_rejects_duplicate_ids(self):
        path = self.write_tree([
            {'id': 'same', 'name': 'rules', 'config': {'text': 'One'}},
            {'id': 'same', 'name': 'rules', 'config': {'text': 'Two'}},
        ])
        with self.assertRaisesRegex(TreeValidationError, 'duplicate entry id'):
            load_tree(path)

    def test_rejects_non_object_config(self):
        path = self.write_tree([{'id': 'bad', 'name': 'rules', 'config': 'oops'}])
        with self.assertRaisesRegex(TreeValidationError, 'config must be an object'):
            load_tree(path)

    def test_rejects_missing_named_node_name(self):
        path = self.write_tree([{'id': 'skill-1', 'name': 'skill', 'config': {'text': 'Body'}}])
        with self.assertRaisesRegex(TreeValidationError, "requires config.name"):
            load_tree(path)

    def test_blocks_executable_nodes_for_spark_export(self):
        path = self.write_tree([
            {
                'id': 'tool-1',
                'name': 'native_tool',
                'config': {'name': 'shout', 'description': 'x', 'parameters': {}, 'code': 'def run(a,w): return "x"'},
            }
        ])
        entries = load_tree(path)
        with self.assertRaisesRegex(SparkUnsupportedNodeError, 'native_tool'):
            validate_spark_exportable(entries)


if __name__ == '__main__':
    unittest.main()
