from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

IMAGES = {
    "apt": "docker.io/library/debian:stable",
    "dnf": "docker.io/library/fedora:latest",
    "pacman": "docker.io/library/archlinux:latest",
    "apk": "docker.io/library/alpine:latest",
}


@dataclass
class Result:
    returncode: int
    stdout: str = ""


def needs_isolation(name: str, native: str | None) -> bool:
    return name in IMAGES and name != native


def environment_name(manager: str) -> str:
    return f"pack-{manager}"


def environment_ready(manager: str) -> bool:
    if not shutil.which("podman"):
        return False
    return subprocess.run(
        ["podman", "container", "exists", environment_name(manager)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def create_environment(manager: str) -> bool:
    if environment_ready(manager):
        return True
    if not shutil.which("podman"):
        return False
    image = IMAGES[manager]
    print(f"  creating isolated {manager} environment from {image}…")
    if subprocess.call(["podman", "pull", image]) != 0:
        return False
    return subprocess.call([
        "podman", "create", "--name", environment_name(manager),
        "--network", "host", image, "sleep", "infinity",
    ]) == 0


def run(manager: str, args: list[str], capture: bool = False):
    if not environment_ready(manager) and not create_environment(manager):
        return Result(1) if capture else 1
    name = environment_name(manager)
    subprocess.call(["podman", "start", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    command = ["podman", "exec", "-i", name, *args]
    if capture:
        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return subprocess.call(command)
