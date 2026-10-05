from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from . import environments


@dataclass(frozen=True)
class Manager:
    name: str
    binary: str
    search_cmd: tuple[str, ...]
    sync_cmd: tuple[str, ...]
    install_cmd: tuple[str, ...]
    remove_cmd: tuple[str, ...]
    list_cmd: tuple[str, ...]
    native_distros: tuple[str, ...] = ()

    def host_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def available(self, native: str | None = None) -> bool:
        if environments.needs_isolation(self.name, native):
            return environments.environment_ready(self.name)
        return self.host_available()

    def _run(self, command: list[str], native: str | None = None, capture: bool = False):
        if environments.needs_isolation(self.name, native):
            return environments.run(self.name, command, capture=capture)
        if capture:
            return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return subprocess.call(command)

    def search(self, package: str, native: str | None = None) -> bool:
        result = self._run([*self.search_cmd, package], native, capture=True)
        return result.returncode == 0 and bool(result.stdout.strip())

    def sync(self, native: str | None = None) -> int:
        return self._run(list(self.sync_cmd), native)

    def install(self, package: str, native: str | None = None) -> int:
        return self._run([*self.install_cmd, package], native)

    def remove(self, package: str, native: str | None = None) -> int:
        return self._run([*self.remove_cmd, package], native)

    def list_installed(self, native: str | None = None) -> int:
        return self._run(list(self.list_cmd), native)


MANAGERS: dict[str, Manager] = {
    "apt": Manager("apt", "apt", ("apt-cache", "search", "--names-only"), ("apt", "update"), ("apt", "install"), ("apt", "remove"), ("dpkg-query", "-W"), ("debian", "ubuntu", "linuxmint", "pop", "zorin")),
    "dnf": Manager("dnf", "dnf", ("dnf", "search"), ("dnf", "makecache", "--refresh"), ("dnf", "install"), ("dnf", "remove"), ("dnf", "list", "installed"), ("fedora", "rhel", "centos")),
    "flatpak": Manager("flatpak", "flatpak", ("flatpak", "search"), ("flatpak", "update", "--appstream"), ("flatpak", "install", "flathub"), ("flatpak", "uninstall"), ("flatpak", "list")),
    "pacman": Manager("pacman", "pacman", ("pacman", "-Ss"), ("pacman", "-Syu", "--noconfirm"), ("pacman", "-S"), ("pacman", "-R"), ("pacman", "-Q"), ("arch", "manjaro", "endeavouros")),
    "pip": Manager("pip", "python3", ("python3", "-m", "pip", "index", "versions"), (), ("python3", "-m", "pip", "install"), ("python3", "-m", "pip", "uninstall", "-y"), ("python3", "-m", "pip", "list")),
    "nix": Manager("nix", "nix", ("nix", "search", "nixpkgs"), ("nix-channel", "--update"), ("nix", "profile", "install"), ("nix", "profile", "remove"), ("nix", "profile", "list")),
    "apk": Manager("apk", "apk", ("apk", "search"), ("apk", "update"), ("apk", "add"), ("apk", "del"), ("apk", "info"), ("alpine",)),
}
