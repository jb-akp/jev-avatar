"""The same four routing questions, asked of a normal chat LLM, so we can race it against Jev."""
import json, sys, time, urllib.request
sys.path.insert(0, "proxy")
from pathlib import Path


def openai_key():
    for line in (Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()

from router import QUESTIONS, INTENT_NODE

PRICE = {"gpt-6-luna": (0.10, 0.50), "gpt-6-sol": (2.00, 10.00)}  # $ per 1M in/out, list price
PROMPT = ("You route calls for a dental office. Answer as JSON only: "
          '{"intent": one of ' + json.dumps(list(QUESTIONS["intent"]["criteria"])) +
          ', "emergency": probability 0-1 that this is a dental emergency (severe pain, swelling, bleeding, broken tooth), '
          '"wants_human": probability 0-1 the caller explicitly asks to be transferred to a real person, '
          '"frustration": 0 calm, 1 annoyed, 2 very frustrated}')


def ask(model, caller_said):
    body = {"model": model, "messages": [{"role": "system", "content": PROMPT}, {"role": "user", "content": caller_said}],
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {openai_key()}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    d = json.load(urllib.request.urlopen(req, timeout=120))
    ms = round((time.perf_counter() - t0) * 1000)
    a = json.loads(d["choices"][0]["message"]["content"])
    u = d.get("usage", {})
    pin, pout = PRICE[model]
    cost = (u.get("prompt_tokens", 0) * pin + u.get("completion_tokens", 0) * pout) / 1e6
    return a, ms, cost


def node(a):
    if a["emergency"] >= 0.7: return "Emergency Triage"
    if a["wants_human"] >= 0.7 or a["frustration"] >= 1.5: return "Human Handoff"
    return INTENT_NODE.get(a["intent"], "Clarify")
