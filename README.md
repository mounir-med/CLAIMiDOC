# CLAIMiDOC

**Assistant documentaire multimodal et agentique pour gestionnaires de sinistres automobiles.**

CLAIMiDOC lit des contrats d'assurance (PDF) et des photographies de dégâts, produit des réponses **sourcées** (document, page, article), consulte un historique de sinistres via **MCP** et prépare des demandes de remboursement **soumises à une validation humaine explicite**.

> ⚠️ **Toutes les données sont synthétiques** (contrats, factures, historiques). Aucune donnée personnelle réelle.
> Le système **ne paie jamais seul**, ne remplace pas un gestionnaire habilité et ne garantit aucun diagnostic ni montant : ses sorties sont des **aides à la décision**.

---

## Sommaire

1. [Fonctionnalités](#1-fonctionnalités)
2. [Architecture](#2-architecture)
3. [Stack technique](#3-stack-technique)
4. [Structure du dépôt](#4-structure-du-dépôt)
5. [Démarrage rapide (local, sans GPU)](#5-démarrage-rapide-local-sans-gpu)
6. [Démarrage avec Docker Compose](#6-démarrage-avec-docker-compose)
7. [Utiliser avec les vrais modèles](#7-utiliser-avec-les-vrais-modèles)
8. [Comptes, rôles et permissions](#8-comptes-rôles-et-permissions)
9. [Utilisation](#9-utilisation)
10. [Référence de l'API](#10-référence-de-lapi)
11. [Configuration (variables d'environnement)](#11-configuration-variables-denvironnement)
12. [Sécurité](#12-sécurité)
13. [Tests et évaluation](#13-tests-et-évaluation)
14. [État du projet et limites connues](#14-état-du-projet-et-limites-connues)
15. [Dépannage](#15-dépannage)
16. [Documentation complémentaire](#16-documentation-complémentaire)

---

## 1. Fonctionnalités

Le projet est **une seule application** construite en 4 incréments.

| Étape | Contenu |
|---|---|
| **1. Socle documentaire & RAG** | Corpus synthétique de 40 PDF (contrats « tous risques » et « au tiers », avenants, barèmes, notices d'exclusions, guides internes, procédures confidentielles ; dont 6 scans). Ingestion PyMuPDF + OCR Tesseract, découpage **par article et par page**, recherche hybride (dense + sparse) avec **filtrage d'accès dans la requête Qdrant**, reranking, réponses avec citations validées, refus « information non trouvée » hors corpus. |
| **2. Multimodal & reranker** | Analyse de photos de dégâts (zones, gravité apparente, qualité, **message de clarification** si photo insuffisante), lecture de factures, extraction de figures, fusion RRF, jeu d'adaptation de 954 exemples sans fuite, script d'entraînement du reranker (MLflow) et comparaison nDCG@5 / MRR@10. |
| **3. Orchestration & MCP** | Graphe **LangGraph** avec interruption pour approbation humaine, vérifications de cohérence (totaux, prix vs référentiel, photos vs facture, doublons, dates), serveur **MCP (FastMCP) à exactement 3 outils**, client MCP, brouillon de demande, jeton d'approbation (`approval_token`) et idempotence. |
| **4. Bot, sécurité, déploiement** | Bot Telegram (aiogram), liaison des comptes, Docker Compose, tests de sécurité (accès, injection, approbation), 150 scénarios d'évaluation. |
| **Frontend** | Next.js : design system, connexion, tableau de bord, espace dossier à 3 panneaux redimensionnables (pièces / conversation / visionneuse PDF), citations cliquables avec aperçu, analyse de photos, cohérence, brouillon et modale d'approbation, chronologie du workflow, évaluation, administration, palette Ctrl/⌘+K, mode clair/sombre, accessibilité. |

### Les 3 outils MCP

| Outil | Rôle |
|---|---|
| `get_claim_history(policy_id)` | Historique des sinistres d'un contrat |
| `get_open_claims(policy_id)` | Sinistres en cours |
| `create_reimbursement_request(policy_id, title, description, approval_token)` | Crée une demande ; refuse sans jeton d'approbation valide |

### Règle de calcul (déterministe, jamais faite par le LLM)

```
remboursement = min(montant_éligible − franchise, plafond)    (borné à 0 ; montants en Decimal)
```

La franchise et le plafond sont extraits des passages cités par expressions régulières, pas par un modèle de langage.

---

## 2. Architecture

```
Navigateur ──► Next.js (route handlers, cookie httpOnly) ──► FastAPI ──► Qdrant (hybride + filtre niveau_acces)
Telegram ──► bot aiogram ──────────────────────────────────►   │  ├─► PostgreSQL (users, sessions, audit, checkpoints LangGraph)
                                                                │  ├─► MinIO (fichiers)    ├─► MLflow (expériences)
                                                                │  ├─► VLM (Qwen2.5-VL via vLLM / API compatible OpenAI)
                                                                │  └─► LangGraph ──► client MCP ──► serveur MCP (3 outils, autorisation serveur)
```

### Flux d'une question (RAG)

1. Le **rôle** de l'utilisateur est relu en base (jamais fourni par le client) et détermine les niveaux d'accès autorisés.
2. Recherche hybride Qdrant : le **filtre d'accès est appliqué dans chaque `Prefetch` et au niveau final**, avant tout passage au LLM.
3. Mise en **quarantaine** des passages ressemblant à une injection de prompt, reranking, seuil de pertinence.
4. Génération au format JSON, puis **validation des citations** : chaque citation doit correspondre à un passage réellement récupéré et accessible.
5. Sans source valide : réponse « Information non trouvée ».

### Flux agentique (workflow)

```
réception → validation → analyse (historique MCP + règles RAG) → cohérence → brouillon
        → ⏸ INTERRUPTION (approbation humaine) → création → clôture
        (branches : refus, annulation)
```

### Approbation humaine

- **Hash du contenu** : SHA-256 du JSON canonique `{policy_id, title, description}` (ce que l'humain voit et ce que reçoit le serveur MCP).
- **`approval_token`** : HMAC lié au hash, à l'identifiant de l'approbateur, à une expiration (15 min par défaut) et à un identifiant unique (**usage unique**, imposé côté serveur MCP).
- **Toute modification du brouillon change le hash** : l'approbation antérieure est refusée (API 409 + rejet MCP).
- **Idempotence** : clé = SHA-256(hash + contrat) ; un rejeu renvoie la demande existante (`duplicate: true`).
- **Escalade** : au-delà de 2 500 EUR de montant éligible, seul un superviseur peut approuver.
- Le JWT de l'utilisateur n'est **jamais** écrit dans l'état ni dans les checkpoints du graphe.

---

## 3. Stack technique

| Domaine | Technologies |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, Alembic, PostgreSQL |
| RAG | LangChain (Runnables), PyMuPDF, OCR Tesseract, embeddings BGE-M3, Qdrant |
| Multimodal | Qwen2.5-VL-7B-Instruct (vLLM ou API compatible OpenAI), encodeur CLIP multilingue |
| Reranking | Cross-encoder multilingue (`BAAI/bge-reranker-v2-m3`, modèle léger adapté) |
| Orchestration | LangGraph (interruption, checkpoints en base) |
| MCP | SDK Python MCP `<2` (FastMCP) — serveur **et** client |
| Stockage / suivi | MinIO, MLflow |
| Frontend | Next.js 15 (App Router), React, TypeScript, Tailwind CSS, Framer Motion, TanStack Query, Zod, Auth.js, react-pdf, Recharts, cmdk, lucide-react |
| Bot | aiogram 3 |
| Déploiement | Docker Compose |
| Qualité | pytest, Ruff, mypy, Vitest, Playwright, pre-commit |

> Pour les tests hors-ligne, des substituts déterministes remplacent les modèles lourds : `HashEmbedder`, `LexicalReranker`, `StubLLM`, `StubVLM`, et Qdrant en mémoire.

---

## 4. Structure du dépôt

```
claimidoc/
├── README.md · Makefile · docker-compose.yml · .env.example · pyproject.toml (Ruff)
├── backend/
│   ├── app/
│   │   ├── api/          routes : auth, ask (+SSE), documents, claims, workflow, admin, telegram
│   │   ├── core/         config, sécurité (JWT, scrypt), permissions, rate limit, stockage, conteneur
│   │   ├── models/       tables SQLAlchemy (users, sessions, audit, liens Telegram)
│   │   ├── schemas/      schémas Pydantic (citations, VLM)
│   │   ├── ingestion/    extraction, OCR, découpage, métadonnées, embeddings, indexation Qdrant
│   │   ├── rag/          retriever hybride, reranker, LLM, garde-fous, citations, chaîne, métriques
│   │   ├── vlm/          client VLM, qualité photo, dommages, factures, figures, fusion RRF
│   │   ├── workflow/     graphe LangGraph, calcul, approbation, cohérence, règles, brouillon
│   │   ├── mcp_server/   serveur FastMCP (3 outils), autorisation, service de sinistres simulé
│   │   ├── mcp_client/   passerelles MCP (HTTP et en processus)
│   │   └── bot/          bot Telegram (aiogram)
│   ├── alembic/ · scripts/ (seed_users.py, demo_e2e.py) · tests/ · Dockerfile
├── frontend/             Next.js (src/app, src/components/ui, src/lib, e2e/)
├── data/                 générateurs, corpus synthétique (40 PDF), manifest, historique simulé
├── training/             jeu d'adaptation, entraînement et évaluation du reranker
├── eval/                 150 scénarios et scripts de mesure
└── docs/                 cadrage, hypothèses, guides, rapports
```

---

## 5. Démarrage rapide (local, sans GPU)

Cet essai utilise des **modèles de substitution** : la qualité des réponses est dégradée, mais toute la chaîne (accès, citations, workflow, approbation) fonctionne.

**Prérequis** : Python 3.11+, Node 20+, Docker (pour Qdrant), Tesseract (`tesseract-ocr`, idéalement `tesseract-ocr-fra`). Sous Windows, utilisez WSL.

### 5.1 Qdrant

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### 5.2 Backend

```bash
cd backend
pip install -e ".[dev]"
python -c "import secrets;print(secrets.token_urlsafe(32))"    # à lancer 3 fois : 3 secrets
```

Créez `backend/.env` (le fichier doit être dans `backend/`) :

```ini
JWT_SECRET=<secret 1>
APPROVAL_SECRET=<secret 2>
BOT_API_KEY=<secret 3>
DEMO_USERS_PASSWORD=MotDePasseDemo2026
EMBEDDER=hash
RERANKER=lexical
RERANK_MIN_SCORE=0.5
LLM_MODE=stub
VLM_MODE=stub
MCP_URL=
```

> `MCP_URL=` (vide) exécute le service de sinistres simulé **dans le même processus**, avec les mêmes contrôles d'autorisation : inutile de lancer le serveur MCP séparément pour l'essai.

Indexation, comptes et lancement :

```bash
python -m app.ingestion.run_ingestion --corpus ../data/corpus --embedder hash --recreate
python scripts/seed_users.py
uvicorn app.main:app --port 8000
```

Documentation interactive : <http://localhost:8000/docs>

### 5.3 Frontend (nouveau terminal)

```bash
cd frontend
npm install --legacy-peer-deps        # ou : pnpm install
cat > .env.local <<'EOT'
AUTH_SECRET=<un 4e secret aléatoire>
FASTAPI_URL=http://localhost:8000
EOT
npm run dev
```

Ouvrez <http://localhost:3000> et connectez-vous (voir [§8](#8-comptes-rôles-et-permissions)).

### 5.4 Démonstration en ligne de commande

API lancée, depuis `backend/` :

```bash
export DEMO_USERS_PASSWORD=MotDePasseDemo2026
python scripts/demo_e2e.py http://localhost:8000
```

---

## 6. Démarrage avec Docker Compose

> ⚠️ Les fichiers Docker sont fournis mais **n'ont pas été exécutés** lors de la construction : attendez-vous à d'éventuels ajustements.

```bash
cp .env.example .env
```

Renseignez les valeurs vides de `.env` : `JWT_SECRET`, `APPROVAL_SECRET`, `BOT_API_KEY`, `DEMO_USERS_PASSWORD`, `POSTGRES_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `AUTH_SECRET` (et `TELEGRAM_BOT_TOKEN` pour le bot). Pour un essai sans modèles, ajoutez `EMBEDDER=hash`, `RERANKER=lexical`, `RERANK_MIN_SCORE=0.5` (l'image backend n'embarque pas les modèles lourds).

```bash
docker compose up --build -d
docker compose run --rm ingest                         # indexe le corpus dans Qdrant
docker compose exec api python scripts/seed_users.py   # crée les comptes de démonstration
```

| Service | URL |
|---|---|
| Interface web | <http://localhost:3000> |
| API (Swagger) | <http://localhost:8000/docs> |
| MLflow | <http://localhost:5000> |
| Console MinIO | <http://localhost:9001> |

Le serveur MCP n'est **volontairement pas publié** sur l'hôte (réseau Compose uniquement).

---

## 7. Utiliser avec les vrais modèles

```bash
pip install -e "backend[ml]"
```

| Besoin | Configuration |
|---|---|
| Embeddings BGE-M3 | `EMBEDDER=bge-m3` puis ré-ingérer avec `--recreate` |
| Reranker multilingue | `RERANKER=cross-encoder`, `RERANKER_MODEL=BAAI/bge-reranker-v2-m3` (ou chemin du modèle adapté) |
| LLM de génération | `LLM_MODE=openai`, `LLM_BASE_URL`, `LLM_MODEL` (Ollama, vLLM, API distante) |
| VLM | `VLM_MODE=openai` avec vLLM : `vllm serve Qwen/Qwen2.5-VL-7B-Instruct` (quantification 4 bits possible) |
| Serveur MCP séparé | définir `MCP_URL=http://localhost:8765/mcp` et lancer `python -m app.mcp_server.server` |

⚠️ **Recalibrez `RERANK_MIN_SCORE`** avec le vrai reranker : il détermine le refus « hors corpus » et sa valeur de test (0.5, reranker lexical) n'est pas transposable.

### Adapter et comparer le reranker

```bash
make dataset                                         # génère et vérifie les 954 exemples (split par document)
python training/reranker/train_reranker.py           # entraînement + suivi MLflow
python training/reranker/evaluate_reranker.py --embedder bge-m3 \
       --initial BAAI/bge-reranker-v2-m3 --adapted training/reranker/artifacts/<version>
```

Compare 3 configurations (sans reranker, initial, adapté) avec nDCG@5 et MRR@10.

---

## 8. Comptes, rôles et permissions

Créés par `python scripts/seed_users.py`, tous avec le mot de passe `DEMO_USERS_PASSWORD` (`MotDePasseDemo2026` si vous avez repris l'exemple).

| Identifiant | Rôle | Documents visibles | Actions |
|---|---|---|---|
| `alice.assure` | `assure` | public | poser des questions |
| `gaspard.gestionnaire` | `gestionnaire` | public + interne | questions, photos/factures, historique, workflow, approbation (≤ 2 500 EUR) |
| `sonia.superviseur` | `superviseur` | public + interne + restreint | tout, dont administration et approbation au-delà du seuil |

Toutes les permissions sont vérifiées **côté serveur** (FastAPI et serveur MCP), jamais dans le frontend ni dans le bot.

---

## 9. Utilisation

### Interface web

1. **Connexion** → tableau de bord (données de démonstration) → ouvrir le dossier **D-42**.
2. **Conversation** : « Quelle est la franchise en cas de bris de pare-chocs ? » → réponse avec puces de citation (article, page). Survolez une puce pour l'extrait exact ; cliquez pour ouvrir le PDF à la bonne page.
3. **Photos** : glissez-déposez ; une photo floue ou trop petite déclenche un message de clarification.
4. **Instruction du dossier** : renseignez contrat (`P-1001`), date, nature, facture (JSON) → *Lancer l'analyse* : cohérence, score de risque indicatif, brouillon avec calcul détaillé.
5. **Approbation** : *Approuver…* affiche le hash du contenu ; saisissez ses 8 premiers caractères pour confirmer.
6. **Ctrl/⌘ + K** : palette de commandes ; bouton lune/soleil : thème clair/sombre.

### Bot Telegram

Liaison : un utilisateur connecté génère un code (`POST /telegram/link-code`), puis dans Telegram : `/start <code>`.

| Commande | Effet |
|---|---|
| `/ask <question>` | Question documentaire sourcée |
| photo + légende `D-42` | Analyse de dégâts |
| photo + légende `facture D-42` | Extraction de facture |
| `/history P-1001` · `/claims P-1001` | Historique / sinistres en cours (via MCP) |
| `/create_request P-1001 D-42 bris_pare_chocs` | Prépare un brouillon |
| `/approve <hash8>` | Approuve (recopier les 8 premiers caractères du hash) |
| `/cancel` | Annule |

Types de dommage : `bris_pare_chocs`, `collision`, `bris_glace`.

---

## 10. Référence de l'API

| Méthode · Chemin | Rôle minimal | Description |
|---|---|---|
| `POST /auth/login` | — | Retourne un JWT (session révocable) |
| `GET /auth/me` | tout | Identité courante |
| `POST /ask` | assuré | Question → `RagAnswer` (réponse, citations, statut) |
| `POST /ask/stream` | assuré | Idem en SSE (`citations`, `token`, `done`) |
| `GET /documents` | assuré | Documents accessibles à votre rôle |
| `GET /documents/{doc_id}/{version}/file` | assuré | PDF ; **404** identique si inexistant ou interdit |
| `POST /claims/{ref}/photos` | gestionnaire | Analyse VLM d'une photo (multipart) |
| `POST /claims/{ref}/invoice` | gestionnaire | Extraction d'une facture |
| `GET /policies/{id}/history` · `/open-claims` | gestionnaire | Via la passerelle MCP |
| `POST /workflow/start` | gestionnaire | Lance l'analyse, s'arrête au brouillon |
| `GET /workflow/{id}` | propriétaire / superviseur | État, brouillon, chronologie |
| `PATCH /workflow/{id}/draft` | gestionnaire | Modifie le résumé (invalide l'ancien hash) |
| `POST /workflow/{id}/decision` | gestionnaire | `approve` (avec `confirm: true` et `draft_hash`), `reject`, `cancel` |
| `GET /admin/users` · `POST /admin/users/{id}/role` | superviseur | Gestion des rôles |
| `GET /admin/sessions` · `POST /admin/sessions/{jti}/revoke` | superviseur | Gestion des sessions |
| `POST /telegram/link-code` · `/link` · `/session` | utilisateur / bot | Liaison Telegram (clé de service) |
| `GET /health` | — | Santé |

Codes notables : `401` non authentifié, `403` action non autorisée, `409` brouillon modifié ou aucune approbation en attente, `422` confirmation manquante, `429` limite de débit.

---

## 11. Configuration (variables d'environnement)

Voir `.env.example`. Les secrets n'ont **aucune valeur par défaut** : l'application refuse de démarrer si un secret requis est absent ou fait moins de 16 caractères.

| Variable | Rôle |
|---|---|
| `JWT_SECRET`, `APPROVAL_SECRET`, `BOT_API_KEY` | Secrets (l'`APPROVAL_SECRET` doit être identique côté API et serveur MCP) |
| `DEMO_USERS_PASSWORD` | Mot de passe des comptes de démo |
| `DATABASE_URL` | PostgreSQL (défaut dev : SQLite local) |
| `QDRANT_URL`, `QDRANT_COLLECTION` | Base vectorielle |
| `EMBEDDER` | `bge-m3` ou `hash` (tests) |
| `RERANKER`, `RERANKER_MODEL`, `RERANK_MIN_SCORE` | `none` / `lexical` / `cross-encoder` ; seuil de refus |
| `LLM_MODE`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | `stub` ou `openai` (API compatible) |
| `VLM_MODE`, `VLM_BASE_URL`, `VLM_API_KEY`, `VLM_MODEL` | `stub` ou `openai` |
| `MCP_URL` | URL du serveur MCP ; **vide** = service simulé en processus |
| `STORAGE_BACKEND`, `MINIO_*` | `local` ou `minio` |
| `RATE_LIMIT_PER_MINUTE` | Limite par utilisateur |
| `TELEGRAM_BOT_TOKEN`, `API_BASE_URL` | Bot |
| `AUTH_SECRET`, `FASTAPI_URL` | **Frontend** (serveur Next.js uniquement, jamais exposés au navigateur) |

---

## 12. Sécurité

- **Filtrage d'accès avant génération** : appliqué dans la requête Qdrant (par `niveau_acces`), avec une vérification de défense en profondeur sur les résultats.
- **Contenus = données** : passages mis en quarantaine s'ils ressemblent à une injection, balises échappées, prompt qui interdit d'obéir au contenu, zones VLM limitées à une liste fermée.
- **Permissions côté serveur** uniquement (FastAPI, serveur MCP).
- **Approbation** : jeton HMAC lié au contenu et à l'approbateur, usage unique, expiration, idempotence.
- **Secrets** en variables d'environnement ; jamais dans le dépôt ni dans les prompts ; mots de passe hachés (scrypt).
- **Session** : cookie httpOnly (Auth.js) ; le jeton FastAPI n'est jamais exposé au navigateur ; le proxy Next.js n'expose qu'une liste blanche de routes.
- **Limitation de débit** par utilisateur ; **audit minimal** (utilisateur, action, horodatage, identifiant de dossier, issue — jamais de contenu).
- **Mesures** (latence, nDCG, MRR, taux de blocage…) = résultats observés, jamais des garanties.

⚠️ La détection d'injection par motifs est **contournable par paraphrase**. Faites réaliser une revue de sécurité indépendante avant tout usage réel.

---

## 13. Tests et évaluation

```bash
cd backend && pytest -q            # 75 tests
cd frontend && npm test            # vitest (4 tests)
cd frontend && npx tsc --noEmit    # typage
cd frontend && npm run e2e         # Playwright (serveur lancé)
ruff check backend eval training
make eval                          # 150 scénarios hors-ligne → eval/results/latest.json
```

### Ce qui a été exécuté pendant la construction

| Élément | Résultat |
|---|---|
| pytest (backend) | **75 passés** |
| Ruff | OK (E501 et quelques règles assouplies dans `pyproject.toml`) |
| vitest · tsc · `next build` | 4 passés · 0 erreur · build OK |
| Jeu d'adaptation | 954 exemples (774 / 90 / 90), sans fuite par document |
| Serveur MCP | exactement 3 outils vérifiés |

### 150 scénarios — résultats **observés** en mode hors-ligne

| Catégorie | Total | Réussis | Ignorés |
|---|---|---|---|
| Documentaire | 40 | 33 | 0 |
| Photos | 30 | 15 | 15 (VLM réel requis) |
| Factures / cohérence | 25 | 25 | 0 |
| Workflow / approbation | 20 | 20 | 0 |
| Contrôle d'accès | 20 | 20 | 0 |
| Injection de prompt | 15 | 15 | 0 |

- **Fuites d'accès observées : 0.** Latence de `/ask` (stub) : médiane ≈ 15 ms, p95 ≈ 24 ms.
- Les **7 échecs documentaires** sont conservés dans le rapport : la recherche dégradée remonte parfois le contrat d'un autre produit quasi identique.
- Ces chiffres valident la **plomberie** (sécurité, workflow, cohérence). Ils **ne mesurent pas** la qualité de BGE-M3, du reranker ou de Qwen2.5-VL, et ne se généralisent pas (données synthétiques, gabarits répétitifs).

Détails : `docs/rapports/L4_5_rapport_evaluation.md` et `docs/rapports/L1_6_tests_documentaires_acces.md`.

---

## 14. État du projet et limites connues

### Non exécuté / non vérifié
- **Modèles réels** (BGE-M3, reranker initial et adapté, Qwen2.5-VL, LLM) : jamais lancés ; aucune métrique réelle. L'entraînement du reranker et la comparaison à 3 configurations sont **écrits mais non exécutés**.
- **Docker Compose**, **Alembic** (l'application utilise `create_all`), **PostgresSaver**, **MinIO**, **Qdrant en mode serveur** : non lancés.
- **Serveur MCP en HTTP réel** : les tests passent par la passerelle en processus (mêmes contrôles). Le format de retour du SDK peut demander un ajustement.
- **Bot Telegram réel**, **Playwright de bout en bout avec backend**.
- **Pas de lockfiles** (`uv`, `pnpm`) : versions indicatives.

### Écarts par rapport au cahier des charges
- La **recherche texte-image** (CLIP + fusion RRF dans `/ask`) n'est pas câblée : `vlm/figures.py` et `vlm/fusion.py` existent, mais `/ask` reste textuel.
- Pas de **téléversement de facture** dans l'interface web (saisie JSON ; l'extraction VLM existe côté API et bot).
- Le **tableau de bord** affiche des données de démonstration ; la page **Évaluation** reprend des chiffres copiés de `make eval` (`frontend/src/lib/eval-data.ts`).
- Le worker pdf.js est chargé depuis cdnjs (connexion internet requise ; à héberger localement en environnement fermé).
- Le texte du panneau de gauche de l'écran de connexion est peu contrasté en mode sombre : utilisez un token de couleur dédié (`--on-brand`) au lieu de `primary-foreground`.
- Les exemples d'adaptation du reranker sont « vérifiés par construction » (vérité terrain issue du manifest) : relisez un échantillon humain (≥ 10 %) avant d'en tirer des conclusions.

### Avant toute mise en production
Générer les lockfiles, HTTPS, rotation des secrets, rate limiting partagé (Redis) si plusieurs workers, `alembic upgrade head` à la place de `create_all`, prise en compte de la révocation de session côté MCP, revue de sécurité indépendante.

---

## 15. Dépannage

| Symptôme | Cause probable / solution |
|---|---|
| `Variable d'environnement … manquante ou trop courte` | Secret de moins de 16 caractères ou `.env` absent de `backend/` |
| Réponses toujours « non trouvée » | Ingestion non lancée, Qdrant arrêté (port 6333), ou `RERANK_MIN_SCORE` trop élevé |
| Connexion impossible | `seed_users.py` non lancé, mauvais mot de passe, ou API non joignable sur le port 8000 |
| Erreur d'authentification côté Next.js | `AUTH_SECRET` absent de `frontend/.env.local` |
| Aperçu PDF vide | Pas d'accès à cdnjs (worker pdf.js) ou document interdit pour votre rôle |
| `ModuleNotFoundError: mcp.server.fastmcp` | Le SDK MCP v2 est installé ; épingler `pip install "mcp<2"` |
| OCR aux accents dégradés | Pack `tesseract-ocr-fra` absent (repli sur l'anglais) |
| `git push` refusé | Voir [§16](#16-documentation-complémentaire) ou créer un token d'accès GitHub |

---

## 16. Documentation complémentaire

| Fichier | Contenu |
|---|---|
| `docs/00_cadrage_architecture.md` | Note de cadrage et architecture (L1.1) |
| `docs/HYPOTHESES.md` | 27 hypothèses documentées |
| `docs/RAPPORT_LIVRAISON.md` | Ce qui est exécuté, ce qui ne l'est pas |
| `docs/guides/INSTALLATION.md` · `UTILISATEUR.md` | Guides d'installation et d'utilisation |
| `docs/rapports/` | Tests documentaires et d'accès, évaluation, comparatif du reranker |
| `data/README.md` · `training/README.md` | Données synthétiques ; adaptation du reranker |

---

*Projet pédagogique à données synthétiques. Les réponses et montants produits sont des aides à la décision, jamais des garanties.*
