"""Compare frozen development runs and list extraction/label regressions."""
import argparse
import json
from pathlib import Path


def compare(left, right):
    if left['metadata']['split'] != 'development' or right['metadata']['split'] != 'development':
        raise ValueError('Only development reports have public quality scores')
    for key in ['dataset_version','fact_version','evaluator_version','provider','model','settings','file_hashes','scheduled_answers']:
        if left['metadata'][key] != right['metadata'][key]:
            raise ValueError(f'Unfair comparison: {key} differs')
    if left['metadata']['provider'] not in ('openai', 'groq'):
        raise ValueError('Fake-provider runs are controlled tests, not live evaluation evidence')
    for report in [left,right]:
        if report['status'] != 'completed': raise ValueError('Run is incomplete')
    a,b=left['scores'],right['scores']
    correct=lambda s:{m['gold_claim_id'] for m in s['matches'] if m['correct']}
    matched=lambda s:{m['gold_claim_id'] for m in s['matches']}
    return {'v1_run':left['run_id'],'v2_run':right['run_id'],
        'joint_f1_delta':b['joint_f1']-a['joint_f1'],
        'extraction_f1_delta':b['extraction_f1']-a['extraction_f1'],
        'newly_correct_gold_ids':sorted(correct(b)-correct(a)),
        'no_longer_correct_gold_ids':sorted(correct(a)-correct(b)),
        'newly_missed_gold_ids':sorted(matched(a)-matched(b)),
        'newly_extracted_gold_ids':sorted(matched(b)-matched(a)),
        'v1':a,'v2':b}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('v1_report',type=Path);parser.add_argument('v2_report',type=Path)
    args=parser.parse_args()
    print(json.dumps(compare(json.loads(args.v1_report.read_text()),json.loads(args.v2_report.read_text())),indent=2))
