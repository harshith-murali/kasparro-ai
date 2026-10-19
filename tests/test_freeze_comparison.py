import json
import pytest
from kasparro.agent import Settings
from kasparro.freeze import fingerprint, require_frozen, require_development_reports
from scripts.compare_runs import compare


def test_freeze_required_and_change_detected(tmp_path,monkeypatch):
    import kasparro.freeze as module
    monkeypatch.setattr(module,'ROOT',tmp_path)
    state={'test':'before'}
    monkeypatch.setattr(module,'fingerprint',lambda settings:dict(state))
    (tmp_path/'reports').mkdir()
    with pytest.raises(ValueError):require_frozen(Settings())
    (tmp_path/'reports'/'freeze.json').write_text(json.dumps(state))
    require_frozen(Settings())
    state['test']='changed'
    with pytest.raises(ValueError):require_frozen(Settings())


def test_no_live_development_no_freeze(tmp_path,monkeypatch):
    import kasparro.freeze as module
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'fingerprint',lambda settings:{'settings':{},'datasets':{},'files':{}})
    with pytest.raises(ValueError):require_development_reports(Settings())


def test_settings_limits():
    for kwargs in [{'max_turns':4},{'timeout_seconds':0},{'max_turns':0}]:
        with pytest.raises(ValueError):Settings(**kwargs)


def test_comparison_reports_regression():
    metadata={k:'same' for k in ['dataset_version','fact_version','evaluator_version','model','settings','file_hashes','scheduled_answers']}
    metadata.update(split='development',provider='openai')
    left={'run_id':'one','status':'completed','metadata':metadata,'scores':{'joint_f1':.8,'extraction_f1':.9,'matches':[
        {'gold_claim_id':'claim1','correct':True},{'gold_claim_id':'claim2','correct':False}]}}
    right={'run_id':'two','status':'completed','metadata':dict(metadata),'scores':{'joint_f1':.7,'extraction_f1':.8,'matches':[
        {'gold_claim_id':'claim1','correct':False},{'gold_claim_id':'claim3','correct':True}]}}
    result=compare(left,right)
    assert result['joint_f1_delta']<0
    assert result['no_longer_correct_gold_ids']==['claim1']
    assert result['newly_missed_gold_ids']==['claim2']
    assert result['newly_correct_gold_ids']==['claim3']
    right['metadata']['provider']='fake'
    with pytest.raises(ValueError):compare(left,right)
