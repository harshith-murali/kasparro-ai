import hashlib
import json
from dataclasses import asdict
from .agent import Settings
from .data import ROOT, file_hashes


def fingerprint(settings=None):
    paths = sorted((ROOT/'kasparro').glob('*.py')) + sorted((ROOT/'prompts').glob('*.txt')) + [ROOT/'schema.sql',ROOT/'requirements.lock']
    return {'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'datasets':file_hashes(),'settings':asdict(settings or Settings.from_env())}


def require_frozen(settings):
    path=ROOT/'reports'/'freeze.json'
    if not path.exists() or json.loads(path.read_text()) != fingerprint(settings):
        raise ValueError('Freeze both versions and shared configuration before live check runs')


def require_development_reports(settings):
    found = set()
    current = fingerprint(settings)
    for path in (ROOT/'reports').glob('*/report.json'):
        report = json.loads(path.read_text())
        meta = report.get('metadata', {})
        version = meta.get('agent_version')
        if version not in ('v1','v2'):
            continue
        if (report.get('status') == 'completed' and meta.get('provider') == settings.provider
            and meta.get('split') == 'development' and meta.get('settings') == current['settings']
            and meta.get('file_hashes') == current['datasets']
            and meta.get('prompt_sha256') == current['files'][f'prompts/{version}.txt']
            and meta.get('scheduled_answers') == [f'A{i:02}' for i in range(1,41)]):
            found.add(version)
    if found != {'v1','v2'}:
        raise ValueError('Complete and inspect both live development runs before freezing')
