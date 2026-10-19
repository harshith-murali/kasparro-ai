import json
import pytest
from kasparro.agent import Agent
from kasparro.runner import run_evaluation
from conftest import FakeProvider


class BrokenStore:
    def __init__(self): self.finished=None
    def create(self,*args): pass
    def save_answer(self,*args): raise RuntimeError('secret database password')
    def finish(self,*args,**kwargs): self.finished=(args,kwargs)


def test_partial_evidence_on_infrastructure_failure(tmp_path):
    store=BrokenStore()
    with pytest.raises(RuntimeError):
        run_evaluation(Agent(FakeProvider([TimeoutError()])),store,'v1','development',tmp_path)
    report=json.loads(next(tmp_path.glob('*/report.json')).read_text())
    assert report['status']=='failed'
    assert len(report['answers'])==1
    assert report['answers'][0]['status']=='error'
    assert report['scores'] is None
    assert 'password' not in json.dumps(report)
    assert next(tmp_path.glob('*/predictions.json')).exists()
    assert store.finished[0][1]=='failed'
