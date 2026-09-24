"""Create (or re-point) the Jev router endpoint, then the Brightside scenario with a hosted link.
  python3 scripts/setup_akapulu.py https://<your-ngrok>.ngrok-free.app
Run again with a new URL after restarting ngrok: it updates the endpoint in place."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = Path.home() / "site-to-avatar/.agents/skills/akapulu-avatar/scripts"
sys.path.insert(0, str(HELPER))
import akapulu_api as ak  # request(), load_key()

CLARA = "1f777f64-3758-4a7d-9cbc-c64ae654f7d1"
STATE = ROOT / ".akapulu.json"


def main():
    base = sys.argv[1].rstrip("/")
    key = ak.key_or_die()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    endpoint = {"name": "Jev router", "url": f"{base}/route",
                "body": {"caller_said": "{{llm.caller_said:The caller's exact words, verbatim}}"}}
    if state.get("endpoint_id"):
        ak.request("POST", "/endpoints/update/", key, {"id": state["endpoint_id"], **endpoint})
        print("endpoint re-pointed to", endpoint["url"])
    else:
        r = ak.request("POST", "/endpoints/create/", key, endpoint)
        state["endpoint_id"] = r.get("id") or r.get("endpoint", {}).get("id")
        print("endpoint created", state["endpoint_id"])
    STATE.write_text(json.dumps(state, indent=2))
    if state.get("scenario_id"):
        print("scenario already exists:", state["url"])
        return
    nodes = (ROOT / "scenario/brightside.json").read_text().replace("PASTE_YOUR_ENDPOINT_ID", state["endpoint_id"])
    built = ROOT / "scenario/.built.json"
    built.write_text(nodes)
    subprocess.run([sys.executable, str(HELPER / "validate_scenario.py"), str(built)], check=True)
    r = ak.request("POST", "/scenarios/create/", key, {"name": "Brightside Dental (Jev router)", "nodes_json": json.loads(nodes),
                   "hosted_links": [{"avatar_id": CLARA, "label": "Brightside front desk", "stt_keywords": ["Brightside", "Maya"]}]})
    sc = r.get("scenario", r)
    state["scenario_id"] = sc.get("id")
    state["url"] = (sc.get("hosted_links") or [{}])[0].get("url")
    STATE.write_text(json.dumps(state, indent=2))
    print("scenario", state["scenario_id"], "\nhosted link:", state["url"])


if __name__ == "__main__":
    main()
