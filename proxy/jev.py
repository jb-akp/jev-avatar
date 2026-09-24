"""Tiny client for Jev on Vercel AI Gateway. Jev never writes text: it answers typed questions."""
import json, os, time, urllib.error, urllib.request
from pathlib import Path

URL = "https://ai-gateway.vercel.sh/v1/evaluate"


def key():
    if os.environ.get("AI_GATEWAY_API_KEY"):
        return os.environ["AI_GATEWAY_API_KEY"]
    for line in (Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
        if line.startswith("AI_GATEWAY_API_KEY="):
            return line.split("=", 1)[1].strip()


def evaluate(state, questions):
    body = json.dumps({"model": "typesafe-ai/jev", "state": state, "questions": questions}).encode()
    req = urllib.request.Request(URL, body, {"Authorization": f"Bearer {key()}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        data = json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.HTTPError as e:
        if e.code < 500:
            raise
        data = json.load(urllib.request.urlopen(req, timeout=15))
    data["round_trip_ms"] = round((time.perf_counter() - t0) * 1000)
    attempt = data["providerMetadata"]["gateway"]["routing"]["modelAttempts"][0]["providerAttempts"][0]
    data["jev_ms"] = attempt["endTime"] - attempt["startTime"]
    return data
