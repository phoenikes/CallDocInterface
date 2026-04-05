"""
DRY-RUN TEST: Ablation (Type 25) + Diagnostik (Type 24) am 07.04.2026
Simuliert den kompletten Mapping-Pfad OHNE Schreibzugriffe.
"""
import json
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient

def run_dryrun():
    print("=" * 80)
    print("DRY-RUN TEST: Ablation + Diagnostik am 07.04.2026")
    print("=" * 80)

    # --- 1. CallDoc Abfrage ---
    ci = CallDocInterface(from_date="2026-04-07", to_date="2026-04-07")

    r24 = ci.appointment_search(appointment_type_id=24)
    apts_24 = [a for a in r24.get("data", []) if a.get("status") not in ("blocker",)]
    print(f"\n[1] CallDoc Type 24 (HK Diagnostik): {len(apts_24)} Termine")
    for a in apts_24:
        zeit = a.get("scheduled_for_datetime", "")[11:16]
        print(f"    {zeit} | {a.get('surname','?')}, {a.get('name','?')} | PIZ:{a.get('piz','-')} | room:{a.get('room')} | employee:{a.get('employee')} | status:{a.get('status')}")

    r25 = ci.appointment_search(appointment_type_id=25)
    apts_25 = [a for a in r25.get("data", []) if a.get("status") not in ("blocker",)]
    print(f"\n[2] CallDoc Type 25 (Ablation): {len(apts_25)} Termine")
    for a in apts_25:
        zeit = a.get("scheduled_for_datetime", "")[11:16]
        print(f"    {zeit} | {a.get('surname','?')}, {a.get('name','?')} | PIZ:{a.get('piz','-')} | room:{a.get('room')} | employee:{a.get('employee')} | status:{a.get('status')}")

    # --- 2. SQLHK Mappings laden ---
    mssql = MsSqlApiClient()
    print(f"\n[3] SQLHK Mappings pruefen...")

    # Untersuchungart-Mapping (AKTUELL in DB)
    q_ua = """SELECT UntersuchungartID, UntersuchungartName,
              JSON_VALUE(appointment_type, '$."1"') AS calldoc_type
              FROM [SQLHK].[dbo].[Untersuchungart]"""
    ua_result = mssql.execute_sql(q_ua, "SQLHK")
    ua_map_current = {}
    if ua_result.get("success"):
        for row in ua_result["rows"]:
            ct = row.get("calldoc_type")
            if ct:
                ua_map_current[int(ct)] = {
                    "id": row["UntersuchungartID"],
                    "name": row["UntersuchungartName"],
                }

    print(f"    AKTUELLES DB-Mapping:")
    print(f"      CallDoc 24 -> {ua_map_current.get(24, 'NICHT GEFUNDEN')}")
    print(f"      CallDoc 25 -> {ua_map_current.get(25, 'NICHT GEFUNDEN')} *** FALSCH: zeigt auf KV Intervention!")
    print(f"      CallDoc 31 -> {ua_map_current.get(31, 'NICHT GEFUNDEN')} *** Ablation haengt hier falsch")

    # SIMULIERTES Mapping nach DB-Fix
    ua_map_fixed = dict(ua_map_current)
    del ua_map_fixed[25]  # KV Intervention raus
    ua_map_fixed[25] = {"id": 8, "name": "Ablation"}  # 25 -> Ablation
    # 31 bleibt weg (war nur internes Mapping)
    if 31 in ua_map_fixed:
        del ua_map_fixed[31]

    print(f"\n    NACH DB-FIX:")
    print(f"      CallDoc 24 -> {ua_map_fixed.get(24)}")
    print(f"      CallDoc 25 -> {ua_map_fixed.get(25)}")

    # Herzkatheter-Mapping
    q_hk = "SELECT HerzkatheterID, HerzkatheterName, room_id FROM [SQLHK].[dbo].[Herzkatheter] WHERE room_id IS NOT NULL"
    hk_result = mssql.execute_sql(q_hk, "SQLHK")
    hk_map = {}
    if hk_result.get("success"):
        for row in hk_result["rows"]:
            rid = row.get("room_id")
            if rid:
                hk_map[int(rid)] = {
                    "id": row["HerzkatheterID"],
                    "name": row["HerzkatheterName"],
                }
    print(f"    Herzkatheter room->HK: {json.dumps(hk_map, ensure_ascii=False, default=str)}")

    # employee_id -> Name (aus Zuweiser-Tabelle)
    q_emp = "SELECT employee_id, ZuweiserName, ZuweiserVorname FROM [SQLHK].[dbo].[Zuweiser] WHERE employee_id IS NOT NULL"
    emp_result = mssql.execute_sql(q_emp, "SQLHK")
    emp_map = {}
    if emp_result.get("success"):
        for row in emp_result["rows"]:
            eid = row.get("employee_id")
            if eid:
                emp_map[int(eid)] = row["ZuweiserName"]

    # --- 3. Simulation ---
    print()
    print("=" * 80)
    print("[4] SIMULATION: Was wuerde in Untersuchung-Tabelle landen?")
    print("=" * 80)

    errors = []
    results = []

    for apt_type, apts, type_label in [(24, apts_24, "DIAGNOSTIK"), (25, apts_25, "ABLATION")]:
        for a in apts:
            status = a.get("status")
            if status == "canceled":
                continue

            piz = a.get("piz", "-")
            name = f"{a.get('surname', '?')}, {a.get('name', '?')}"
            room = a.get("room")
            employee = a.get("employee")
            zeit = a.get("scheduled_for_datetime", "")[11:16]

            # UntersuchungartID
            ua_info = ua_map_fixed.get(apt_type)
            ua_id = ua_info["id"] if ua_info else "???"
            ua_name = ua_info["name"] if ua_info else "???"

            # Herzkatheter + Zuweiser - Ablation-Sonderlogik
            if apt_type == 25:
                zuweiser_id = 7
                zuweiser_name = "Duckheim"
                hk_id = 2
                hk_name = "Rummelsberg 2"
                hk_info = True  # immer ok
            else:
                zuweiser_id = 2
                zuweiser_name = "Sandrock"
                hk_info = hk_map.get(room)
                hk_id = hk_info["id"] if hk_info else "???"
                hk_name = hk_info["name"] if hk_info else "???"

            untersucher_name = emp_map.get(employee, "???")

            # Validierung
            err_detail = []
            if not ua_info:
                err_detail.append(f"UntersuchungartID fehlt (type={apt_type})")
            if not hk_info:
                err_detail.append(f"HerzkatheterID fehlt (room={room})")
            if not employee:
                err_detail.append("employee fehlt")
            if untersucher_name == "???":
                err_detail.append(f"employee {employee} nicht in Zuweiser-Tabelle")

            ok = len(err_detail) == 0
            marker = "OK" if ok else "FEHLER"
            if not ok:
                errors.append(f"{name}: {' | '.join(err_detail)}")

            results.append({
                "type": type_label,
                "zeit": zeit,
                "name": name,
                "piz": piz,
                "ua": f"{ua_id} ({ua_name})",
                "hk": f"{hk_id} ({hk_name})",
                "untersucher": f"{employee} ({untersucher_name})",
                "zuweiser": f"{zuweiser_id} ({zuweiser_name})",
                "status": marker,
            })

    # Ausgabe
    header = f"{'Typ':<12} {'Zeit':<6} {'Patient':<28} {'PIZ':<10} {'UntArt':<28} {'HK':<20} {'Untersucher':<22} {'Zuweiser':<18} {'OK?'}"
    print(f"\n{header}")
    print("-" * len(header))
    for r in results:
        print(
            f"{r['type']:<12} {r['zeit']:<6} {r['name']:<28} {r['piz']:<10} "
            f"{r['ua']:<28} {r['hk']:<20} {r['untersucher']:<22} "
            f"{r['zuweiser']:<18} {r['status']}"
        )

    # Zusammenfassung
    diag_count = len([r for r in results if r["type"] == "DIAGNOSTIK"])
    abl_count = len([r for r in results if r["type"] == "ABLATION"])
    ok_count = len([r for r in results if r["status"] == "OK"])
    err_count = len([r for r in results if r["status"] == "FEHLER"])

    print(f"\n{'='*60}")
    print(f"ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"Diagnostik (Type 24): {diag_count} Termine (nicht-canceled)")
    print(f"Ablation   (Type 25): {abl_count} Termine (nicht-canceled)")
    print(f"Total:                {diag_count + abl_count}")
    print(f"OK:                   {ok_count}")
    print(f"FEHLER:               {err_count}")

    if errors:
        print(f"\nFEHLER-DETAILS:")
        for e in errors:
            print(f"  ! {e}")
    else:
        print(f"\n>>> ALLE MAPPINGS KORREKT - Bereit fuer Umsetzung! <<<")

    return err_count == 0


if __name__ == "__main__":
    success = run_dryrun()
    print(f"\nTest-Ergebnis: {'BESTANDEN' if success else 'FEHLGESCHLAGEN'}")
