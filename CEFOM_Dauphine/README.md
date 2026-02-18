# Scripts de collecte (Codex)

Ce dossier regroupe les scripts pour récupérer des données depuis différents sites, + les scripts et vidéos de demo Browser Use.

## Organisation

```
CEFOM_Dauphine/
|-- README.md
|-- scripts/
`-- browser_use/
    |-- scripts/
    `-- videos/
```

## Scripts de collecte (dossier "scripts/")

### 1) quotes_to_df.py
But : Recuperer les quotes du site "Quotes to Scrape (JS)" via l'API JSON et afficher un DataFrame.

Execution (WSL) :
```bash
/home/olivier/.venvs/quotes/bin/python /home/olivier/quotes_to_df.py
```

Filtre tag (optionnel) :
```bash
/home/olivier/.venvs/quotes/bin/python /home/olivier/quotes_to_df.py life
```

---

### 2) trustpilot_carrefour_df.py
But : Recuperer des avis Trustpilot FR (Carrefour) via HTML (sans API dediee) et afficher un DataFrame.

Execution (WSL) :
```bash
/home/olivier/.venvs/quotes/bin/python /home/olivier/trustpilot_carrefour_df.py --pages 2
```

Note : La pagination est reelle et les avis sont extraits des pages HTML (pas besoin d'API ici).

---

### 3) instagram_first_non_pinned.py
But : Trouver le 1er post non epingle d'un profil public Instagram, et lister ses medias.

Execution (WSL) :
```bash
/home/olivier/.venvs/quotes/bin/python /home/olivier/instagram_first_non_pinned.py fast_train_driver
```

---

### 4) instagram_first_three_non_pinned.py
But : Recuperer les 3 premiers posts non epingles, telecharger medias + exporter commentaires (si login). Les fichiers sont organises dans un dossier ~/fast_train_driver/.

Execution (WSL) :
```bash
/home/olivier/.venvs/quotes/bin/python /home/olivier/instagram_first_three_non_pinned.py fast_train_driver --limit 3 --max-comments 50
```

Commentaires :
Pour acceder aux commentaires, il faut une session Instaloader :
```bash
/home/olivier/.venvs/quotes/bin/instaloader --login fast_train_driver
/home/olivier/.venvs/quotes/bin/python /home/olivier/instagram_first_three_non_pinned.py fast_train_driver --limit 3 --login-user fast_train_driver
```

---

## Demos Browser Use (dossier "browser_use/")

Les scripts ci-dessous proviennent du repo python_experiments/browser_use et ont ete copies ici pour presentation / archivage.

### Scripts (browser_use/scripts/)
- simple_browser_use_demo.py : demo sur books.toscrape.com (page 41), extraction du meilleur rating via evaluate JS.
- amazon_best_seller_demo.py : ouvre la page Amazon Best Sellers (Books), trouve le rang #1, ouvre la fiche produit (headless).
- amazon_best_seller_visible.py : version visible (fenetre Chrome) de la demo Amazon.
- run_amazon_best_seller_demo.sh : lance un Chrome headless en CDP puis execute amazon_best_seller_demo.py.

### Videos (browser_use/videos/)
Fichiers .mp4 enregistres automatiquement pendant l'execution des demos Browser Use.

Note importante :
Ces scripts s'appuient sur l'environnement python_experiments/browser_use (fichier .env avec OPENAI_API_KEY, dependances, Chromium, etc.).
Si tu veux les executer depuis ce dossier, il faudra adapter les chemins et/ou recreer un environnement equivalent.

---

## Dependances (WSL)

### Pour les scripts de collecte
Venv utilise :
```
/home/olivier/.venvs/quotes
```
Packages installes :
- requests
- pandas
- beautifulsoup4
- lxml
- instaloader

### Pour les demos Browser Use
Packages typiques :
- browser_use
- python-dotenv
- openai (via ChatOpenAI)

