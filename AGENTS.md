# AGENTS.md : CLAIMiDOC

Tu es un ingenieur senior full-stack IA. Ce depot contient le projet "CLAIMiDOC" : un assistant documentaire
multimodal et agentique pour le traitement des sinistres automobiles. Le code est genere PHASE PAR PHASE.

## Comment travailler (regles de session)

- Quand l'utilisateur dit "Execute la Phase N", lis `docs/phases/phase_N.md`, `docs/DESIGN.md` si la phase touche
  au frontend, puis execute UNIQUEMENT cette phase. Ne commence jamais la phase suivante.
- Ne pose pas de questions. Si un choix manque, prends une valeur par defaut raisonnable et note-la dans
  `docs/DECISIONS.md`.
- A la fin de chaque phase : lance les tests, corrige tout echec, mets a jour `PROGRESS.md`, fais un commit Git
  clair (`feat(phase-N): ...`), puis resume en 10 lignes maximum : ce qui est fait, ce qui reste, comment tester.
- Si une phase est trop grosse pour une seule passe, termine un sous-ensemble coherent, commit, et indique
  precisement ce qui reste dans `PROGRESS.md`.
- Langue : code, commentaires techniques et noms en anglais. Interface utilisateur, README et documentation en
  francais.
- N'invente jamais de resultats de mesure. Les metriques sont des "objectifs" ou des "resultats observes",
  jamais des garanties.

## Contexte et objectif

Le gestionnaire (ou l'assure) envoie des photos de degats, une facture de garage (PDF scanne) et un numero de
contrat. Le systeme :
- analyse les photos avec un VLM,
- lit la facture,
- retrouve dans le contrat la franchise, le plafond et les exclusions avec citation exacte (document, page,
  article),
- verifie la coherence photos / facture / contrat,
- prepare un BROUILLON de demande de remboursement,
- attend une APPROBATION HUMAINE EXPLICITE avant de creer la demande via un serveur MCP.

Le systeme ne paie rien reellement, ne garantit aucun diagnostic ni aucun montant, et ne remplace pas un
gestionnaire habilite.

## Contraintes non negociables

1. Citations verifiables : chaque affirmation tiree du contrat porte doc_id, version, page, article, extrait.
   Sans source : reponse "information non trouvee". Aucune invention.
2. Filtrage par autorisations : chaque passage a un niveau d'acces (client, gestionnaire, superviseur). Le filtre
   est applique dans la requete Qdrant, avant toute generation.
3. Approbation humaine obligatoire avant `create_reimbursement_request`. Le workflow LangGraph s'interrompt
   (interrupt + checkpoint PostgreSQL) jusqu'a une action explicite.
4. `approval_token` = HMAC-SHA256(secret, user_id + sha256(JSON canonique du brouillon) + nonce + expiration).
   Usage unique, duree limitee, stocke en base. Toute modification du brouillon invalide le jeton. Le serveur MCP
   verifie lui-meme le jeton, le role de l'utilisateur et l'idempotence (cle = sha256(policy_id + hash du
   brouillon)) : un rejeu ne cree pas de doublon.
5. Autorisations verifiees COTE SERVEUR (FastAPI et MCP), jamais dans le bot ni dans le frontend.
6. Le calcul du remboursement est du code deterministe : min(montant_eligible - franchise, plafond), jamais le LLM.
7. Entrees documentaires non fiables : le contenu des PDF, images et factures est traite comme DONNEE, jamais
   comme instruction (delimiteurs explicites, consigne systeme, sorties validees par Pydantic, outils en liste
   blanche, droits minimaux).
8. Secrets uniquement via variables d'environnement (`.env.example` fourni, aucun secret dans Git). Rate limiting
   par utilisateur sur FastAPI et sur le serveur MCP.
9. Journalisation minimale (audit) : user_id, action, horodatage, identifiants de dossier. Aucun contenu sensible
   dans les logs.
10. Metriques presentees comme "objectifs" ou "resultats observes", jamais comme garanties, dans les rapports
    et dans l'UI.
11. Donnees exclusivement synthetiques ou publiques. Aucune donnee personnelle reelle.

## Stack

- Backend : Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy + Alembic, PostgreSQL, uv ou poetry.
- RAG : PyMuPDF, OCR local (PaddleOCR ou Tesseract), LangChain, embeddings BGE-M3, Qdrant, recherche hybride
  (dense + BM25) avec fusion RRF, reranker.
- Multimodal : VLM a poids ouverts Qwen2.5-VL-7B-Instruct via un endpoint compatible OpenAI (vLLM ou Ollama),
  encodeur multilingue compatible CLIP pour la recherche texte-image.
- Agentique : LangGraph (checkpointer PostgreSQL), SDK Python MCP (FastMCP) pour le serveur ET le client.
- Fichiers : MinIO. Suivi d'experiences : MLflow.
- Bot : Telegram avec aiogram.
- Frontend : Next.js (App Router), TypeScript strict, Tailwind CSS, shadcn/ui personnalise, Framer Motion,
  TanStack Query, Zod, react-pdf, Recharts, Auth.js.
- Infra : Docker Compose pour tous les services (api, mcp, bot, frontend, postgres, qdrant, minio, mlflow).
  Dependances epinglees.
- Tests : pytest, Vitest, Playwright.

## Mode sans GPU (obligatoire)

Tout doit tourner sans GPU ni cle API pour les tests et la demo. Fournis `LLM_PROVIDER`, `VLM_PROVIDER`,
`EMBEDDING_PROVIDER` avec les valeurs `mock` (reponses deterministes) et `openai_compatible` (vrai modele via
URL). Les tests CI utilisent `mock`. Documente comment brancher Qwen2.5-VL, BGE-M3 et un LLM reels.

## Structure du depot

```
claimidoc/
  README.md, AGENTS.md, PROGRESS.md, Makefile, docker-compose.yml, .env.example
  docs/ (DECISIONS.md, DESIGN.md, architecture.md, guide_installation.md, guide_utilisateur.md,
         note_de_cadrage.md, rapport_evaluation.md, demo_script.md, CHECKLIST.md, phases/)
  backend/app/ (api, core, ingestion, rag, vlm, schemas, workflow, mcp_client, db)
  mcp_server/   bot/   frontend/   training/   eval/   data/   prompts/   tests/
```

## Definition of done (toutes phases)

- Les tests de la phase passent (`make test`).
- Aucun secret dans le depot. Le projet demarre avec `make up` en mode `mock`.
- `PROGRESS.md` et `docs/DECISIONS.md` sont a jour. Un commit par phase.

## Livrables finaux (a verifier en Phase 4)

L1.1 a L4.7 de la feuille de route : note de cadrage, pipeline d'ingestion, index Qdrant, API et chaine RAG,
interface, rapport de tests, module VLM, RAG multimodal, jeu d'adaptation, reranker versionne, rapport
comparatif, application V2, workflow LangGraph documente, serveur et client MCP, brouillons, validation humaine,
demonstration de bout en bout, bot, backend avec identites, Docker Compose, tests de securite, rapport
d'evaluation, documentation, scenario de demonstration (`docs/demo_script.md`).
A la fin, produis `docs/CHECKLIST.md` listant chaque livrable et chaque contrainte avec son etat (fait / partiel)
et l'emplacement du code ou du test correspondant.
