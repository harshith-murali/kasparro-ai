import json
import os
import time
from dataclasses import dataclass
from openai import OpenAI, APITimeoutError
from .data import ROOT, Catalogue
from .models import AnswerInput, locate_quotes


class AgentError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind, self.message = kind, message


@dataclass(frozen=True)
class Settings:
    model: str = "gpt-4.1-mini-2025-04-14"
    timeout_seconds: float = 60.0
    temperature: float = 0.0
    max_tokens: int = 6000
    max_turns: int = 3

    def __post_init__(self):
        if not 1 <= self.max_turns <= 3 or self.timeout_seconds <= 0:
            raise ValueError("Use one to three turns and a positive provider timeout")

    @classmethod
    def from_env(cls):
        return cls(model=os.getenv("OPENAI_MODEL", cls.model),
                   timeout_seconds=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")))


class OpenAIProvider:
    def __init__(self, settings):
        self.settings = settings
        # Never log credentials, headers, raw exceptions, or environment values.
        self.client = OpenAI(base_url="https://api.openai.com/v1", timeout=settings.timeout_seconds, max_retries=0)

    def complete(self, messages, tools):
        try:
            response = self.client.chat.completions.create(
                model=self.settings.model, messages=messages, tools=tools,
                temperature=self.settings.temperature, max_tokens=self.settings.max_tokens,
                response_format={"type": "json_object"})
            if response.choices[0].finish_reason not in ("stop", "tool_calls"):
                raise AgentError("invalid_output", "Incomplete model response")
            return response.choices[0].message.model_dump(exclude_none=True)
        except APITimeoutError:
            raise AgentError("timeout", "Provider request timed out") from None
        except AgentError:
            raise
        except Exception:
            raise AgentError("provider_error", "Provider request failed") from None


class Agent:
    def __init__(self, provider, catalogue=None, settings=None):
        self.provider = provider
        self.catalogue = catalogue or Catalogue()
        self.settings = settings or Settings.from_env()

    def classify(self, answer, version, trace=None):
        answer = AnswerInput.model_validate(answer)
        if answer.brand_id not in self.catalogue.by_brand:
            raise AgentError("unknown_brand", "Unknown primary brand")
        if version not in ("v1", "v2"):
            raise AgentError("invalid_input", "Unknown agent version")
        path = ROOT / "prompts" / f"{version}.txt"
        if not path.exists():
            raise AgentError("unfrozen_version", "Agent prompt is not available")
        prompt = path.read_text().replace("{brands}", ", ".join(sorted(self.catalogue.by_brand)))
        tools = [{"type": "function", "function": {"name": "get_brand_facts",
            "description": "Read the supplied catalogue facts for a known brand.",
            "strict": True, "parameters": {"type": "object", "properties": {
                "brand_id": {"type": "string", "enum": sorted(self.catalogue.by_brand)}},
                "required": ["brand_id"], "additionalProperties": False}}}]
        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": answer.model_dump_json()}]
        trace = trace if trace is not None else []
        trace.append({"input": messages.copy(), "tools": tools})
        looked_up = set()
        try:
            for _ in range(self.settings.max_turns):
                reply = self.provider.complete(messages, tools)
                trace.append({"model": reply})
                calls = reply.get("tool_calls", [])
                messages.append(reply)
                if calls:
                    for call in calls:
                        fn = call["function"]
                        if call.get("type") != "function" or fn["name"] != "get_brand_facts":
                            raise AgentError("illegal_tool", "Illegal tool request")
                        args = json.loads(fn["arguments"])
                        if not isinstance(args, dict) or set(args) != {"brand_id"} or not isinstance(args["brand_id"], str):
                            raise AgentError("invalid_tool_arguments", "Invalid fact lookup arguments")
                        brand = args["brand_id"]
                        if brand not in self.catalogue.by_brand:
                            raise AgentError("unknown_tool_brand", "Unknown requested brand")
                        facts = self.catalogue.get_brand_facts(brand)
                        looked_up.add(brand)
                        result = {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(facts)}
                        messages.append(result)
                        trace.append({"tool": result})
                    continue
                if answer.brand_id not in looked_up:
                    raise AgentError("missing_tool", "Model did not request primary brand facts")
                allowed_ids = {r["fact_id"] for b in looked_up for r in self.catalogue.by_brand[b]}
                return locate_quotes(answer, json.loads(reply["content"]), allowed_ids)
            raise AgentError("turn_limit", "Model turn limit exhausted")
        except AgentError:
            raise
        except TimeoutError:
            raise AgentError("timeout", "Provider request timed out") from None
        except (ValueError, KeyError, TypeError):
            raise AgentError("invalid_output", "Invalid model output or tool arguments") from None
        except Exception:
            raise AgentError("provider_error", "Provider request failed") from None

    def outcome(self, answer, version):
        trace, start = [], time.monotonic()
        result = {"answer_id": answer["answer_id"], "status": "success", "claims": [], "error": None}
        try:
            result["claims"] = self.classify(answer, version, trace)["claims"]
        except AgentError as exc:
            result.update(status="error", error={"type": exc.kind, "message": exc.message})
        result["latency_seconds"] = time.monotonic() - start
        result["trace"] = trace
        return result
