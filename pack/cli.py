from __future__ import annotations

import argparse
import os
import platform
import re
from pathlib import Path

from .bootstrap import bootstrap_selected
from .config import load_config, save_config
from .managers import MANAGERS


def require_root():
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        raise SystemExit("Pack needs root. Try again with sudo.")

def distro_id():
    path=Path("/etc/os-release")
    if not path.exists(): return platform.system().lower()
    values={}
    for line in path.read_text(errors="ignore").splitlines():
        if "=" in line:
            k,v=line.split("=",1); values[k]=v.strip().strip('"')
    return values.get("ID","unknown").lower()

def detect_native_manager():
    distro=distro_id()
    return next((n for n,m in MANAGERS.items() if distro in m.native_distros),None)

def enabled(config): return [MANAGERS[n] for n in config.get("enabled_managers",[]) if n in MANAGERS]
def ensure_setup(config):
    if not config.get("setup_complete"): raise SystemExit("Pack hasn't been set up. Run: sudo pack setup")

def setup():
    require_root(); native=detect_native_manager(); names=list(MANAGERS)
    print(f"Pack setup 📦\nHost distro: {distro_id()}\nNative package manager: {native or 'unknown'}")
    print("\nChoose managers by number, or 'all'.")
    for i,n in enumerate(names,1): print(f"{i}. {n}"+(" (native)" if n==native else ""))
    raw=input("\nManagers: ").strip().lower(); chosen=names[:] if raw=="all" else []
    if raw!="all":
        for token in re.split(r"[ ,]+",raw):
            try: name=names[int(token)-1]
            except (ValueError,IndexError): continue
            if name not in chosen: chosen.append(name)
    if not chosen: return print("No managers selected.")
    failed=bootstrap_selected(chosen,native)
    config={"enabled_managers":chosen,"native_manager":native,"setup_complete":True,"bootstrap_failed":failed}
    save_config(config); print("\nSyncing every ready manager…"); sync_all(config,True)
    if failed: print("Unavailable: "+", ".join(failed))

def sync_all(config=None,skip_unavailable=False):
    require_root(); config=config or load_config(); ensure_setup(config); native=config.get("native_manager"); failed=[]; items=enabled(config)
    for i,m in enumerate(items,1):
        print(f"[{i}/{len(items)}] syncing {m.name}…")
        if not m.available(native):
            if not skip_unavailable: failed.append(m.name)
            continue
        if m.sync(native): failed.append(m.name)
    if failed and not skip_unavailable: raise SystemExit("Sync problems: "+", ".join(failed))
    print("Pack sync complete.")

def show_managers():
    c=load_config(); ensure_setup(c); native=c.get("native_manager"); print("MANAGER     TYPE        STATUS")
    for n in c.get("enabled_managers",[]):
        m=MANAGERS[n]; typ="native" if n==native else ("isolated" if n in {"apt","dnf","pacman","apk"} else "universal")
        print(f"{n:<11} {typ:<11} {'ready' if m.available(native) else 'failed'}")

def find_matches(package,config):
    native=config.get("native_manager"); found=[]; print(f"Searching for “{package}”…")
    for m in enabled(config):
        if m.available(native):
            try:
                if m.search(package,native): found.append(m.name)
            except OSError: pass
    return found

def search(package):
    c=load_config(); ensure_setup(c); found=find_matches(package,c)
    if not found: return print(f"No enabled manager found “{package}”.")
    print(f"Found package in {len(found)} manager(s).")
    for i,n in enumerate(found,1): print(f"{i}. {n}")

def choose(package,c):
    found=find_matches(package,c)
    if not found: raise SystemExit(f"No enabled manager found “{package}”.")
    for i,n in enumerate(found,1): print(f"{i}. {n}")
    while True:
        try: return found[int(input(f"Choose manager (1-{len(found)}): "))-1]
        except (ValueError,IndexError): print("Pick one of the listed numbers.")

def install(package):
    require_root(); c=load_config(); ensure_setup(c); native=c.get("native_manager"); selected=choose(package,c); m=MANAGERS[selected]
    print(f"\nSyncing {selected}…")
    if m.sync(native): raise SystemExit(f"{selected} sync failed")
    print(f"\nStarting {selected}…"); code=m.install(package,native)
    if code==0: print(f"\n✓ Installed {package} with {selected}")
    raise SystemExit(code)

def remove(package):
    require_root(); c=load_config(); ensure_setup(c); native=c.get("native_manager"); selected=choose(package,c); raise SystemExit(MANAGERS[selected].remove(package,native))

def list_packages():
    c=load_config(); ensure_setup(c); native=c.get("native_manager")
    for m in enabled(c):
        if m.available(native): print(f"\n=== {m.name} ==="); m.list_installed(native)

def build_parser():
    p=argparse.ArgumentParser(prog="pack",description="One command for many Linux package managers"); p.add_argument("--version",action="version",version="Pack 0.1.0"); sub=p.add_subparsers(dest="command")
    for n,h in (("setup","configure and bootstrap Pack"),("sync","sync all managers"),("managers","show managers"),("list","list installed packages")): sub.add_parser(n,help=h)
    for n in ("search","install","remove"): q=sub.add_parser(n); q.add_argument("package")
    return p

def main():
    p=build_parser(); a=p.parse_args(); simple={"setup":setup,"sync":sync_all,"managers":show_managers,"list":list_packages}
    if a.command in simple: simple[a.command]()
    elif a.command in {"search","install","remove"}: globals()[a.command](a.package)
    else: p.print_help()

if __name__=="__main__": main()
