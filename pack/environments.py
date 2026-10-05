from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path("/var/lib/pack/roots")
DISTRO_FOR_MANAGER = {"apt": "debian", "dnf": "fedora", "pacman": "archlinux", "apk": "alpine"}


def needs_isolation(name: str, native: str | None) -> bool:
    return name in DISTRO_FOR_MANAGER and name != native


def environment_name(manager: str) -> str:
    return f"pack-{manager}"


def environment_ready(manager: str) -> bool:
    if not shutil.which("podman"):
        return False
    result = subprocess.run(
        ["podman", "container", "exists", environment_name(manager)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def create_environment(manager: str) -> bool:
    distro = DISTRO_FOR_MANAGER[manager]
    ROOT.mkdir(parents=True, exist_ok=True)
    if environment_ready(manager):
        return True
    if not shutil.which("podman"):
        return False
    print(f"  creating isolated {distro} environment for {manager}…")
    # A persistent container gives each foreign manager its own /usr, database,
    # repositories and dependency graph instead of mixing them into the host.
    cmd = [
        "podman", "create", "--name", environment_name(manager),
        "--network", "host", f"docker.io/library/{distro}:latest", "sleep", "infinity",
    ]
    return subprocess.call(cmd) == 0


def run(manager: str, args: list[str]) -> int:
    name = environment_name(manager)
    if not environment_ready(manager) and not create_environment(manager):
        return 1
    subprocess.call(["podman", "start", name], stdout=subprocess.DEVNULL)
    return subprocess.call(["podman", "exec", "-i", name, *args])
