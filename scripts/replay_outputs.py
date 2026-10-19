"""Controlled v2 postprocessing replay of recorded v1 model messages.
NO provider calls. This does not replace any of the four required live runs.
"""
import argparse
import json
import time
from pathlib import Path
from kasparro.data import ROOT, Catalogue, load_answers
from kasparro.models import AnswerInput, locate_quotes
from kasparro.evaluation import load_gold, score
from kasparro.runner import save_json


def replay(source_path, output_dir):
    source=json.loads(Path(source_path).read_text())
    if source['status']!='completed' or source['metadata']['split']!='development':
        raise ValueError('A completed development source run is required')
    answers=load_answers('development')
    inputs={a['answer_id']:a for a in answers}
    outcomes=[]
    recovered=[]
    for original in source['answers']:
        start=time.monotonic()
        outcome=dict(original)
        if original.get('error') and original['error']['type']=='invalid_output':
            try:
                trace_path=Path(original['trace_reference'])
                if not trace_path.is_absolute():trace_path=ROOT/trace_path
                trace=json.loads(trace_path.read_text())
                replies=[t['model'] for t in trace if 'model' in t]
                allowed={f['fact_id'] for t in trace if 'tool' in t for f in json.loads(t['tool']['content'])['facts']}
                draft=json.loads(replies[-1]['content'])
                answer={k:v for k,v in inputs[original['answer_id']].items() if k!='split'}
                prediction=locate_quotes(AnswerInput(**answer),draft,allowed,resolve_unique=True)
                outcome.update(status='success',error=None,claims=prediction['claims'])
                recovered.append(original['answer_id'])
            except (ValueError,KeyError,TypeError,IndexError):
                pass
        outcome['source_latency_seconds']=original['latency_seconds']
        outcome['latency_seconds']=time.monotonic()-start
        outcomes.append(outcome)
    output_dir=Path(output_dir)
    save_json(output_dir/'predictions.json',outcomes)
    # Only now join labels. Scorer and all 376 gold claims are unchanged.
    scores=score(answers,outcomes,Catalogue(),load_gold())
    report={'run_id':'controlled-v2-replay','status':'completed',
        'metadata':{**source['metadata'],'provider':'recorded_output_replay','source_provider':source['metadata']['provider'],
            'agent_version':'v2','run_type':'controlled_postprocessing_replay','live_model_requests':0,'source_run_id':source['run_id']},
        'answers':outcomes,'scores':scores,'recovered_answer_ids':recovered,
        'joint_f1_delta_from_source':scores['joint_f1']-source['scores']['joint_f1'],
        'limitation':'Recorded v1 messages reprocessed under v2; not a live v2 run or independent model-quality measurement.'}
    save_json(output_dir/'report.json',report)
    print(json.dumps({'recovered_answers':recovered,'joint_f1':scores['joint_f1'],'delta':report['joint_f1_delta_from_source']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source_report');parser.add_argument('--output-dir',default=str(ROOT/'reports'/'controlled-replay'))
    args=parser.parse_args();replay(args.source_report,args.output_dir)
