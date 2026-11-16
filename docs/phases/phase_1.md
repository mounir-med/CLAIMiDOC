# Phase 1 : socle documentaire et RAG textuel (semaine 1)

## A faire
- Generateur de donnees (`data/`) : 30 a 50 documents PDF synthetiques en francais couvrant deux familles de
  contrats, `tous_risques` et `au_tiers` (conditions generales, avenants, baremes de franchise, exclusions).
  Chaque document a doc_id, version, niveau d'acces. Les marquer clairement comme synthetiques.
- Pipeline d'ingestion (`backend/app/ingestion`) : PyMuPDF, OCR local si PDF scanne, decoupage par article et par
  page, metadonnees (doc_id, version, page, article, famille, niveau_acces, hash_contenu), embeddings BGE-M3
  (ou mock), indexation Qdrant.
- Chaine RAG (`backend/app/rag`) : recherche hybride dense + BM25 avec fusion RRF, filtre d'acces applique dans
  Qdrant, reponse en sortie structuree Pydantic avec citations, "information non trouvee" si aucune source.
- Endpoints FastAPI : `/ask` (streaming SSE), `/documents/{id}/pages/{n}`.
- Frontend : page `/chat` complete selon `docs/DESIGN.md` (citations survolables, visionneuse react-pdf a la bonne
  page, etat "information non trouvee", suggestions).
- Docs : `docs/note_de_cadrage.md` (L1.1) et `docs/architecture.md`.

## Tests (rapport L1.6)
- Exactitude des citations (document, page, article).
- Un utilisateur sans droit ne recoit jamais un passage restreint.
- Question hors corpus : refus "information non trouvee".
- Tests de non-regression de l'ingestion (nombre de passages, metadonnees).

## Critere de validation
Une question technique produit une reponse fondee sur des passages accessibles, avec references verifiables aux
documents et aux pages.
