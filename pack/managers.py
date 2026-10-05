from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Manager:
    name: str
    binary: str
    search_cmd: tuple[str, ...]
    sync_cmd: tuple[str, ...]
    install_cmd: tuple[str, ...]
    native_distros: tuple[str, ...] = ()

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def search(self, package: str) -> bool:
        if not self.available():
            return False
        result = subprocess.run(
            [*self.search_cmd, package],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.returncode == 0 and bool(result.stdout.strip())

    def sync(self) -> int:
        return subprocess.call(list(self.sync_cmd))

    def install(self, package: str) -> int:
        return subprocess.call([*self.install_cmd, package])


MANAGERS: dict[str, Manager] = {
    "apt": Manager(
        "apt", "apt", ("apt-cache", "search", "--names-only"), ("apt", "update"), ("apt", "install"),
        ("debian", "ubuntu", "linuxmint", "pop", "zorin"),
    ),
    "dnf": Manager(
        "dnf", "dnf", ("dnf", "search"), ("dnf", "makecache", "--refresh"), ("dnf", "install"),
        ("fedora", "rhel", "centos"),
    ),
    "flatpak": Manager(
        "flatpak", "flatpak", ("flatpak", "search"), ("flatpak", "update", "--appstream"), ("flatpak", "install", "flathub"),
    ),
    "pacman": Manager(
        "pacman", "pacman", ("pacman", "-Ss"), ("pacman", "-Syyu", "--noconfirm"), ("pacman", "-S"),
        ("arch", "manjaro", "endeavouros"),
    ),
    "pip": Manager(
        "pip", "python3", ("python3", "-m", "pip", "index", "versions"), ("python3", "-m", "pip", "install", "--upgrade", "pip"), ("python3", "-m", "pip", "install"),
    ),
    "nix": Manager(
        "nix", "nix", ("nix", "search", "nixpkgs"), ("nix-channel", "--update"), ("nix-env", "-iA", "nixpkgs"),
    ),
    "apk": Manager(
        "apk", "apk", ("apk", "search"), ("apk", "update"), ("apk", "add"),
        ("alpine",),
    ),
}
