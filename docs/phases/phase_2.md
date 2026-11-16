# Phase 2 : multimodalite et fine-tuning (semaines 2 a 3)

## A faire
- `backend/app/vlm/damage_analysis` : analyse de photos, sortie Pydantic `AnalysePhoto` (pieces_touchees,
  type_dommage, gravite, qualite_photo, confiance, zones normalisees pour l'affichage, clarification, citations).
  Si qualite insuffisante ou confiance faible : demande de clarification, jamais de conclusion.
- `backend/app/vlm/invoice_reader` : lecture de facture scannee en sortie structuree (lignes, totaux, TVA,
  immatriculation) + controles automatiques (somme des lignes, TVA, coherence de l'immatriculation).
- Extraction et indexation des figures et schemas (constat amiable, schemas de collision), recherche texte-image
  avec un encodeur multilingue compatible CLIP, fusion texte + image (RRF) puis reranking.
- Donnees photos : script de telechargement documente pour un dataset public (CarDD ou equivalent, licence
  verifiee) + images de demonstration synthetiques.
- Reranker adapte (`training/`) : jeu de 800 a 1 500 exemples verifies (JSONL : requete, passage positif,
  negatifs difficiles, champ `verified`), split train/val/test sans fuite, script de fine-tuning d'un petit
  cross-encoder multilingue, journalise dans MLflow, modele versionne avec model card.
- Script de comparaison de 3 configurations (sans reranker, reranker initial, reranker adapte) avec nDCG@5 et
  MRR@10 ; rapport Markdown genere. Presenter comme "resultats observes sur le jeu de test". Ne jamais inventer
  de chiffres : si le fine-tuning reel n'est pas execute (pas de GPU), le rapport indique "non execute" et le
  script reste reproductible.
- Endpoints `/analyze-photo`, `/read-invoice`. Frontend : page `/claims/new` (depot, apercus, controle qualite)
  et affichage de l'analyse (zones, gravite, confiance, clarification).

## Tests
- Sorties Pydantic valides, clarification declenchee sur photo floue / confiance faible.
- Controles de facture (total faux detecte, TVA incoherente).
- Pas de fuite entre train / val / test.

## Critere de validation
Une photographie donne lieu a une reponse documentaire sourcee ou a une clarification explicite en cas
d'ambiguite.
