"""Run after inspecting both development reports and before final checks."""
from kasparro.freeze import fingerprint, require_development_reports
from kasparro.agent import Settings
from dotenv import load_dotenv
from kasparro.data import ROOT
from kasparro.runner import save_json

if __name__=='__main__':
    load_dotenv(override=True)
    require_development_reports(Settings.from_env())
    target=ROOT/'reports'/'freeze.json'
    if target.exists(): raise SystemExit('Freeze already exists; do not overwrite after check inference')
    save_json(target,fingerprint())
    print('Frozen both agent versions and shared configuration: reports/freeze.json')
