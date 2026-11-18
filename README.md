# Site institutionnel SGCI — sgci-niger.com

Vitrine institutionnelle trilingue (FR / EN / AR) de SGCI SARLU (Société Générale de Commerce et de l'Industrie).
Adresse canonique : https://www.sgci-niger.com (l'adresse sans `www` y redirige).

## Fichiers

- `src/index.html` — **source** de la page d'accueil (balisage + dictionnaire de traduction `I18N`). C'est le seul fichier à modifier pour l'accueil.
- `content/articles/*.json` — articles d'actualité. `"status": "published"` les met en ligne, `"draft"` les garde hors ligne.
- `media/` — photos des articles. `assets/pages.css` — styles des pages intérieures.
- `scripts/build_site.py` — génère `index.html` (/), `en/index.html` (/en), `ar/index.html` (/ar), les pages d'articles
  (`actualites/…`, `en/news/…`), `mentions-legales.html`, `en/legal-notice.html`, `404.html` et `sitemap.xml`.
- `api/contact.js` — inscription aux alertes (nécessite `RESEND_API_KEY` dans Vercel ; sans clé, le site ouvre la messagerie du visiteur).
- `vercel.json` — adresses propres, redirections, en-têtes de sécurité.

## Publier un article

1. Ajouter les photos dans `media/actualites/<dossier>/`.
2. Créer `content/articles/<nom>.json` à partir de `content/articles/MODELE.txt`, avec `"status": "published"`.
3. Lancer `python3 scripts/build_site.py`, puis valider et pousser sur `main`.

La rubrique « Actualités » et son entrée de menu n'apparaissent que s'il existe au moins un article publié.
Aperçu avec les brouillons : `python3 scripts/build_site.py --drafts` (ne pas pousser ce résultat sur `main`).

## Contact
contact@sgci-niger.com · +227 90 50 53 50
