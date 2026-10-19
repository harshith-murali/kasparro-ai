from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AnswerInput(StrictModel):
    answer_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    question: str
    ai_answer: str


class ClassifyInput(AnswerInput):
    agent_version: Literal["v1", "v2"]


class RunInput(StrictModel):
    agent_version: Literal["v1", "v2"]
    split: Literal["development", "check"]


class DraftClaim(StrictModel):
    quote: str = Field(min_length=1)
    occurrence: StrictInt = Field(ge=0, description="Zero-based exact occurrence of quote in source")
    label: Literal["supported", "contradicted", "unknown"]
    fact_ids: list[str]
    reason: str = Field(min_length=1, max_length=1500)


class DraftOutput(StrictModel):
    answer_id: str
    claims: list[DraftClaim]


class Claim(StrictModel):
    claim_id: str
    start_char: StrictInt
    end_char: StrictInt
    quote: str = Field(min_length=1)
    label: Literal["supported", "contradicted", "unknown"]
    fact_ids: list[str]
    reason: str = Field(min_length=1, max_length=1500)


class Prediction(StrictModel):
    answer_id: str
    claims: list[Claim]


def validate_prediction(answer, prediction, fact_ids):
    """All-or-nothing validation, including Unicode code-point span semantics."""
    output = Prediction.model_validate(prediction)
    if output.answer_id != answer.answer_id:
        raise ValueError("Wrong answer ID")
    previous_end, seen = 0, set()
    for claim in output.claims:
        s, e = claim.start_char, claim.end_char
        if not 0 <= s < e <= len(answer.ai_answer):
            raise ValueError("Invalid span bounds")
        if claim.quote != answer.ai_answer[s:e] or claim.quote.strip() != claim.quote:
            raise ValueError("Quote mismatch or surrounding whitespace")
        if s < previous_end:
            raise ValueError("Overlapping or unordered spans")
        expected_id = f"{answer.answer_id}:{s}:{e}"
        if claim.claim_id != expected_id or claim.claim_id in seen:
            raise ValueError("Invalid or duplicate claim ID")
        if len(set(claim.fact_ids)) != len(claim.fact_ids) or not set(claim.fact_ids) <= fact_ids:
            raise ValueError("Invalid fact IDs")
        # Reasons use a deliberately conservative punctuation-based sentence bound.
        import re
        if len(re.findall(r"[.!?](?:\s|$)", claim.reason)) > 2:
            raise ValueError("Reason exceeds two sentences")
        seen.add(claim.claim_id)
        previous_end = e
    return output.model_dump()


def locate_quotes(answer, draft, fact_ids, *, resolve_unique=False):
    draft = DraftOutput.model_validate(draft)
    claims = []
    for claim in draft.claims:
        starts, at = [], 0
        while (at := answer.ai_answer.find(claim.quote, at)) >= 0:
            starts.append(at)
            at += 1
        if resolve_unique and len(starts) == 1:
            # v2: an exact quote occurring once has an unambiguous source location.
            start = starts[0]
        else:
            if claim.occurrence >= len(starts):
                raise ValueError("Quote occurrence missing from source")
            start = starts[claim.occurrence]
        end = start + len(claim.quote)
        claims.append({**claim.model_dump(exclude={"occurrence"}), "claim_id": f"{answer.answer_id}:{start}:{end}",
                       "start_char": start, "end_char": end})
    return validate_prediction(answer, {"answer_id": draft.answer_id, "claims": claims}, fact_ids)
