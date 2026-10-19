import csv
import copy
import pytest
from kasparro.data import read_csv, load_answers
from kasparro.models import AnswerInput, locate_quotes, validate_prediction
from conftest import prediction, draft


def test_csv_embedded_newlines_commas_unicode(tmp_path):
    value = 'é, quoted "value"\nsecond line\r\nnext'
    path = tmp_path / 'input.csv'
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ai_answer'])
        writer.writeheader(); writer.writerow({'ai_answer': value})
    assert read_csv(path)[0]['ai_answer'] == value


def test_catalogue(catalogue):
    assert len(catalogue.rows) == 132
    booleans = [r['value'] for b in catalogue.by_brand.values() for r in b if r['value_type'] == 'boolean']
    assert False in booleans and True in booleans
    assert len(load_answers('development')) == 40
    assert len(load_answers('check')) == 10


def test_unicode_repeated_quote(answer):
    answer['ai_answer'] = '🙂 é. It is blue. It is blue.'
    output = locate_quotes(AnswerInput(**answer), {'answer_id': 'T01', 'claims': [draft('It is blue.', occurrence=1)]}, set())
    assert output['claims'][0]['start_char'] == answer['ai_answer'].rindex('It is blue.')


@pytest.mark.parametrize('mutation', ['negative','out_of_bounds','quote','id','duplicate','overlap','order','label','fact','reason','whitespace'])
def test_invalid_predictions(answer, mutation):
    claim = prediction(answer)
    claims = [claim]
    if mutation == 'negative': claim['start_char'] = -1
    if mutation == 'out_of_bounds': claim['end_char'] = 999
    if mutation == 'quote': claim['quote'] = 'Wrong.'
    if mutation == 'id': claim['claim_id'] = 'fake'
    if mutation == 'duplicate': claims.append(copy.deepcopy(claim))
    if mutation == 'overlap':
        other = copy.deepcopy(claim); other.update(start_char=1, quote=claim['quote'][1:], claim_id=f"T01:1:{claim['end_char']}"); claims.append(other)
    if mutation == 'order':
        claims = [prediction(answer, 'Choose what you like.'), claim]
    if mutation == 'label': claim['label'] = 'maybe'
    if mutation == 'fact': claim['fact_ids'] = ['invented']
    if mutation == 'reason': claim['reason'] = 'One. Two. Three.'
    if mutation == 'whitespace':
        claim.update(end_char=claim['end_char']+1, quote=claim['quote']+' ', claim_id=f"T01:0:{claim['end_char']+1}")
    with pytest.raises(ValueError):
        validate_prediction(AnswerInput(**answer), {'answer_id': 'T01', 'claims': claims}, set())


def test_valid_and_empty(answer):
    for claims in ([prediction(answer)], []):
        assert validate_prediction(AnswerInput(**answer), {'answer_id':'T01','claims':claims}, set())['claims'] == claims


def test_occurrence_absent(answer):
    with pytest.raises(ValueError):
        locate_quotes(AnswerInput(**answer), {'answer_id':'T01','claims':[draft(occurrence=2)]}, set())
