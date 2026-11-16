# Cahier des charges du design frontend

Objectif : une interface professionnelle, moderne et creative, qui inspire confiance (assurance, argent,
decisions) tout en restant elegante et memorable. Elle ne doit PAS ressembler a un template shadcn gris par
defaut ni a un tableau de bord generique.

## Identite visuelle

- Nom : CLAIMiDOC. Logotype simple avec un symbole abstrait (bouclier + page) dessine en SVG inline.
- Themes clair et sombre, bascule manuelle et respect de `prefers-color-scheme`. Mode sombre par defaut : fond
  encre profond (#0B1020), surfaces en couches (#121A2E, #19233D), bordures fines a faible contraste.
- Accent principal : degrade indigo vers cyan (#6366F1 -> #22D3EE), utilise avec parcimonie (actions primaires,
  focus, jauges). Semantique : emeraude (valide), ambre (incertitude, vigilance), rose-rouge (anomalie, blocage).
- Typographie (via next/font) : titres "Space Grotesk" ou "Sora", texte "Inter", chiffres et identifiants en
  "JetBrains Mono". Echelle typographique coherente, chiffres tabulaires pour les montants.
- Tous les tokens (couleurs, rayons, ombres, espacements, durees d'animation) sont des variables CSS centralisees.
  Rayons genereux (12 a 20 px), ombres douces colorees, effet verre leger (backdrop-blur) sur la barre
  superieure et les panneaux flottants, fine texture de grain en arriere-plan.

## Mise en page

- Rail lateral compact repliable (icones + libelles au survol), barre superieure avec recherche et palette de
  commandes (Cmd/Ctrl+K : naviguer, ouvrir un dossier, changer de theme).
- Vue partagee sur l'ecran principal : conversation a gauche, visionneuse de sources a droite (redimensionnable).
- Responsive complet (mobile d'abord pour le chat et l'approbation), navigation basse sur mobile.

## Ecrans

1. `/login` : page d'accueil soignee, illustration SVG abstraite animee (formes fluides), connexion Auth.js,
   selection de role de demonstration en mode demo.
2. `/chat` : conversation en streaming avec indicateur d'ecriture elegant. Citations en puces numerotees [1] :
   au survol, une carte affiche l'extrait, le document, la version, la page et l'article ; au clic, la
   visionneuse react-pdf s'ouvre a la bonne page avec le passage surligne. Etat visuel dedie pour
   "information non trouvee". Suggestions de questions en cartes.
3. `/claims/new` : zone de depot glisser-deposer (photos, facture PDF, numero de contrat), apercus avec controle
   qualite immediat (net/flou), barre de progression.
4. `/claims/[id]` : tableau de bord de dossier. Frise du workflow LangGraph en direct (etapes qui s'allument via
   SSE). Photo avec calques de zones detectees, badge de gravite, jauge de confiance. Facture extraite sous forme
   de tableau editable avec anomalies surlignees. Panneau "Contrat" avec les clauses citees.
5. `/claims/[id]/approval` : ecran d'approbation de type "document". Brouillon lisible, jauge de risque, liste
   d'anomalies avec preuves, empreinte du brouillon (hash court en police mono), montant calcule et son detail
   (facture - franchise, plafond). Bouton d'approbation a MAINTIEN de 1 seconde (anneau de progression), bouton
   Refuser, bouton Annuler. Si le brouillon change : banniere "Le contenu a change, re-approbation necessaire" et
   bouton desactive.
6. `/dashboard` et `/admin` : cartes de metriques (latence, qualite des citations, securite), graphiques Recharts
   sobres, tableau des scenarios d'evaluation filtrable, bandeau permanent "Resultats observes sur le jeu de
   test, pas des garanties".

## Mouvement et interactions

- Framer Motion : transitions de page douces, apparition en cascade des cartes, ressorts discrets, effet de
  brillance sur les etats de chargement. Squelettes de chargement partout (aucun ecran blanc). Respecter
  `prefers-reduced-motion`.
- Retours immediats : toasts, etats vides illustres (SVG inline), micro-interactions sur boutons et puces.

## Qualite

- Accessibilite WCAG AA : contrastes, focus visibles, navigation clavier complete, roles ARIA, libelles d'images.
- Aucune autorisation decidee cote client : le bouton d'approbation appelle FastAPI avec le hash du brouillon
  affiche ; une action non autorisee affiche l'erreur 403 renvoyee par le serveur.
- Composants reutilisables et documentes. Tests Vitest sur les composants cles et Playwright sur les parcours :
  connexion -> question avec citation -> dossier -> approbation, et parcours de refus d'acces.
- Aucun secret dans le navigateur ; appels a l'API via des route handlers Next.js (cookie httpOnly).
