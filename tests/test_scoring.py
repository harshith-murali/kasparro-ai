import copy
import pytest
from kasparro.evaluation import score, load_gold
from kasparro.data import load_answers
from conftest import prediction, outcome


def gold(answer, claim):
    return {'answer_id':answer['answer_id'], 'claim_id':claim['claim_id'], 'start_char':claim['start_char'],
            'end_char':claim['end_char'], 'quote':claim['quote'], 'expected_label':'unknown'}


@pytest.mark.parametrize('case,expected', [('perfect',(1,1,1,1)), ('missed',(1,0,0,0)), ('extra',(1,2,1,1)),
    ('wrong',(1,1,1,0)), ('provider_error',(1,0,0,0)), ('empty',(1,0,0,0))])
def test_cases(answer,catalogue,case,expected):
    c = prediction(answer)
    refs = [gold(answer,c)]
    claims = [copy.deepcopy(c)]
    error = None
    if case in ('missed','empty'): claims = []
    if case == 'extra': claims.append(prediction(answer,'Choose what you like.'))
    if case == 'wrong': claims[0]['label'] = 'supported'
    if case == 'provider_error': claims=[]; error={'type':'provider_error','message':'Provider request failed'}
    result = score([answer],[outcome(answer,claims,error)],catalogue,refs)
    assert tuple(result[k] for k in ('G','P','M','C')) == expected
    G,P,M,C = expected
    assert result['extraction_f1'] == 2*M/(P+G)
    assert result['joint_f1'] == 2*C/(P+G)
    assert len(result['missed_gold_ids']) == G-M
    assert len(result['unmatched_prediction_ids']) == P-M
    assert len(result['matched_wrong_label_ids']) == M-C


def test_required_arithmetic(answer,catalogue):
    sentences = [f'Claim number {i}.' for i in range(12)]
    answer['ai_answer'] = ' '.join(sentences)
    refs = [gold(answer,prediction(answer,s)) for s in sentences[:10]]
    claims = [prediction(answer,s) for s in sentences[:8]+sentences[10:]]
    claims[0]['label']='contradicted'
    result=score([answer],[outcome(answer,claims)],catalogue,refs)
    assert (result['G'],result['P'],result['M'],result['C']) == (10,10,8,7)
    for key in ['extraction_precision','extraction_recall','extraction_f1']: assert result[key] == .8
    for key in ['joint_precision','joint_recall','joint_f1','gold_claim_coverage']: assert result[key] == .7


@pytest.mark.parametrize('kind',['missing','duplicate','unexpected'])
def test_bad_schedules(answer,catalogue,kind):
    outcomes=[] if kind=='missing' else [outcome(answer),outcome(answer)]
    if kind=='unexpected': outcomes=[outcome({**answer,'answer_id':'other'})]
    with pytest.raises(ValueError): score([answer],outcomes,catalogue,[])


def test_check_nulls(answer,catalogue):
    result=score([answer],[outcome(answer,[prediction(answer)])],catalogue)
    assert result['P']==1
    assert all(value is None for key,value in result.items() if key not in ('P','scheduled_answers','answer_errors'))


def test_empty_schedule(catalogue):
    result=score([],[],catalogue,[])
    assert result['joint_f1'] is None


def test_issued_gold_valid(catalogue):
    answers=load_answers('development')
    result=score(answers,[outcome(a) for a in answers],catalogue,load_gold())
    assert result['G']==376
    assert len(result['missed_gold_ids'])==376


def test_partial_and_merged_are_unmatched(answer,catalogue):
    full=prediction(answer)
    refs=[gold(answer,full)]
    for quote in ['Mini is blue.',answer['ai_answer']]:
        result=score([answer],[outcome(answer,[prediction(answer,quote)])],catalogue,refs)
        assert result['M']==0 and result['joint_f1']==0


@pytest.mark.parametrize('bad', ['error_with_claims','error_without_error','success_with_error','processing'])
def test_outcome_consistency(answer,catalogue,bad):
    o=outcome(answer)
    if bad=='error_with_claims': o.update(status='error',error={'type':'timeout'},claims=[prediction(answer)])
    if bad=='error_without_error': o['status']='error'
    if bad=='success_with_error': o['error']={'type':'timeout'}
    if bad=='processing': o['status']='processing'
    with pytest.raises(ValueError): score([answer],[o],catalogue,[])
