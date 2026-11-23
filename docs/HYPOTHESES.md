# Hypothèses (H1–H18 validées à la conception + ajouts d'implémentation)

H1 Langue : contenus et UI en français ; code en anglais. · H2 Corpus généré par script (reportlab), 40 PDF dont 6 scans rastérisés, marqués « DOCUMENT SYNTHÉTIQUE ».
H3 OCR par défaut Tesseract (`fra+eng`, repli `eng` si le pack français est absent — c'est le cas dans l'environnement de test : accents dégradés). H4 Pas de GPU requis pour développer ; VLM via API compatible OpenAI sinon.
H5 LLM de génération : API compatible OpenAI configurable ; **mode stub extractif** pour les tests. H6 Hybride = dense + sparse BGE-M3 (fusion RRF Qdrant). H7 Reranker initial `BAAI/bge-reranker-v2-m3` ; adaptation d'un modèle plus léger (`mmarco-mMiniLMv2`).
H8 Rôles : assure→public ; gestionnaire→public+interne ; superviseur→tous. H9 JWT HS256 émis par FastAPI + Auth.js (Credentials, cookie httpOnly). H10 Seule la version `is_current` est indexée pour les réponses.
H11 `article=null` si aucun article identifiable. H12 Citations invalides supprimées ; plus aucune source ⇒ « non trouvé ». H13 Seuil de refus hors corpus = seuil sur le score de reranking (**à recalibrer** avec le vrai reranker ; 0.5 en test lexical).
H14 Rate limiting en mémoire (un seul worker). H15 Accent indigo, secondaire teal ; Geist/Geist Mono. H16 Dépendances versionnées dans `pyproject.toml`/`package.json` (lockfiles à générer). H17 Montants en `Decimal`, EUR TTC. H18 Métriques = résultats observés.

## Ajouts faits pendant l'implémentation
H19 Remboursement borné à 0 (un montant négatif n'a pas de sens métier). H20 « Montant éligible » = total TTC de la facture (les lignes non justifiées par les photos sont signalées, pas retranchées). H21 Seuil d'escalade = 2 500 EUR (issu du guide interne synthétique) : au-delà, approbation réservée au superviseur.
H22 Le serveur MCP ne consulte pas la table de sessions de l'API (révocation non vue) ; JWT à durée courte. H23 Les zones de dommages utilisées par le workflow proviennent de l'analyse photo **mémorisée côté serveur**, jamais d'un champ client.
H24 Les jetons d'approbation sont émis par l'API au moment de l'approbation humaine (hash relu côté serveur) ; en production, les clés `APPROVAL_SECRET` du backend et du serveur MCP doivent être identiques.
H25 Jeu d'adaptation : requêtes générées par gabarits, vérité terrain issue du manifest (**vérifié par construction + contrôles automatiques**, pas par relecture humaine : relire ≥10 % avant d'en tirer des conclusions). H26 Tableau de bord frontend : données de démonstration (aucun endpoint d'agrégation).
H27 Liaison Telegram : code à usage unique généré dans l'application ; le bot s'authentifie par clé de service et obtient un JWT court de l'utilisateur lié.
