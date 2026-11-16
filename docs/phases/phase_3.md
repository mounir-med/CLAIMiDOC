# Phase 3 : orchestration agentique et MCP (semaine 4)

## A faire
- Graphe LangGraph : reception -> validation_entrees -> analyse (RAG + VLM + facture en parallele) ->
  verification_coherence -> preparation_brouillon -> INTERRUPT approbation_humaine -> creation_demande ->
  cloture. Branches refus et annulation -> cloture. Checkpointer PostgreSQL. Diagramme Mermaid dans `docs/`.
- Serveur MCP (`mcp_server/`, FastMCP) simulant le service de sinistres, avec exactement ces outils :
  `get_claim_history(policy_id)`, `get_open_claims(policy_id)`,
  `create_reimbursement_request(policy_id, title, description, approval_token)`.
  Controles d'autorisation, verification du jeton, idempotence et rate limiting cote serveur.
- Client MCP (`backend/app/mcp_client`) integre au workflow.
- Agent de coherence : photos vs facture, prix vs table de reference, contrat vs sinistre, doublons via
  `get_open_claims`, hash des photos reutilisees. Produit un score de risque et une liste d'anomalies.
- Calcul de remboursement deterministe : min(montant_eligible - franchise, plafond).
- Brouillon de demande : resume, montants, franchise/plafond/exclusions avec citations, anomalies, niveau
  d'incertitude, recommandation (jamais une decision).
- Approbation : `approval_token` HMAC lie au contenu exact et a l'utilisateur, usage unique, expiration,
  idempotence (voir contraintes dans AGENTS.md).
- Endpoints : `/claims` (creer, lire), `/claims/{id}/draft`, `/claims/{id}/approve`, `/claims/{id}/reject`,
  `/claims/{id}/cancel`, flux d'etat du workflow en SSE.
- Frontend : `/claims/[id]` (frise du workflow en direct, photo avec zones, facture editable, panneau contrat) et
  `/claims/[id]/approval` (maintien 1 s, hash, banniere de changement de contenu) selon `docs/DESIGN.md`.

## Tests
- Le workflow s'interrompt et ne cree rien sans approbation.
- Jeton : brouillon modifie, jeton expire, rejeu, utilisateur different, doublon (idempotence).
- Le serveur MCP refuse un appel sans autorisation ou sans jeton valide.
- Demonstration de bout en bout scriptee (L3.6).

## Critere de validation
L'assistant consulte l'historique, propose une demande et ne la cree qu'apres approbation explicite.
