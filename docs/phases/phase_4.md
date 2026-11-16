# Phase 4 : bot, securite, deploiement, evaluation (semaines 5 a 6)

## A faire
- Bot Telegram (`bot/`, aiogram) relie a FastAPI : `/start`, `/ask`, `/analyze`, `/history`, `/claims`,
  `/create_request`, `/approve`, `/cancel`. Liaison compte Telegram <-> identite applicative par code a usage
  unique genere dans le frontend. Permissions verifiees cote serveur. `/approve` affiche le contenu exact et son
  empreinte avant validation.
- Docker Compose complet (api, mcp, bot, frontend, postgres, qdrant, minio, mlflow), guide d'installation,
  versions epinglees des dependances, des prompts (`prompts/` versionne) et des modeles.
- Tests automatises : integration, injection de prompt (PDF et image contenant des instructions cachees),
  controle d'acces, approbation (brouillon modifie, jeton expire, rejeu, utilisateur different, doublon).
- Evaluation d'environ 150 scenarios (`eval/scenarios/*.yaml`) : 40 questions documentaires, 30 photos,
  25 factures et coherence, 20 workflow et approbation, 20 controle d'acces, 15 injection de prompt. Le runner
  mesure latence (mediane et p95), qualite des citations, taux de blocage des actions non autorisees, ressources,
  et genere `docs/rapport_evaluation.md` avec une section "limites" honnete. Aucun chiffre invente.
- Frontend : `/dashboard` et `/admin` (metriques, graphiques Recharts, tableau des scenarios filtrable, bandeau
  "Resultats observes, pas des garanties"), page de liaison Telegram.
- Documentation : `docs/guide_utilisateur.md`, `docs/guide_installation.md`, `docs/demo_script.md` (scenario de
  soutenance), README avec demarrage en moins de 10 minutes.
- `docs/CHECKLIST.md` : chaque livrable L1.1 a L4.7 et chaque contrainte avec son etat et l'emplacement du code
  ou du test.

## Critere de validation
Depuis Telegram, un gestionnaire envoie une photo, recoit une reponse sourcee, consulte un historique et
approuve une demande ; les actions non autorisees sont bloquees. `make test` passe en mode `mock`.
