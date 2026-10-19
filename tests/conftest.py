import json
import pytest
from kasparro.data import Catalogue
from kasparro.models import AnswerInput, locate_quotes


class FakeProvider:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.requests = []

    def complete(self, messages, tools):
        self.requests.append(json.loads(json.dumps({"messages": messages, "tools": tools})))
        result = next(self.replies)
        if isinstance(result, Exception):
            raise result
        return result


def tool(brand="cleartrail", name="get_brand_facts", arguments=None):
    return {"role": "assistant", "tool_calls": [{"id": "call1", "type": "function", "function": {
        "name": name, "arguments": json.dumps({"brand_id": brand}) if arguments is None else arguments}}]}


def response(answer_id="T01", claims=None):
    return {"role": "assistant", "content": json.dumps({"answer_id": answer_id, "claims": claims or []})}


def draft(quote="ClearTrail Mini is blue.", label="unknown", **extra):
    return {"quote": quote, "occurrence": 0, "label": label, "fact_ids": [], "reason": "No relevant catalogue fact.", **extra}


@pytest.fixture
def catalogue():
    return Catalogue()


@pytest.fixture
def answer():
    return {"answer_id": "T01", "brand_id": "cleartrail", "question": "Which?", "ai_answer": "ClearTrail Mini is blue. Choose what you like."}


def outcome(answer, claims=None, error=None):
    return {"answer_id": answer["answer_id"], "status": "error" if error else "success",
            "claims": claims or [], "error": error, "latency_seconds": 0.1}


def prediction(answer, quote="ClearTrail Mini is blue.", label="unknown"):
    return locate_quotes(AnswerInput.model_validate(answer), {"answer_id": answer["answer_id"], "claims": [draft(quote, label)]}, set())["claims"][0]
