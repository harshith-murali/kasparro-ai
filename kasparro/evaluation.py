"""Labels are opened only here, after the runner saves predictions."""
from .data import ROOT, read_csv
from .models import AnswerInput, validate_prediction


def load_gold():
    return [{**r, "start_char": int(r["start_char"]), "end_char": int(r["end_char"])}
            for r in read_csv(ROOT / "development_gold.csv")]


def score(answers, outcomes, catalogue, gold=None):
    scheduled = {a["answer_id"]: a for a in answers}
    ids = [o["answer_id"] for o in outcomes]
    if len(ids) != len(set(ids)) or set(ids) != set(scheduled):
        raise ValueError("Missing, duplicate or unexpected answer outcomes")
    predictions = []
    for outcome in outcomes:
        if outcome["status"] == "error":
            if outcome["claims"] or not outcome.get("error"):
                raise ValueError("Error outcomes must have no predictions and preserve an error")
        elif outcome["status"] == "success":
            if outcome.get("error") is not None:
                raise ValueError("Successful outcome cannot have an error")
            answer = {k: v for k, v in scheduled[outcome["answer_id"]].items() if k != "split"}
            validate_prediction(AnswerInput.model_validate(answer),
                                {"answer_id": outcome["answer_id"], "claims": outcome["claims"]}, catalogue.ids)
            predictions.extend((outcome["answer_id"], c) for c in outcome["claims"])
        else:
            raise ValueError("Nonterminal answer outcome")
    result = {"scheduled_answers": len(answers), "answer_errors": sum(o["status"] == "error" for o in outcomes),
              "P": len(predictions), "G": None, "M": None, "C": None,
              "extraction_precision": None, "extraction_recall": None, "extraction_f1": None,
              "joint_precision": None, "joint_recall": None, "joint_f1": None,
              "gold_claim_coverage": None, "missed_gold_ids": None,
              "unmatched_prediction_ids": None, "matched_wrong_label_ids": None, "matches": None}
    if gold is None:
        return result
    refs = [g for g in gold if g["answer_id"] in scheduled]
    index = {(g["answer_id"], g["start_char"], g["end_char"]): g for g in refs}
    if len(index) != len(refs) or len({g["claim_id"] for g in refs}) != len(refs):
        raise ValueError("Duplicate gold claims")
    for g in refs:
        if scheduled[g["answer_id"]]["ai_answer"][g["start_char"]:g["end_char"]] != g["quote"]:
            raise ValueError("Gold quote mismatch")
    matched, wrong, extras, correct = {}, [], [], 0
    for aid, claim in predictions:
        key = (aid, claim["start_char"], claim["end_char"])
        ref = index.get(key)
        if ref is None:
            extras.append(claim["claim_id"])
        else:
            is_correct = claim["label"] == ref["expected_label"]
            correct += is_correct
            matched[ref["claim_id"]] = {"prediction_id": claim["claim_id"],
                "gold_claim_id": ref["claim_id"], "expected_label": ref["expected_label"],
                "predicted_label": claim["label"], "correct": is_correct}
            if not is_correct:
                wrong.append(claim["claim_id"])
    G, P, M, C = len(refs), len(predictions), len(matched), correct
    result.update(G=G, M=M, C=C, missed_gold_ids=sorted(g["claim_id"] for g in refs if g["claim_id"] not in matched),
                  unmatched_prediction_ids=sorted(extras), matched_wrong_label_ids=sorted(wrong),
                  matches=[matched[k] for k in sorted(matched)])
    if not answers:
        return result
    div = lambda numerator, denominator: numerator / denominator if denominator else 0.0
    result.update(extraction_precision=div(M, P), extraction_recall=div(M, G), extraction_f1=div(2*M, P+G),
                  joint_precision=div(C, P), joint_recall=div(C, G), joint_f1=div(2*C, P+G), gold_claim_coverage=div(C, G))
    return result
