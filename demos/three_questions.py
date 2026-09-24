"""One caller line, Jev's three decision types. Run: python3 demos/three_questions.py "my face is swelling" """
import sys
sys.path.insert(0, "proxy")
from router import route

line = " ".join(sys.argv[1:]) or "Hi, my tooth has been throbbing all night and my face is swelling. Can someone see me today?"
r = route(line)
a = r["answers"]
print(f'\n  Caller: "{line}"\n')
print(f'  CHOICE   intent       → {a["intent"]["choice"]}  ({r["confidence"]["intent"]:.0%} confident)')
print(f'  YES/NO   emergency    → {a["emergency"]["probability"]:.0%} yes')
print(f'  YES/NO   wants human  → {a["wants_human"]["probability"]:.0%} yes')
print(f'  SCORE    frustration  → {a["frustration"]["score"]:.1f} of 2  (0 calm, 1 annoyed, 2 very frustrated)')
print(f'\n  Code decides → {r["next_node"]}   because {r["why"]}')
print(f'  Jev took {r["jev_ms"]} ms · {r["round_trip_ms"]} ms round trip · {r["input_tokens"]} tokens in, 0 words out\n')
