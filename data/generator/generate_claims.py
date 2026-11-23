"""Historique de sinistres SYNTHÉTIQUE pour le serveur MCP simulé."""
import json
import random
from pathlib import Path

rng = random.Random(7)
POLICIES = [("P-1001", "CG-TR-CONFORT"), ("P-1002", "CG-TR-PREMIUM"), ("P-1003", "CG-TR-ESSENTIEL"), ("P-1004", "CG-AT-STANDARD"),
            ("P-1005", "CG-AT-BASIQUE"), ("P-1006", "CG-TR-CONFORT"), ("P-1007", "CG-AT-PLUS"), ("P-1008", "CG-TR-PREMIUM")]
claims = []
for pid, _ in POLICIES:
    for k in range(rng.randint(1, 4)):
        claims.append({"claim_id": f"S-{pid[2:]}-{k+1}", "policy_id": pid, "date": f"2026-0{rng.randint(1, 9)}-{rng.randint(10, 28)}",
                       "status": rng.choice(["clos", "clos", "en_cours"]), "amount": rng.choice([320, 480, 760, 1250, 2100]),
                       "invoice_number": f"F-{rng.randint(10000, 99999)}", "label": rng.choice(["Bris de pare-chocs", "Collision", "Bris de glace"])})
# cas de test déterministe pour la détection de doublon
claims.append({"claim_id": "S-1001-9", "policy_id": "P-1001", "date": "2026-03-12", "status": "clos", "amount": 870,
               "invoice_number": "F-20260", "label": "Bris de pare-chocs"})
out = {"synthetic": True, "policies": [{"policy_id": p, "contract_doc_id": d} for p, d in POLICIES], "claims": claims}
path = Path(__file__).resolve().parents[1] / "claims_history" / "claims.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{len(claims)} sinistres synthétiques")
