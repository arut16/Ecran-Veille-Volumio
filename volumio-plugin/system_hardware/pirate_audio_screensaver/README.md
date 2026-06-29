# Pirate Audio Screensaver - Volumio plugin wrapper

This directory contains the Volumio plugin wrapper for the Python screensaver stored in this repository.

## Purpose

The existing project can still be installed manually through the repository-level `install.sh` script.

This wrapper is intended for Volumio plugin packaging under:

```text
system_hardware/pirate_audio_screensaver
```

## Local test on a Volumio device

From the plugin directory on a Volumio device:

```bash
volumio plugin refresh
volumio vrestart
volumio plugin install
```

Then enable the plugin from the Volumio UI.

## Publication workflow

For official publication, copy this folder into a fork of `volumio/volumio-plugins-sources` at:

```text
system_hardware/pirate_audio_screensaver
```

Commit and push the fork, then run:

```bash
volumio plugin submit
```

## Runtime behavior

- `install.sh` installs system dependencies, the Python package and the systemd service file.
- `onStart()` writes `/etc/volumio-screensaver.env`, enables and starts `volumio-screensaver.service`.
- `onStop()` stops and disables the service.
- `uninstall.sh` removes the service, virtualenv and environment file.
