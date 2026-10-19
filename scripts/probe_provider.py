"""One development-input integration probe; never counts as a full live run."""
import json
from dotenv import load_dotenv
from kasparro.agent import Agent, Settings, create_provider
from kasparro.data import load_answers
from kasparro.runner import save_json

load_dotenv(override=True)
settings=Settings.from_env()
agent=Agent(create_provider(settings),settings=settings)
answer=load_answers('development')[0]
result=agent.outcome({k:v for k,v in answer.items() if k!='split'},'v1')
save_json('reports/provider-checks/A01-probe.json',result)
print(json.dumps({k:result[k] for k in ['answer_id','status','error','latency_seconds']}))
print('Accepted claims:',len(result['claims']))
