# CLAIMiDOC

Assistant documentaire multimodal et agentique pour le traitement des sinistres automobiles
(RAG + VLM + agents LangGraph + MCP + validation humaine).

Ce depot contient le cahier des charges complet pour Codex. Le code est genere phase par phase.

## Demarrage

1. Extraire le zip et ouvrir le dossier `claimidoc/` dans Codex (ou lancer Codex a la racine).
2. Initialiser Git : `git init && git add . && git commit -m "chore: scaffold"`.
3. Ouvrir `PROMPTS.md` et copier-coller les commandes, une phase a la fois.
4. Verifier les tests et le diff entre chaque phase avant de passer a la suivante.

## Fichiers cles

- `AGENTS.md` : instructions permanentes lues automatiquement par Codex.
- `docs/phases/phase_N.md` : detail de chaque phase.
- `docs/DESIGN.md` : cahier des charges du frontend.
- `PROGRESS.md` : suivi d'avancement.
- `.env.example` : variables d'environnement (a copier en `.env`).
