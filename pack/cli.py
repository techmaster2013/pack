from __future__ import annotations

import argparse
import os
import platform
import re
from pathlib import Path

from .bootstrap import bootstrap_selected
from .config import load_config, save_config
from .managers import MANAGERS


def require_root() -> None:
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Pack needs root for this command. Try again with sudo.")
        raise SystemExit(1)


def distro_id() -> str:
    path = Path("/etc/os-release")
    if not path.exists():
        return platform.system().lower()
    values = {}
    for line in path.read_text(errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values.get("ID", "unknown").lower()


def detect_native_manager() -> str | None:
    distro = distro_id()
    for name, manager in MANAGERS.items():
        if distro in manager.native_distros:
            return name
    return None


def enabled(config: dict):
    return [MANAGERS[name] for name in config.get("enabled_managers", []) if name in MANAGERS]


def ensure_setup(config: dict) -> None:
    if not config.get("setup_complete"):
        print("Pack hasn't been set up yet. Run: sudo pack setup")
        raise SystemExit(1)


def setup() -> None:
    require_root()
    native = detect_native_manager()
    names = list(MANAGERS)
    print("Pack setup 📦")
    print(f"Host distro: {distro_id()}")
    print(f"Native package manager: {native or 'unknown'}")
    print("\nChoose package managers. Enter numbers separated by spaces, or 'all'.")
    for i, name in enumerate(names, 1):
        print(f"{i}. {name}" + (" (native)" if name == native else ""))
    raw = input("\nManagers: ").strip().lower()
    chosen = names[:] if raw == "all" else []
    if raw != "all":
        for token in re.split(r"[ ,]+", raw):
            try:
                name = names[int(token) - 1]
            except (ValueError, IndexError):
                continue
            if name not in chosen:
                chosen.append(name)
    if not chosen:
        print("No managers selected. Nothing changed.")
        return
    failed = bootstrap_selected(chosen, native)
    config = {"enabled_managers": chosen, "native_manager": native, "setup_complete": True, "bootstrap_failed": failed}
    save_config(config)
    print("\nSyncing every ready manager…")
    sync_all(config, skip_unavailable=True)
    if failed:
        print("Setup finished with unavailable managers: " + ", ".join(failed))


def sync_all(config: dict | None = None, skip_unavailable: bool = False) -> None:
    require_root()
    config = config or load_config()
    ensure_setup(config)
    native = config.get("native_manager")
    failed = []
    managers = enabled(config)
    for i, manager in enumerate(managers, 1):
        print(f"[{i}/{len(managers)}] syncing {manager.name}…")
        if not manager.available(native):
            print("! not ready\n")
            if not skip_unavailable:
                failed.append(manager.name)
            continue
        code = manager.sync(native)
        print("✓ synced\n" if code == 0 else f"✗ exit {code}\n")
        if code:
            failed.append(manager.name)
    if failed and not skip_unavailable:
        raise SystemExit("Pack sync finished with problems: " + ", ".join(failed))
    print("Pack sync complete.")


def show_managers() -> None:
    config = load_config()
    ensure_setup(config)
    native = config.get("native_manager")
    print("MANAGER     TYPE        STATUS")
    for name in config.get("enabled_managers", []):
        manager = MANAGERS[name]
        kind = "native" if name == native else ("isolated" if name in {"apt", "dnf", "pacman", "apk"} else "universal")
        print(f"{name:<11} {kind:<11} {'ready' if manager.available(native) else 'failed'}")


def find_matches(package: str, config: dict) -> list[str]:
    native = config.get("native_manager")
    matches = []
    print(f"Searching for “{package}”…")
    for manager in enabled(config):
        if not manager.available(native):
            continue
        try:
            if manager.search(package, native):
                matches.append(manager.name)
        except OSError:
            pass
    return matches
