# Ecran Veille Volumio

Ecran de veille Python pour Volumio sur Raspberry Pi Zero 2 W avec Pimoroni Pirate Audio 1W Amp / Audio 1W HAT.

Pour l'instant il affiche uniquement l'heure au format 24 h sur l'ecran ST7789 240x240. Les deux points clignotent chaque seconde et l'heure change de position aleatoirement toutes les minutes.

## Comportement

- L'ecran de veille s'active apres 5 minutes sans musique (`status` different de `play`).
- Il se masque automatiquement quand la musique demarre depuis l'interface Web Volumio.
- Un appui sur un des 4 boutons du HAT masque l'horloge et relance le delai de 5 minutes.
- Les boutons sont lus en BCM `5,6,16,24` par defaut. Les anciennes cartes Pirate Audio utilisaient parfois `20` pour le bouton Y.

## Installation depuis SSH

Une fois le depot GitHub publie, connecte-toi au Raspberry Pi :

```bash
ssh volumio@volumio.local
```

Puis lance l'installation :

```bash
curl -fsSL https://raw.githubusercontent.com/arut16/Ecran-Veille-Volumio/main/install.sh | bash
```

Le script installe les dependances, copie le service dans `/opt/volumio-screensaver`, cree `/etc/volumio-screensaver.env`, puis active le service `systemd`.

## Configuration

La configuration se trouve ici :

```bash
sudo nano /etc/volumio-screensaver.env
sudo systemctl restart volumio-screensaver
```

Les options utiles :

```bash
VOLUMIO_URL=http://127.0.0.1:3000
IDLE_DELAY_SECONDS=300
BUTTON_PINS=5,6,16,24
FONT_SIZE=58
DISPLAY_ROTATION=90
BLANK_TURNS_BACKLIGHT_OFF=true
```

Si le bouton Y ne reagit pas :

```bash
BUTTON_PINS=5,6,16,20
```

## Commandes de service

```bash
sudo systemctl status volumio-screensaver
sudo journalctl -u volumio-screensaver -f
sudo systemctl restart volumio-screensaver
sudo systemctl disable --now volumio-screensaver
```

## Publier le depot GitHub depuis le PC

Le connecteur GitHub de Codex ne permet pas ici de creer le depot lui-meme, et ce PC n'a pas `git`/`gh` dans le terminal actuel. Apres installation de Git et GitHub CLI sur le PC :

```powershell
cd "C:\Users\arut1\Documents\Ecran Veille Volumio"
git init
git add .
git commit -m "Initial Volumio screensaver"
gh repo create arut16/Ecran-Veille-Volumio --public --source . --remote origin --push
```

Pour un depot prive, remplace `--public` par `--private`. Dans ce cas, l'installation par `curl` public ne fonctionnera pas directement ; clone le depot prive sur le Raspberry puis lance `sudo ./install.sh` depuis le dossier clone.

## References materiel

Pimoroni indique que la gamme Pirate Audio utilise un ecran ST7789 240x240 et 4 boutons actifs bas sur BCM 5, 6, 16 et 24. Les exemples officiels mentionnent aussi l'ancien pin BCM 20 pour certaines cartes.
