"""Same caller, same four questions: Jev vs GPT-6 Luna vs GPT-6 Sol. In a live call, every half second is dead air."""
import statistics, sys
sys.path.insert(0, "proxy"); sys.path.insert(0, "demos")
from router import route
from llm_router import ask, node

LINES = ["my face is swelling and my tooth is killing me",
         "can I book a cleaning for next week",
         "why did you charge me twice",
         "I want to talk to a real person right now",
         "what time do you open on saturday"]
RUNS = 2
rows = {"Jev": [], "GPT-6 Luna": [], "GPT-6 Sol": []}
cost = {k: 0.0 for k in rows}
for line in LINES:
    for _ in range(RUNS):
        r = route(line); rows["Jev"].append((r["round_trip_ms"], r["next_node"])); cost["Jev"] += r["input_tokens"] * 0.042 / 1e6
        for name, model in [("GPT-6 Luna", "gpt-6-luna"), ("GPT-6 Sol", "gpt-6-sol")]:
            a, ms, c = ask(model, line); rows[name].append((ms, node(a))); cost[name] += c
    print(f'  {line[:44]:<46} Jev → {r["next_node"]}', flush=True)
n = len(LINES) * RUNS
print(f'\n  {"model":<12}{"median":>10}{"slowest":>10}{"per 1,000 calls":>18}')
for k, v in rows.items():
    ms = [x[0] for x in v]
    print(f'  {k:<12}{statistics.median(ms):>8.0f}ms{max(ms):>8.0f}ms{cost[k] / n * 1000:>17.4f}$')
jev = statistics.median(x[0] for x in rows["Jev"])
for k in ["GPT-6 Luna", "GPT-6 Sol"]:
    print(f'  {k} is {statistics.median(x[0] for x in rows[k]) / jev:.1f}x slower than Jev')
