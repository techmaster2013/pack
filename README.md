# Pack 📦

Pack is a package manager frontend for Linux. It's the Bedrock Linux of package managers.

Pack gives multiple package ecosystems one interface while keeping foreign distro package managers isolated from the host system.

## v0.1

Initial package managers:

- apt
- dnf
- Flatpak / Flathub
- pacman
- pip
- Nix
- apk

The installer asks which managers you want Pack to configure. Once setup finishes, Pack immediately syncs every enabled manager.

```bash
sudo pack setup
sudo pack sync
sudo pack managers
sudo pack search fastfetch
sudo pack install fastfetch
```

`sudo pack sync` updates/syncs every enabled package manager.

`sudo pack install <package>` searches every enabled manager, lets you choose a source, syncs that manager, then starts the real underlying package manager so its normal output remains visible.

## Architecture

The host distro's package manager can run natively. Foreign distro package managers are intended to run in Pack-managed isolated environments so they do not overwrite the host distro's system files.

Each ecosystem is implemented as an adapter, making new package managers easy to add later.

## Status

Pack is in very early development. The current code is the v0.1 CLI foundation; isolation/bootstrap support for foreign distro managers is still being built.
