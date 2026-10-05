# Pack 📦

Pack is a multi-package-manager frontend for Linux — basically the Bedrock Linux idea, but for package managers.

> DO NOT RUN AS ROOT!!!

## Managers

Pack supports apt, dnf, Flatpak/Flathub, pacman, pip, Nix, and apk.

The host distro manager stays native. Foreign distro ecosystems (apt, dnf, pacman, apk) run in persistent Pack-managed Podman environments, so Fedora/Arch/Alpine/Debian packages don't overwrite the host's `/usr` or package database. Flatpak, Nix, and pip use their normal host ecosystem.

## Install Pack

Clone the repo and run:

```bash
bash installer/install.sh
```

The installer installs Pack and immediately starts `pack setup`.

## Commands

```bash
pack setup
pack sync
pack managers
pack search fastfetch
pack install fastfetch
pack remove fastfetch
pack list
```

During setup, choose managers by number or enter `all`. Pack tries the native package manager first when it needs a dependency, then other usable package managers. Foreign distro managers are provisioned as isolated environments. Setup finishes by syncing every manager that is ready.

`pack install <package>` searches every enabled ecosystem and asks which result to use. Pack syncs that ecosystem immediately before installation and streams the real package manager output.

## Isolation

On a Debian-family host, for example, apt remains native while dnf gets Fedora, pacman gets Arch Linux, and apk gets Alpine environments. Pack installs Podman through the native package manager when isolation is required and Podman is missing.

Pacman synchronization uses a full `pacman -Syu` rather than an unsupported partial-upgrade workflow.

## Adding managers

Manager definitions live in `pack/managers.py`. Runtime isolation lives in `pack/environments.py`, while first-time provisioning/fallback logic lives in `pack/bootstrap.py`.

Pack v0.1 is experimental system software. Test it somewhere disposable before trusting it on an important machine.
