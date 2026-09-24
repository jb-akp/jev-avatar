"""Brightside Dental routing. Jev answers four one-factor questions; plain code turns the answers into a node."""
from jev import evaluate

QUESTIONS = {
    "intent": {
        "type": "choice",
        "instructions": "What is the caller mainly asking the dental office for?",
        "criteria": {
            "book_appointment": "wants to book a new appointment or check-up",
            "cancel_or_reschedule": "wants to cancel or move an existing appointment",
            "billing": "asks about a bill, insurance, payment or price",
            "hours": "asks about opening hours, location, parking or directions",
            "unclear": "the request is unclear or not about the dental office",
        },
    },
    "emergency": {
        "type": "boolean",
        "instructions": "Is this a dental emergency: severe pain, swelling, bleeding, a knocked-out or broken tooth?",
    },
    "wants_human": {
        "type": "boolean",
        "instructions": "Is the caller explicitly asking to be transferred to a real person or staff member instead of talking to this assistant? Asking to be seen by the dentist does not count.",
    },
    "frustration": {
        "type": "score",
        "instructions": "How frustrated or upset is the caller?",
        "criteria": ["calm", "annoyed", "very frustrated"],
    },
}

INTENT_NODE = {
    "book_appointment": "Book Appointment",
    "cancel_or_reschedule": "Book Appointment",
    "billing": "Billing",
    "hours": "Hours and Location",
    "unclear": "Clarify",
}
EMERGENCY_LINE = 0.5  # a false alarm is cheap, a missed emergency is not
NODES = ["Emergency Triage", "Human Handoff", "Book Appointment", "Billing", "Hours and Location", "Clarify"]


def route(caller_said):
    d = evaluate(caller_said, QUESTIONS)
    a = d["answers"]
    conf = d["providerMetadata"]["typesafe"]["confidence"]
    emergency, human = a["emergency"]["probability"], a["wants_human"]["probability"]
    frustration, intent = a["frustration"]["score"], a["intent"]["choice"]
    if emergency >= EMERGENCY_LINE:
        node, why = "Emergency Triage", f"emergency {emergency:.0%} ≥ {EMERGENCY_LINE:.0%}"
    elif human >= 0.7:
        node, why = "Human Handoff", f"wants a person {human:.0%} ≥ 70%"
    elif frustration >= 1.5:
        node, why = "Human Handoff", f"frustration {frustration:.1f} ≥ 1.5"
    elif conf.get("intent", 1) < 0.6:
        node, why = "Clarify", f"intent confidence {conf['intent']:.0%} < 60%"
    else:
        node, why = INTENT_NODE[intent], f"intent = {intent}"
    raw = {k: {kk: vv for kk, vv in v.items() if kk not in ("probabilities",)} | ({"probabilities": v["probabilities"]} if "probabilities" in v else {}) for k, v in a.items()}
    return {"request": {"model": "typesafe-ai/jev", "state": caller_said,
                        "questions": {k: {"type": q["type"], "instructions": q["instructions"]} for k, q in QUESTIONS.items()}},
            "response": raw,
            "caller_said": caller_said, "next_node": node, "why": why, "answers": a, "confidence": conf,
            "jev_ms": d["jev_ms"], "round_trip_ms": d["round_trip_ms"], "input_tokens": d["usage"]["inputTokens"]}
