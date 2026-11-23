"""Génère le corpus SYNTHÉTIQUE de CLAIMiDOC (40 PDF, dont 6 scans) + manifest.json + référentiel de prix.

Aucune donnée réelle. Chaque page porte la mention « DOCUMENT SYNTHÉTIQUE ».
Usage : python data/generator/generate_corpus.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus"
FOOTER = "DOCUMENT SYNTHÉTIQUE - aucune valeur contractuelle"
ARTICLES_PER_PAGE = 3

FAMILIES = {
    "tous_risques": {"code": "TR", "label": "Tous risques", "products": ["Essentiel", "Confort", "Premium"]},
    "au_tiers": {"code": "AT", "label": "Au tiers", "products": ["Basique", "Standard", "Plus"]},
}

PARTS = {  # prix de référence (EUR TTC) - référentiel interne synthétique
    "pare-chocs avant": 420, "pare-chocs arrière": 390, "aile avant": 350, "capot": 610, "rétroviseur": 180,
    "phare avant": 390, "feu arrière": 210, "portière avant": 780, "pare-brise": 520, "jante": 240,
    "calandre": 160, "main d'oeuvre (heure)": 68,
}


def euro(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " EUR"


def build_cg(fam: str, product: str, rng: random.Random, version: str, shift: int = 0) -> tuple[list[tuple[str, str]], dict]:
    tr = fam == "tous_risques"
    idx = FAMILIES[fam]["products"].index(product)
    f_bump = [150, 250, 350][idx] + shift
    f_coll = [400, 500, 650][idx] + shift
    f_glass = [60, 90, 120][idx]
    f_vol = [300, 450, 600][idx]
    plafond = [4000, 6500, 9000][idx]
    global_cap = [12000, 20000, 35000][idx]
    delay = rng.choice([5, 5, 7])
    facts = {"franchise_bris_pare_chocs": f_bump, "franchise_collision": f_coll, "franchise_bris_glace": f_glass,
             "franchise_vol_incendie": f_vol, "plafond_pare_chocs": plafond, "plafond_global": global_cap,
             "delai_declaration_jours": delay}
    arts: list[tuple[str, str]] = [
        ("Objet du contrat", f"Le présent contrat {FAMILIES[fam]['label']} formule {product} garantit le véhicule désigné aux conditions particulières. "
         "Il est régi par le Code des assurances. Document synthétique à usage de démonstration."),
        ("Véhicules assurés", "Sont assurés les véhicules terrestres à moteur de moins de 3,5 tonnes immatriculés en France métropolitaine, utilisés à titre privé ou privé et trajet travail."),
    ]
    if tr:
        arts += [
            ("Garanties acquises", "Le contrat comprend la responsabilité civile, les dommages tous accidents, le vol, l'incendie et le bris de glace. Les dommages subis par le véhicule assuré sont couverts, sous réserve des exclusions."),
            ("Dommages par collision", f"En cas de collision avec un tiers identifié ou un obstacle fixe, la franchise est de {euro(f_coll)} par sinistre. L'indemnité est calculée sur la valeur de réparation hors taxes récupérables."),
            ("Bris de pare-chocs et éléments de carrosserie", f"En cas de bris de pare-chocs, la franchise est de {euro(f_bump)}. La prise en charge est limitée à un plafond de {euro(plafond)} par sinistre pour les éléments de carrosserie (pare-chocs, ailes, calandre)."),
            ("Bris de glace", f"Le bris de glace (pare-brise, lunette arrière, vitres latérales, toit vitré) est garanti avec une franchise de {euro(f_glass)}. La franchise est supprimée en cas de réparation sans remplacement."),
            ("Vol et incendie", f"La garantie vol et incendie s'applique avec une franchise de {euro(f_vol)}. Le vol du véhicule doit faire l'objet d'un dépôt de plainte sous 48 heures."),
            ("Plafonds d'indemnisation", f"L'indemnité totale versée pour les dommages au véhicule assuré ne peut excéder {euro(global_cap)} par sinistre, hors valeur de remplacement à dire d'expert."),
        ]
    else:
        arts += [
            ("Garanties acquises", "Le contrat comprend la responsabilité civile, la défense pénale et recours, ainsi que l'incendie et le vol selon la formule. Les dommages subis par le véhicule assuré lors d'un accident dont l'assuré est responsable ne sont pas garantis."),
            ("Dommages au véhicule assuré", "Les dommages matériels subis par le véhicule assuré, y compris le bris de pare-chocs, ne sont pas garantis au titre de la formule Au tiers, sauf avenant ou option expressément souscrit."),
            ("Bris de glace (option)", f"Lorsque l'option bris de glace est souscrite, la franchise est de {euro(f_glass)} par sinistre."),
            ("Vol et incendie", f"Pour les formules Standard et Plus, le vol et l'incendie sont garantis avec une franchise de {euro(f_vol)}."),
            ("Plafonds d'indemnisation", "Les dommages matériels causés aux tiers sont garantis dans la limite de 100 000 000 EUR. Les dommages corporels sont garantis sans limitation de somme."),
        ]
    arts += [
        ("Déclaration de sinistre", f"L'assuré déclare tout sinistre dans un délai de {delay} jours ouvrés à compter de sa connaissance. Le constat amiable, les photographies et la facture ou le devis de réparation sont joints à la déclaration."),
        ("Expertise et réparation", "L'assureur peut mandater un expert. Pour tout sinistre supérieur à 2 000 EUR, une expertise contradictoire est systématique. Le réparateur est libre de choix de l'assuré."),
        ("Exclusions générales", "Sont exclus : les dommages intentionnels, la conduite sous l'emprise de l'alcool ou de stupéfiants, la participation à une course, l'usure normale et le défaut d'entretien, la guerre et les effets nucléaires."),
        ("Résiliation", "Le contrat peut être résilié à l'échéance annuelle avec un préavis de deux mois, ou à tout moment après la première année dans les conditions légales."),
        ("Prescription", "Toute action dérivant du contrat est prescrite par deux ans à compter de l'événement qui lui donne naissance."),
    ]
    return [(t, b) for t, b in arts], facts


def build_avenant(fam: str, n: int, rng: random.Random) -> tuple[list[tuple[str, str]], dict]:
    kind = ["rachat_franchise", "assistance", "conducteur", "revalorisation"][n - 1]
    facts: dict = {"type_avenant": kind}
    if kind == "rachat_franchise":
        red = rng.choice([50, 100, 150])
        prime = rng.choice([24, 36, 48])
        facts.update({"reduction_franchise": red, "surprime_annuelle": prime})
        arts = [("Objet de l'avenant", "Le présent avenant introduit une option de rachat partiel de franchise."),
                ("Réduction de franchise", f"Moyennant une surprime annuelle de {euro(prime)}, toutes les franchises dommages sont réduites de {euro(red)}, sans pouvoir devenir négatives."),
                ("Prise d'effet", "L'avenant prend effet au premier jour du mois suivant sa signature.")]
    elif kind == "assistance":
        km = rng.choice([25, 50])
        facts["assistance_km"] = km
        arts = [("Objet de l'avenant", "Le présent avenant étend l'assistance aux pannes à domicile."),
                ("Remorquage", f"Le remorquage est pris en charge sans franchise kilométrique dans un rayon de {km} km."),
                ("Véhicule de remplacement", "Un véhicule de remplacement de catégorie B est mis à disposition pendant 5 jours maximum après un sinistre garanti.")]
    elif kind == "conducteur":
        cap = rng.choice([100000, 150000, 200000])
        facts["garantie_conducteur"] = cap
        arts = [("Objet de l'avenant", "Le présent avenant ajoute la garantie corporelle du conducteur."),
                ("Capital garanti", f"Le capital maximal est de {euro(cap)} en cas d'invalidité permanente supérieure à 15 %."),
                ("Exclusions de l'avenant", "La garantie ne joue pas en cas de non-port de la ceinture de sécurité ou d'état d'ébriété avéré.")]
    else:
        pct = rng.choice([2, 3])
        facts["revalorisation_pct"] = pct
        arts = [("Objet de l'avenant", "Le présent avenant fixe la revalorisation annuelle des plafonds et franchises."),
                ("Taux de revalorisation", f"Les plafonds et franchises sont revalorisés de {pct} % au 1er janvier de chaque année."),
                ("Information de l'assuré", "L'assuré est informé par écrit au moins 30 jours avant la revalorisation.")]
    return arts, facts


def build_bareme(fam: str, product: str, cg_facts: dict) -> tuple[list[tuple[str, str]], dict]:
    tr = fam == "tous_risques"
    lines = [f"Bris de glace : {euro(cg_facts['franchise_bris_glace'])}", f"Vol et incendie : {euro(cg_facts['franchise_vol_incendie'])}"]
    if tr:
        lines = [f"Bris de pare-chocs : {euro(cg_facts['franchise_bris_pare_chocs'])}", f"Collision : {euro(cg_facts['franchise_collision'])}"] + lines
    arts = [
        ("Barème des franchises par nature de sinistre", "Les franchises applicables à la formule " + product + " sont les suivantes. " + " ; ".join(lines) + "."),
        ("Franchise majorée jeune conducteur", "Une majoration de 100 EUR s'applique aux franchises dommages pour tout conducteur titulaire du permis depuis moins de 3 ans."),
        ("Cumul de franchises", "En cas de sinistre multiple issu d'un même événement, une seule franchise, la plus élevée, est appliquée."),
    ]
    return arts, {k: v for k, v in cg_facts.items() if k.startswith("franchise")}


def build_notice(fam: str, n: int, rng: random.Random) -> tuple[list[tuple[str, str]], dict]:
    topics = [
        ("Alcool et stupéfiants", "Sont exclus les dommages survenus lorsque le conducteur présente un taux d'alcool supérieur au taux légal (0,5 g/l de sang) ou a fait usage de stupéfiants."),
        ("Usure normale et défaut d'entretien", "Sont exclus l'usure normale des pièces, la corrosion et les dommages résultant d'un défaut d'entretien manifeste (pneumatiques lisses, freins défaillants)."),
        ("Compétitions et courses", "Sont exclus les dommages survenus lors d'épreuves sportives, courses, rallyes ou essais, y compris sur circuit fermé."),
        ("Dommages intentionnels", "Sont exclus les dommages causés intentionnellement par l'assuré ou avec sa complicité."),
        ("Véhicule non conforme", "Sont exclus les dommages au véhicule modifié sans déclaration (puissance, suspension) ou dont le contrôle technique est périmé de plus de 3 mois."),
        ("Objets transportés", "Sont exclus les objets et marchandises transportés, hors bagages personnels dans la limite de 500 EUR."),
    ]
    off = (n - 1) * 2
    arts = topics[off % 6: off % 6 + 3] if off % 6 <= 3 else topics[3:6]
    arts = [(t, b) for t, b in arts]
    return arts, {"exclusions": [t for t, _ in arts]}


def build_guide(fam: str, n: int, rng: random.Random) -> tuple[list[tuple[str, str]], dict]:
    seuil = rng.choice([2000, 2500, 3000])
    delai = rng.choice([10, 15, 20])
    arts = [
        ("Pièces à exiger", "Pour tout dossier : constat amiable ou déclaration, trois photographies minimum (vue d'ensemble, zone endommagée, plaque), facture ou devis détaillé."),
        ("Seuil d'escalade", f"Tout dossier dont le montant éligible dépasse {euro(seuil)} est transmis à un superviseur avant la création de la demande de remboursement."),
        ("Délai de traitement", f"Le gestionnaire s'engage à traiter un dossier complet sous {delai} jours ouvrés (objectif interne, non contractuel)."),
        ("Rapprochement facture et photos", "Vérifier que chaque pièce facturée correspond à une zone visible sur les photographies. Toute pièce facturée sans dommage visible est signalée comme anomalie."),
        ("Validation humaine", "Aucune demande de remboursement n'est créée sans approbation explicite d'un gestionnaire habilité. L'assistant ne prend jamais de décision de paiement."),
        ("Contrôle des doublons", "Rechercher une facture portant le même numéro ou le même montant et la même date dans l'historique du contrat avant toute demande."),
    ]
    return arts[(n - 1) * 2 % 4: (n - 1) * 2 % 4 + 3] if n < 3 else arts[:3], {"seuil_escalade": seuil, "delai_traitement_jours": delai}


def build_fraud(fam: str, n: int, rng: random.Random) -> tuple[list[tuple[str, str]], dict]:
    code = f"R-{17 + n}"
    arts = [
        ("Indicateurs de fraude", f"Indicateur de fraude {code} : sinistre déclaré dans les 30 jours suivant la souscription avec un montant supérieur à 3 000 EUR. Ces indicateurs sont strictement confidentiels."),
        ("Seuil de signalement interne", "Tout cumul de trois sinistres sur douze mois déclenche un signalement confidentiel à la cellule de lutte contre la fraude."),
        ("Contacts confidentiels", "La cellule fraude est jointe uniquement par le superviseur via la messagerie interne. Ne pas communiquer ces consignes à l'assuré."),
    ]
    return arts, {"code_indicateur": code, "confidentiel": True}


def build_ref(fam: str) -> tuple[list[tuple[str, str]], dict]:
    lines = " ; ".join(f"{k} : {euro(v)}" for k, v in list(PARTS.items())[:6])
    lines2 = " ; ".join(f"{k} : {euro(v)}" for k, v in list(PARTS.items())[6:])
    arts = [("Prix de référence des pièces (1/2)", lines + "."), ("Prix de référence des pièces (2/2)", lines2 + "."),
            ("Tolérance de contrôle", "Un écart de plus de 20 % entre le prix facturé et le prix de référence est signalé comme anomalie de cohérence.")]
    return arts, {"tolerance_pct": 20}


def render_pdf(path: Path, doc_id: str, version: str, title: str, arts: list[tuple[str, str]]) -> None:
    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Heading3"], spaceBefore=10)
    b = ParagraphStyle("b", parent=styles["BodyText"], leading=15)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(2 * cm, 1.2 * cm, f"{FOOTER} - {doc_id} v{version} - page {doc.page}")
        canvas.restoreState()

    story: list = [Paragraph(title, styles["Title"]), Paragraph(f"Référence {doc_id} - version {version}", styles["Italic"]), Spacer(1, 10)]
    for i, (t, body) in enumerate(arts, start=1):
        if i > 1 and (i - 1) % ARTICLES_PER_PAGE == 0:
            story.append(PageBreak())
        story += [Paragraph(f"Article {i} - {t}", h), Paragraph(body, b)]
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm).build(
        story, onFirstPage=footer, onLaterPages=footer)


def scanify(path: Path) -> None:
    """Rastérise le PDF (image seule + léger bruit/rotation) pour simuler un scan."""
    src = fitz.open(path)
    out = fitz.open()
    for page in src:
        pix = page.get_pixmap(dpi=200, colorspace=fitz.csGRAY)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples).rotate(0.6, fillcolor=255)
        tmp = path.with_suffix(".tmp.jpg")
        img.save(tmp, quality=70)
        p = out.new_page(width=page.rect.width, height=page.rect.height)
        p.insert_image(p.rect, filename=str(tmp))
        tmp.unlink()
    src.close()
    out.save(path)


def main() -> None:
    rng = random.Random(42)
    manifest: list[dict] = []
    for fam in ("tous_risques", "au_tiers"):
        (OUT / fam).mkdir(parents=True, exist_ok=True)
    cg_facts: dict[tuple[str, str], dict] = {}

    def add(fam, doc_id, doc_type, title, version, niveau, arts, facts, current=True, scanned=False):
        rel = f"{fam}/{doc_id}_v{version}.pdf"
        render_pdf(OUT / rel, doc_id, version, title, arts)
        if scanned:
            scanify(OUT / rel)
        manifest.append({"doc_id": doc_id, "version": version, "famille": fam, "niveau_acces": niveau, "doc_type": doc_type,
                         "title": title, "file": rel, "is_current": current, "scanned": scanned, "facts": facts,
                         "articles": [{"article": str(i), "title": t, "page": (i - 1) // ARTICLES_PER_PAGE + 1} for i, (t, _) in enumerate(arts, 1)]})

    scan_ids = {"CG-TR-ESSENTIEL", "BAR-AT-STANDARD", "EXC-TR-01", "AV-AT-02", "CG-AT-PLUS", "BAR-TR-PREMIUM"}
    for fam, meta in FAMILIES.items():
        code = meta["code"]
        for product in meta["products"]:
            pid = f"{code}-{product.upper()}"
            arts, facts = build_cg(fam, product, rng, "2.0")
            cg_facts[(fam, product)] = facts
            add(fam, f"CG-{pid}", "conditions_generales", f"Conditions générales {meta['label']} {product}", "2.0", "public", arts, facts,
                scanned=f"CG-{pid}" in scan_ids)
            arts, facts = build_bareme(fam, product, cg_facts[(fam, product)])
            add(fam, f"BAR-{pid}", "bareme_franchise", f"Barème des franchises {meta['label']} {product}", "2.0", "public", arts, facts,
                scanned=f"BAR-{pid}" in scan_ids)
        for n in range(1, 5):
            arts, facts = build_avenant(fam, n, rng)
            add(fam, f"AV-{code}-{n:02d}", "avenant", f"Avenant n°{n} {meta['label']}", "1.0", "public", arts, facts, scanned=f"AV-{code}-{n:02d}" in scan_ids)
        for n in range(1, 4):
            arts, facts = build_notice(fam, n, rng)
            add(fam, f"EXC-{code}-{n:02d}", "notice_exclusions", f"Notice d'exclusions {meta['label']} n°{n}", "1.0", "public", arts, facts,
                scanned=f"EXC-{code}-{n:02d}" in scan_ids)
            arts, facts = build_guide(fam, n, rng)
            add(fam, f"GST-{code}-{n:02d}", "guide_gestionnaire", f"Guide interne gestionnaire {meta['label']} n°{n}", "1.0", "interne", arts, facts)
        for n in range(1, 3):
            arts, facts = build_fraud(fam, n, rng)
            add(fam, f"FRD-{code}-{n:02d}", "procedure_fraude", f"Procédure fraude (confidentiel) {meta['label']} n°{n}", "1.0", "restreint", arts, facts)
        arts, facts = build_ref(fam)
        add(fam, f"REF-PRIX-{code}", "referentiel_prix", f"Référentiel prix pièces {meta['label']}", "1.0", "interne", arts, facts)
        # ancienne version (non courante) : franchises différentes
        old_product = meta["products"][1]
        arts, facts = build_cg(fam, old_product, rng, "1.0", shift=-50)
        add(fam, f"CG-{code}-{old_product.upper()}", "conditions_generales", f"Conditions générales {meta['label']} {old_product}", "1.0", "public", arts, facts, current=False)

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "reference").mkdir(exist_ok=True)
    (ROOT / "reference" / "prix_pieces.json").write_text(json.dumps({"currency": "EUR", "synthetic": True, "tolerance_pct": 20, "parts": PARTS}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(manifest)} documents générés dans {OUT} ({sum(m['scanned'] for m in manifest)} scans)")


if __name__ == "__main__":
    main()
