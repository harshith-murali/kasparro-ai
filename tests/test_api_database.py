import os
import uuid
import pytest
from fastapi.testclient import TestClient
from kasparro.agent import Agent
from kasparro.api import create_app
from kasparro.store import Store
from conftest import FakeProvider, tool, response, draft, prediction, outcome


@pytest.fixture
def store():
    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to run real PostgreSQL integration tests')
    database = Store(url)
    database.initialize()
    return database


def client_for(store,replies):
    return TestClient(create_app(Agent(FakeProvider(replies)),store))


@pytest.mark.parametrize('replies,status', [([tool(),response(claims=[draft()])],200),
    ([tool(),response()],200), ([RuntimeError('secret')],502), ([TimeoutError()],504),
    ([tool(),response(claims=[draft(label='invalid')])],502)])
def test_classify(store,answer,replies,status):
    result = client_for(store,replies).post('/classify',json={**answer,'agent_version':'v1'})
    assert result.status_code == status
    if status == 200: assert result.json()['answer_id'] == answer['answer_id']
    assert 'secret' not in result.text


@pytest.mark.parametrize('extra',[{'claims':[]},{'gold':[]},{'expected_label':'supported'}, {'agent_version':'v3'}, {'answer_id':1}])
def test_api_rejects_inputs(store,answer,extra):
    client=client_for(store,[])
    assert client.post('/classify',json={**answer,'agent_version':'v1',**extra}).status_code==422


def test_unknown_primary(store,answer):
    assert client_for(store,[]).post('/classify',json={**answer,'agent_version':'v1','brand_id':'unknown'}).status_code==404


def test_joined_success_empty_error_and_constraints(store,answer):
    import psycopg
    run_id=str(uuid.uuid4())
    store.create(run_id,{'split':'check'})
    successful=outcome(answer,[prediction(answer)])
    empty=outcome({**answer,'answer_id':'T02'})
    failed=outcome({**answer,'answer_id':'T03'},error={'type':'timeout','message':'Provider request timed out'})
    for o in [failed,successful,empty]: store.save_answer(run_id,o,'fake-trace')
    store.finish(run_id,'completed',{'joint_f1':None})
    result=store.get(run_id)
    assert [a['answer_id'] for a in result['answers']]==['T01','T02','T03']
    assert [len(a['claims']) for a in result['answers']]==[1,0,0]
    assert result['answers'][2]['error']['type']=='timeout'
    with pytest.raises(psycopg.errors.UniqueViolation): store.save_answer(run_id,successful,None)
    with pytest.raises(psycopg.errors.UniqueViolation):
        with store.connect() as conn:
            conn.execute('INSERT INTO claim_results SELECT * FROM claim_results WHERE run_id=%s',(run_id,))
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        store.save_answer(str(uuid.uuid4()),empty,None)
    client=client_for(store,[])
    assert client.get(f'/evaluation-runs/{run_id}').json()['answers']==result['answers']
    assert client.get('/evaluation-runs/not-a-uuid').status_code==422
    assert client.get(f'/evaluation-runs/{uuid.uuid4()}').status_code==404


def test_run_endpoint_check_persists_all_answers(store,tmp_path,monkeypatch):
    import kasparro.api as module
    from kasparro.runner import run_evaluation
    monkeypatch.setattr(module,'run_evaluation',lambda a,s,v,split:run_evaluation(a,s,v,split,tmp_path))
    # Two model turns for each of ten check answers; structurally valid empty outputs.
    replies=[]
    from kasparro.data import load_answers
    for a in load_answers('check'): replies.extend([tool(a['brand_id']),response(a['answer_id'])])
    client=client_for(store,replies)
    result=client.post('/evaluation-runs',json={'agent_version':'v1','split':'check'})
    assert result.status_code==201
    payload=result.json()
    assert payload['scores']['joint_f1'] is None
    assert payload['scores']['G'] is None
    assert payload['scores']['scheduled_answers']==10
    stored=client.get('/evaluation-runs/'+payload['run_id']).json()
    assert len(stored['answers'])==10
    assert all(a['status']=='success' and a['claims']==[] for a in stored['answers'])
    assert list(tmp_path.glob('*/predictions.json'))


def test_bad_run_input(store):
    client=client_for(store,[])
    for value in [{'agent_version':'v1','split':'invalid'},{'agent_version':'v1','split':'check','claims':[]}]:
        assert client.post('/evaluation-runs',json=value).status_code==422


def test_classify_does_not_require_database(answer,monkeypatch):
    monkeypatch.delenv('DATABASE_URL',raising=False)
    client=TestClient(create_app(Agent(FakeProvider([tool(),response()]))))
    assert client.post('/classify',json={**answer,'agent_version':'v1'}).status_code==200


def test_unknown_primary_without_provider_key(answer,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    client=TestClient(create_app())
    assert client.post('/classify',json={**answer,'agent_version':'v1','brand_id':'missing'}).status_code==404


def test_development_errors_retain_all_gold(store,tmp_path,monkeypatch):
    import kasparro.api as module
    from kasparro.runner import run_evaluation
    monkeypatch.setattr(module,'run_evaluation',lambda a,s,v,split:run_evaluation(a,s,v,split,tmp_path))
    client=client_for(store,[TimeoutError() for _ in range(40)])
    result=client.post('/evaluation-runs',json={'agent_version':'v1','split':'development'})
    assert result.status_code==201
    payload=result.json()
    assert payload['status']=='completed'
    assert payload['scores']['G']==376
    assert payload['scores']['P']==0
    assert payload['scores']['joint_f1']==0
    assert payload['scores']['answer_errors']==40
    stored=client.get('/evaluation-runs/'+payload['run_id']).json()
    assert len(stored['answers'])==40
    assert all(a['status']=='error' and not a['claims'] for a in stored['answers'])
