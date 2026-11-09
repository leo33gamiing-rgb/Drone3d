# Sources du catalogue

Régénérer les PDF après une modification des données (`build.py`) ou du style (`style.css`) :

```bash
python3 build.py
node topdf.js "$PWD" catalog fiche_m400 fiche_m4t fiche_mini
```

`topdf.js` a besoin de Playwright (Chromium). Les photos dans `img/` sont des visuels officiels DJI.
