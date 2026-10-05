from __future__ import annotations

import argparse
import os
import platform
import re
import sys
from pathlib import Path

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
    values: dict[str, str] = {}
    for line in path.read_text(errors="ignore").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values.get("ID", "unknown").lower()


def detect_native_manager() -> str | None:
    distro = distro_id()
    for name, manager in MANAGERS.items():
        if distro in manager.native_distros:
            return name
    return None


def setup() -> None:
    require_root()
    native = detect_native_manager()
    print("Pack setup 📦")
    print(f"Host distro: {distro_id()}")
    if native:
        print(f"Native package manager: {native}")
    print("\nChoose package managers to enable. Enter numbers separated by spaces.")
    names = list(MANAGERS)
    for i, name in enumerate(names, 1):
        suffix = " (native)" if name == native else ""
        print(f"{i}. {name}{suffix}")
    raw = input("\nManagers: ").strip()
    chosen: list[str] = []
    for token in re.split(r"[ ,]+", raw):
        if not token:
            continue
        try:
            index = int(token) - 1
        except ValueError:
            continue
        if 0 <= index < len(names) and names[index] not in chosen:
            chosen.append(names[index])
    if not chosen:
        print("No managers selected. Nothing changed.")
        return
    config = {
        "enabled_managers": chosen,
        "native_manager": native,
        "setup_complete": True,
    }
    save_config(config)
    print("\nEnabled: " + ", ".join(chosen))
    unavailable = [name for name in chosen if not MANAGERS[name].available()]
    if unavailable:
        print("\nThese managers are selected but not bootstrapped yet:")
        for name in unavailable:
            print(f"- {name}")
        print("Foreign-manager installation/isolation is the next v0.1 piece.")
    print("\nSyncing all currently available managers…\n")
    sync_all(config, skip_unavailable=True)


def enabled(config: dict):
    return [MANAGERS[name] for name in config.get("enabled_managers", []) if name in MANAGERS]


def ensure_setup(config: dict) -> None:
    if not config.get("setup_complete"):
        print("Pack hasn't been set up yet. Run: sudo pack setup")
        raise SystemExit(1)


def sync_all(config: dict | None = None, skip_unavailable: bool = False) -> None:
    require_root()
    config = config or load_config()
    ensure_setup(config)
    managers = enabled(config)
    failed: list[str] = []
    for i, manager in enumerate(managers, 1):
        print(f"[{i}/{len(managers)}] syncing {manager.name}…")
        if not manager.available():
            print(f"! {manager.name} is not installed yet\n")
            if not skip_unavailable:
                failed.append(manager.name)
            continue
        code = manager.sync()
        if code == 0:
            print(f"✓ {manager.name} synced\n")
        else:
            print(f"✗ {manager.name} failed with exit code {code}\n")
            failed.append(manager.name)
    if failed:
        print("Pack sync finished with problems: " + ", ".join(failed))
        raise SystemExit(1)
    print("Pack sync complete.")


def show_managers() -> None:
    config = load_config()
    ensure_setup(config)
    native = config.get("native_manager")
    print("MANAGER     TYPE        STATUS")
    for name in config.get("enabled_managers", []):
        manager = MANAGERS.get(name)
        if not manager:
            continue
        kind = "native" if name == native else "managed"
        status = "ready" if manager.available() else "not installed"
        print(f"{name:<11} {kind:<11} {status}")


def find_matches(package: str, config: dict) -> list[str]:
    matches: list[str] = []
    print(f"Searching for “{package}”…")
    for manager in enabled(config):
        if not manager.available():
            continue
        try:
            if manager.search(package):
                matches.append(manager.name)
        except OSError:
            pass
    return matches


def search(package: str) -> None:
    config = load_config()
    ensure_setup(config)
    matches = find_matches(package, config)
    if not matches:
        print(f"No enabled manager found “{package}”.")
        return
    print(f"Found package “{package}” in {len(matches)} manager{'s' if len(matches) != 1 else ''}.")
    for i, name in enumerate(matches, 1):
        print(f"{i}. {name}")


def install(package: str) -> None:
    require_root()
    config = load_config()
    ensure_setup(config)
    matches = find_matches(package, config)
    if not matches:
        print(f"No enabled manager found “{package}”.")
        raise SystemExit(1)
    print(f"Found package “{package}” in {len(matches)} manager{'s' if len(matches) != 1 else ''}.")
    for i, name in enumerate(matches, 1):
        print(f"{i}. {name}")
    while True:
        choice = input(f"What version do you want to download? (1-{len(matches)}) ").strip()
        try:
            selected = matches[int(choice) - 1]
            break
        except (ValueError, IndexError):
            print("Pick one of the listed numbers.")
    manager = MANAGERS[selected]
    print(f"\nSyncing {selected}…")
    code = manager.sync()
    if code != 0:
        print(f"{selected} sync failed with exit code {code}.")
        raise SystemExit(code)
    print(f"\nStarting {selected}…")
    code = manager.install(package)
    if code == 0:
        print(f"\n✓ Installed {package} with {selected}")
    raise SystemExit(code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pack", description="One command for many Linux package managers")
    parser.add_argument("--version", action="version", version="Pack 0.1.0")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("setup", help="configure Pack and choose package managers")
    sub.add_parser("sync", help="sync every enabled package manager")
    sub.add_parser("managers", help="show enabled package managers")
    search_parser = sub.add_parser("search", help="search every enabled package manager")
    search_parser.add_argument("package")
    install_parser = sub.add_parser("install", help="search, choose a manager, sync it, and install")
    install_parser.add_argument("package")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "setup":
        setup()
    elif args.command == "sync":
        sync_all()
    elif args.command == "managers":
        show_managers()
    elif args.command == "search":
        search(args.package)
    elif args.command == "install":
        install(args.package)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
