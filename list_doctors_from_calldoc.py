"""Holt die komplette Aerzte-/Mitarbeiterliste direkt aus CallDoc /doctors/."""
import requests
from constants import DOCTORS

URL = "http://192.168.1.76:8001/api/v1/frontend/doctors/"
r = requests.get(URL, timeout=15)
r.raise_for_status()
data = r.json().get("data", [])

# Reverse-Map: CallDoc id -> constants-Name
mapped = set(DOCTORS.values())

print(f"CallDoc /doctors/ -> {len(data)} Eintraege\n")
print(f"{'id':>6} | {'role':<10} | {'in constants?':<13} | Name")
print("-" * 70)
for d in sorted(data, key=lambda x: x.get("id", 0)):
    did = d.get("id")
    name = " ".join(filter(None, [
        (d.get("title") or "").strip(),
        (d.get("first_name") or "").strip(),
        (d.get("last_name") or "").strip(),
    ]))
    role = d.get("role") or "-"
    flag = "JA" if did in mapped else ">> FEHLT <<"
    print(f"{did:>6} | {role:<10} | {flag:<13} | {name}")

doctors = [d for d in data if (d.get("role") == "Doctor")]
print(f"\nGesamt: {len(data)} | role=Doctor: {len(doctors)}")
fehlend = [d for d in data if d.get("role") == "Doctor" and d.get("id") not in mapped]
print(f"\nAerzte (role=Doctor) NICHT in constants.py: {len(fehlend)}")
for d in sorted(fehlend, key=lambda x: x.get("id", 0)):
    name = " ".join(filter(None, [(d.get("title") or ""), (d.get("first_name") or ""), (d.get("last_name") or "")]))
    print(f"  id={d.get('id'):<7} {name}")
