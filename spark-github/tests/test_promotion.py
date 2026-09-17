import json
import tempfile
import unittest
from pathlib import Path

from tools.check_evaluation import EvaluationError, load_evaluation
from tools.promote_candidate import PromotionError, promote_candidate


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'harnesses' / 'demo').mkdir(parents=True)
        (self.root / 'candidates' / 'demo' / 'c1').mkdir(parents=True)
        (self.root / 'evaluations' / 'demo' / 'results').mkdir(parents=True)
        self.current = [
            {'id': 'r1', 'name': 'rules', 'config': {'text': 'Old rule.'}},
        ]
        self.candidate = [
            {'id': 'r1', 'name': 'rules', 'config': {'text': 'Improved rule.'}},
        ]
        (self.root / 'harnesses' / 'demo' / 'tree.json').write_text(json.dumps(self.current), encoding='utf-8')
        (self.root / 'candidates' / 'demo' / 'c1' / 'tree.json').write_text(json.dumps(self.candidate), encoding='utf-8')

    def write_eval(self, decision='PROMOTE', **overrides):
        payload = {
            'format': 'reef-spark-evaluation-v1',
            'harness': 'demo',
            'candidate_id': 'c1',
            'decision': decision,
            'evaluated_by': 'gemini-spark',
            'cases_total': 3,
            'current_passed': 1,
            'candidate_passed': 3,
            'notes': 'Candidate improved all cases.',
        }
        payload.update(overrides)
        path = self.root / 'evaluations' / 'demo' / 'results' / 'c1.json'
        path.write_text(json.dumps(payload), encoding='utf-8')
        return path

    def test_load_evaluation_rejects_wrong_format(self):
        path = self.write_eval(format='wrong')
        with self.assertRaisesRegex(EvaluationError, 'format'):
            load_evaluation(path)

    def test_reject_decision_does_not_promote(self):
        eval_path = self.write_eval(decision='REJECT')
        with self.assertRaisesRegex(PromotionError, 'not PROMOTE'):
            promote_candidate(self.root, 'demo', 'c1', eval_path, 'r1')
        self.assertEqual(json.loads((self.root / 'harnesses' / 'demo' / 'tree.json').read_text()), self.current)

    def test_mismatched_candidate_is_rejected(self):
        eval_path = self.write_eval(candidate_id='other')
        with self.assertRaisesRegex(PromotionError, 'candidate_id'):
            promote_candidate(self.root, 'demo', 'c1', eval_path, 'r1')

    def test_successful_promotion_archives_previous_and_evaluation(self):
        eval_path = self.write_eval()
        release_dir = promote_candidate(self.root, 'demo', 'c1', eval_path, 'release-001')
        current = json.loads((self.root / 'harnesses' / 'demo' / 'tree.json').read_text())
        self.assertEqual(current, self.candidate)
        self.assertEqual(json.loads((release_dir / 'previous-tree.json').read_text()), self.current)
        self.assertEqual(json.loads((release_dir / 'tree.json').read_text()), self.candidate)
        self.assertEqual(json.loads((release_dir / 'evaluation.json').read_text())['decision'], 'PROMOTE')
        metadata = json.loads((release_dir / 'release.json').read_text())
        self.assertEqual(metadata['release_id'], 'release-001')
        self.assertEqual(metadata['candidate_id'], 'c1')


if __name__ == '__main__':
    unittest.main()
