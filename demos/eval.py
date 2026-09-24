"""20 realistic callers with the node a good receptionist would pick. Don't trust Jev (or any model): check it."""
import sys
sys.path.insert(0, "proxy"); sys.path.insert(0, "demos")
from router import route
from llm_router import ask, node

CASES = [
    ("my tooth got knocked out playing basketball", "Emergency Triage"),
    ("there's blood everywhere after my extraction yesterday", "Emergency Triage"),
    ("my jaw is swollen and I can barely open my mouth", "Emergency Triage"),
    ("I cracked a molar on a popcorn kernel and it hurts so bad", "Emergency Triage"),
    ("can I schedule a cleaning for my daughter", "Book Appointment"),
    ("I need to move my Thursday appointment", "Book Appointment"),
    ("do you have anything open next Monday morning", "Book Appointment"),
    ("I have to cancel tomorrow, sorry", "Book Appointment"),
    ("do you take MetLife", "Billing"),
    ("how much is a filling without insurance", "Billing"),
    ("I got a bill for 340 dollars and I don't understand it", "Billing"),
    ("can I pay in monthly installments", "Billing"),
    ("where do I park", "Hours and Location"),
    ("are you open on Sundays", "Hours and Location"),
    ("what's your address again", "Hours and Location"),
    ("let me speak to the office manager", "Human Handoff"),
    ("this is the third time I've called and nobody fixes my bill, I'm done", "Human Handoff"),
    ("I'd rather talk to a human, no offense", "Human Handoff"),
    ("hello?", "Clarify"),
    ("I'm calling about the thing from last week", "Clarify"),
]

jev_ok = luna_ok = 0
misses = []
for said, want in CASES:
    j = route(said)["next_node"]
    l = node(ask("gpt-6-luna", said)[0])
    jev_ok += j == want; luna_ok += l == want
    mark = "✓" if j == want else "✗"
    print(f"  {mark} {j:<20} want {want:<20} Luna {'✓' if l == want else '✗'}  | {said}", flush=True)
    if j != want: misses.append((said, j, want))
print(f"\n  Jev  {jev_ok}/{len(CASES)} correct\n  Luna {luna_ok}/{len(CASES)} correct")
for s, got, want in misses:
    print(f'  Jev miss: "{s}" → {got} (wanted {want})')
