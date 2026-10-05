from __future__ import annotations

import shutil

from .managers import MANAGERS, Manager

PACKAGE_NAMES: dict[str, dict[str, str]] = {
    "apt": {"flatpak": "flatpak", "pip": "python3-pip", "nix": "nix-bin"},
    "dnf": {"flatpak": "flatpak", "pip": "python3-pip", "nix": "nix"},
    "pacman": {"flatpak": "flatpak", "pip": "python-pip", "nix": "nix"},
    "apk": {"flatpak": "flatpak", "pip": "py3-pip"},
}


def try_package(manager: Manager, target: str) -> bool:
    package = PACKAGE_NAMES.get(manager.name, {}).get(target)
    if not package or not manager.available():
        return False
    print(f"  trying {manager.name}: {package}")
    if manager.sync() != 0:
        return False
    return manager.install(package) == 0 and MANAGERS[target].available()


def try_source(target: str) -> bool:
    print(f"  no package manager could install {target}; source fallback selected")
    if target == "pip":
        import subprocess
        code = subprocess.call(["python3", "-m", "ensurepip", "--upgrade"])
        return code == 0 and MANAGERS[target].available()
    print(f"  automatic source recipe for {target} is not implemented yet")
    return False


def bootstrap_manager(target: str, native: str | None) -> bool:
    manager = MANAGERS[target]
    if manager.available():
        return True
    print(f"\nInstalling {target}…")
    tried: set[str] = set()
    if native in MANAGERS and native != target:
        tried.add(native)
        if try_package(MANAGERS[native], target):
            print(f"✓ installed {target} using native {native}")
            return True
    for name, candidate in MANAGERS.items():
        if name == target or name in tried:
            continue
        tried.add(name)
        if try_package(candidate, target):
            print(f"✓ installed {target} using {name}")
            return True
    if try_source(target):
        print(f"✓ installed {target} from source")
        return True
    if target in {"apt", "dnf", "pacman", "apk"}:
        print(f"✗ {target} needs Pack's isolated distro environment; refusing to attach foreign distro repositories to the host")
    else:
        print(f"✗ couldn't install {target}")
    return False


def bootstrap_selected(selected: list[str], native: str | None) -> list[str]:
    failed: list[str] = []
    order = sorted(selected, key=lambda name: name != native)
    for name in order:
        if not bootstrap_manager(name, native):
            failed.append(name)
    return failed
