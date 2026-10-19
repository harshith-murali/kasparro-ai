"""Explain rejected model outputs without changing predictions or scoring rules.
This diagnostic never reads gold and never repairs or accepts an invalid output.
"""
import argparse
import json
from pathlib import Path
from kasparro.data import load_answers
from kasparro.models import AnswerInput, locate_quotes


def diagnose(report_path):
    report=json.loads(Path(report_path).read_text())
    answers={a['answer_id']:a for a in load_answers()}
    records=[]
    for outcome in report['answers']:
        if outcome.get('error',{} ) is None or outcome['error']['type']!='invalid_output':
            continue
        trace=json.loads(Path(outcome['trace_reference']).read_text())
        replies=[t['model'] for t in trace if 'model' in t]
        allowed=set()
        for step in trace:
            if 'tool' in step:
                allowed.update(r['fact_id'] for r in json.loads(step['tool']['content'])['facts'])
        answer=answers[outcome['answer_id']]
        record={'answer_id':outcome['answer_id'],'accepted_claims':0}
        try:
            draft=json.loads(replies[-1]['content'])
            source=answer['ai_answer']
            record['non_exact_quotes']=[c['quote'] for c in draft.get('claims',[]) if isinstance(c,dict) and isinstance(c.get('quote'),str) and c['quote'] not in source]
            locate_quotes(AnswerInput(**{k:v for k,v in answer.items() if k!='split'}),draft,allowed)
            record['diagnostic']='Output validates with saved tool facts; investigate original failure'
        except Exception as exc:
            record['diagnostic']=type(exc).__name__+': '+str(exc)[:1500]
        records.append(record)
    return {'run_id':report['run_id'],'diagnostics_only':True,'rejections':records}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('report')
    print(json.dumps(diagnose(parser.parse_args().report),indent=2,ensure_ascii=False))
