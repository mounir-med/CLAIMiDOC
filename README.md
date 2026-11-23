# CLAIMiDOC

Assistant documentaire multimodal et agentique pour gestionnaires de sinistres automobiles.
Contrats PDF + photos de dégâts → réponses **sourcées** (document, page, article), historique via **MCP**,
demandes de remboursement **soumises à validation humaine explicite**.

> **Toutes les données sont synthétiques** (contrats, factures, historiques, photos de test). Aucune donnée personnelle réelle.
> Le système ne paie jamais seul, ne remplace pas un gestionnaire habilité et ne garantit aucun diagnostic ni montant : ses sorties sont des **aides à la décision**.

## État du projet (honnête)

Voir `docs/RAPPORT_LIVRAISON.md` : ce qui a été exécuté ici (tests Python hors-ligne) et ce qui reste à valider
sur votre machine (modèles BGE-M3 / Qwen2.5-VL, entraînement du reranker, Docker Compose, tests Playwright).

## Démarrage rapide (développement, sans GPU)

```bash
cp .env.example .env            # puis renseigner les secrets (JWT_SECRET, APPROVAL_SECRET, ...)
make install                    # dépendances backend + frontend
make corpus                     # (re)génère le corpus synthétique (déjà fourni dans data/corpus)
make up-infra                   # Qdrant, PostgreSQL, MinIO
make ingest                     # indexe le corpus (EMBEDDER=hash pour un essai rapide, bge-m3 pour le réel)
make api                        # FastAPI sur :8000
make web                        # Next.js sur :3000
make test                       # pytest (+ vitest)
```

Stack complète : `docker compose up --build` (voir `docs/guides/INSTALLATION.md`).
Documentation : `docs/00_cadrage_architecture.md`, `docs/HYPOTHESES.md`, `docs/guides/`.
