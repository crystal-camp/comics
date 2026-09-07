CRYSTAL LAKE COMICS — V5
========================

TEST LOCAL (sans GitHub)
------------------------
Option simple :
1. Ouvrir une invite de commandes dans ce dossier.
2. Taper : py build_library.py
3. Taper : py -m http.server 8000
4. Ouvrir : http://127.0.0.1:8000/

Option alternative :
- Double-cliquer SERVE_LOCAL.py si Windows/Python l'autorise.
- Il reconstruit library.json puis ouvre le site.

AJOUTER UN COMIC
----------------
Créer un dossier :
comics/nom-du-comic/

Exemple :
comics/hollow-road/
  cover.png
  001.png
  002.png
  003.png
  comic.json

Puis relancer :
py build_library.py

comic.json (exemple)
--------------------
{
  "title": "Hollow Road",
  "description": "Après la tempête, plusieurs campeurs s'aventurent au-delà des limites de Crystal Lake.",
  "date": "2026-08-13",
  "cover": "cover.png",
  "theme": "forest"
}

Thèmes disponibles :
- lake (défaut)
- forest
- night
- paper
- blood

Optionnel :
"backCover": "back.png"
Si backCover n'est PAS défini, la BD peut se terminer naturellement sur une double-page.

QUALITÉ
-------
Les pages principales sont chargées directement depuis les fichiers image source.
Le script Python ne convertit, ne redimensionne et ne recomprime aucune image.
Formats détectés : JPG, JPEG, PNG, WEBP, GIF, AVIF, SVG.
Format de page recommandé : 1024 x 1536 px.

RACCOURCIS LECTEUR
------------------
← / → : précédent / suivant
Molette : zoom centré sous la souris
+ / - : zoom
0 : Adapter
F : plein écran
Esc : fermer les panneaux
Double-clic : focus 200 % / retour

MODES
-----
Souple : page-turn plus lent et ample
Papier : page-turn naturel standard
Rigide : aucun effet de feuille, changement direct de spread

GITHUB / DISCORD
----------------
Après configuration de site.config.json avec l'URL publique, build_library.py génère pour chaque comic une page /comics/slug/index.html avec les métadonnées Open Graph (titre, résumé, couverture) utilisées par Discord pour les embeds.
