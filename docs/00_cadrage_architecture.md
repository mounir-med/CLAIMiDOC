# L1.1 — Note de cadrage et architecture

## Objectif
CLAIMiDOC est **une seule application**, livrée en 4 incréments, qui assiste les gestionnaires de sinistres automobiles :
réponses **sourcées** (document, page, article) sur des contrats PDF, analyse de photos/factures, consultation d'un historique via **MCP**,
et préparation de demandes de remboursement **soumises à validation humaine explicite**.
Le système ne paie jamais seul ; ses sorties sont des aides à la décision. Toutes les données sont **synthétiques**.

## Architecture
```
Navigateur ──► Next.js (route handlers, cookie httpOnly) ──► FastAPI ──► Qdrant (hybride dense+sparse, filtre niveau_acces)
Telegram ──► bot aiogram ──────────────────────────────────►   │  ├─► PostgreSQL (users, sessions, audit, checkpoints LangGraph)
                                                                │  ├─► MinIO (fichiers)  ├─► MLflow (expériences)
                                                                │  ├─► VLM (Qwen2.5-VL via vLLM / API OpenAI-compatible)
                                                                │  └─► LangGraph ──► client MCP ──► serveur MCP (3 outils, autorisation serveur)
```

## Flux RAG (étape 1)
1. Ingestion : PyMuPDF (natif) ou OCR Tesseract (scans) → découpage **par article et par page** → métadonnées
   (`doc_id, version, page, article, famille, niveau_acces, hash_contenu, is_current`) → embeddings → Qdrant.
2. Requête : le **rôle** (lu en base, jamais envoyé par le client) détermine les niveaux autorisés ; le filtre est appliqué **dans la requête Qdrant**
   (dans chaque `Prefetch` ET au niveau final), avant tout passage au LLM.
3. Recherche hybride (dense + sparse, fusion RRF) → quarantaine des passages ressemblant à une injection → reranking → seuil → génération JSON → **validation des citations** (chaque citation doit correspondre à un passage récupéré et accessible). Sans source valide : « information non trouvée ».

## Flux agentique (étape 3)
`réception → validation → analyse (historique MCP + règles RAG) → cohérence → brouillon → INTERRUPTION → création → clôture`
(+ branches refus / annulation). Checkpoints LangGraph (PostgreSQL en production). Le JWT utilisateur n'est jamais écrit dans l'état/checkpoint.

### Approbation
- Hash du contenu = SHA-256 du JSON canonique `{policy_id, title, description}` (ce que l'humain voit et ce que reçoit le serveur MCP).
- `approval_token` = HMAC(secret, {hash, approbateur, jti, expiration}) ; **usage unique** (table `used_tokens` du service sinistres), durée limitée (15 min par défaut).
- Toute modification du brouillon change le hash → l'approbation antérieure est inutilisable (API 409 + rejet côté MCP).
- Idempotence : clé = SHA-256(hash + contrat) ; un rejeu renvoie la demande existante (`duplicate: true`).
- Calcul : `min(montant_éligible − franchise, plafond)` borné à 0, en `Decimal`, code déterministe ; franchise/plafond extraits des passages cités par regex (pas par le LLM).

## Sécurité (contraintes non négociables)
Permissions côté serveur uniquement (FastAPI + MCP) · contenus PDF/images = données (quarantaine, liste fermée de zones VLM, délimiteurs échappés) ·
secrets en variables d'environnement (`require()` refuse les secrets absents/courts) · limitation de débit par utilisateur ·
audit minimal (utilisateur, action, horodatage, identifiant de dossier, issue ; jamais de contenu) · 404 identique pour « inexistant » et « interdit » sur les documents.

## Décisions techniques notables
| Sujet | Choix | Raison |
|---|---|---|
| Hybride | BGE-M3 dense + poids lexicaux creux dans Qdrant | un seul index, filtre uniforme |
| Tests/CI | `HashEmbedder`, `LexicalReranker`, `StubLLM/StubVLM`, Qdrant `:memory:` | reproductibilité sans GPU ni réseau |
| MCP | SDK `mcp<2` (FastMCP) | la v2 renomme FastMCP ; épinglé |
| Frontend → API | proxy Next.js avec liste blanche de préfixes | cookie httpOnly, aucun jeton dans le navigateur |
