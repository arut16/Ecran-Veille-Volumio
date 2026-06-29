# Publication du screensaver dans le gestionnaire de plugins Volumio

Ce dépôt contient historiquement le projet Python installable manuellement par SSH.

Une couche plugin Volumio a été ajoutée dans :

```text
volumio-plugin/system_hardware/pirate_audio_screensaver
```

## Pourquoi ce dossier séparé ?

Le script `install.sh` à la racine du dépôt est conservé pour ne pas casser l'installation manuelle existante :

```bash
curl -fsSL https://raw.githubusercontent.com/arut16/Ecran-Veille-Volumio/main/install.sh | sudo bash
```

Le dossier `volumio-plugin/system_hardware/pirate_audio_screensaver` contient, lui, la structure attendue pour un plugin Volumio.

## Fichiers ajoutés

```text
package.json
index.js
config.json
UIConfig.json
install.sh
uninstall.sh
i18n/strings_en.json
i18n/strings_fr.json
README.md
```

## Cycle de vie du plugin

- `install.sh` installe les dépendances système, le package Python et le fichier systemd.
- `index.js` écrit `/etc/volumio-screensaver.env` à partir des réglages de l'interface Volumio.
- `onStart()` active et démarre `volumio-screensaver.service`.
- `onStop()` arrête et désactive `volumio-screensaver.service`.
- `uninstall.sh` supprime le service, l'environnement virtuel et le fichier de configuration.

## Test local sur Volumio

Sur le Raspberry Pi Volumio :

```bash
cd /home/volumio
mkdir -p plugin-test/system_hardware
cp -r /chemin/du/depot/volumio-plugin/system_hardware/pirate_audio_screensaver plugin-test/system_hardware/
cd plugin-test/system_hardware/pirate_audio_screensaver
volumio plugin refresh
volumio vrestart
volumio plugin install
```

Ensuite, activer le plugin depuis l'interface Volumio.

## Publication officielle

La publication officielle passe normalement par un fork de :

```text
volumio/volumio-plugins-sources
```

Copier le dossier :

```text
volumio-plugin/system_hardware/pirate_audio_screensaver
```

vers :

```text
system_hardware/pirate_audio_screensaver
```

Puis, depuis ce dossier dans le fork :

```bash
volumio plugin submit
```

## Point d'attention

Cette première couche est volontairement non destructive. Elle ne remplace pas encore l'installation manuelle historique. Après validation sur un vrai appareil Volumio, il sera possible de déplacer définitivement le plugin vers un fork `volumio-plugins-sources` pour soumission au store.
