"""Read-only verification of original preservation and the grading/improvement boundary."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((ROOT/'GRADING_FREEZE.json').read_text(encoding='utf-8'))
assert digest(ROOT/'ORIGINAL_COPY.md')==freeze['original_sha256']
for name,expected in freeze['files'].items():
    assert digest(ROOT/name)==expected,(name,'grading file changed after grading freeze')
scores=json.loads((ROOT/'01_SCORES.json').read_text(encoding='utf-8'))
assert scores['status']=='PROVISIONAL_SELF_REVIEW_NOT_INDEPENDENT'
assert len(scores['cases'])==10
assert scores['formal_pass_rate'] is None and scores['correctness_rate'] is None
assert {k:sum(c[k] for c in scores['cases']) for k in ['A','T','R']}==scores['totals']
assert all(0<=c[k]<=2 for c in scores['cases'] for k in ['A','T','R'])
exposure=json.loads((ROOT/'EXPOSURE_REGISTER.json').read_text(encoding='utf-8'))
assert len(exposure['cases'])==10 and not exposure['independent_review_completed']
assert all(not c['unseen_reuse_allowed'] for c in exposure['cases'])
assert '04_METHOD_IMPROVEMENT_CANDIDATE.md' not in freeze['files']
print('PASS: original unchanged; grading frozen separately; ten provisional records; no certification; exposed cases excluded.')
