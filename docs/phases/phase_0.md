# Phase 0 : fondations et design system

## A faire
- Structure du depot complete (voir AGENTS.md), `Makefile` (`make up`, `make down`, `make test`, `make seed`,
  `make eval`), `docker-compose.yml` de base (postgres, qdrant, minio, mlflow, api, frontend), `.env` depuis
  `.env.example`.
- Backend FastAPI : config (pydantic-settings), healthcheck, logging d'audit minimal, rate limiting par
  utilisateur, authentification JWT avec roles (client, gestionnaire, superviseur), fournisseurs `mock` pour
  LLM / VLM / embeddings (interface commune + implementation mock deterministe).
- Modele de donnees SQLAlchemy + migrations Alembic : users, roles, claims, drafts, approvals, audit_log,
  idempotency_keys. Script `make seed` : 3 utilisateurs de demonstration (un par role).
- Frontend : initialiser Next.js (App Router, TypeScript strict, Tailwind, shadcn/ui, Framer Motion, TanStack
  Query, Zod, Auth.js). Creer le DESIGN SYSTEM complet selon `docs/DESIGN.md` : tokens CSS, themes clair/sombre,
  polices, composants de base personnalises (Button, Card, Badge, Input, Tabs, Toast, Skeleton, Dialog, Gauge,
  CommandPalette, AppShell avec rail lateral), page `/design` listant tous les composants.
- Pages `/login` (complete, avec l'illustration animee) et coquille de l'application.

## Tests
- Auth : connexion, roles, acces refuse (403) sans le bon role.
- Rate limiting. Migrations appliquees sur base vide.
- Vitest sur les composants de base, build Next.js sans erreur.

## Critere de validation
`make up` demarre les services en mode `mock`, on se connecte avec un utilisateur de demo, la page `/design`
montre le design system dans les deux themes.
