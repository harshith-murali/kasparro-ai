import argparse
import json
from dotenv import load_dotenv
from .agent import Agent, OpenAIProvider, Settings
from .store import Store
from .runner import run_evaluation


def main():
    load_dotenv(override=True)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    run = sub.add_parser("run")
    run.add_argument("--version", choices=["v1", "v2"], required=True)
    run.add_argument("--split", choices=["development", "check"], required=True)
    args = parser.parse_args()
    store = Store()
    if args.command == "init-db":
        store.initialize()
        print("Database schema initialized")
    else:
        settings = Settings.from_env()
        result = run_evaluation(Agent(OpenAIProvider(settings), settings=settings), store, args.version, args.split)
        print(json.dumps({"run_id": result["run_id"], "status": result["status"], "scores": result["scores"]}, indent=2))


if __name__ == "__main__":
    main()
