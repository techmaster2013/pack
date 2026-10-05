from __future__ import annotations
import argparse, os, platform, re, subprocess, tempfile
from pathlib import Path
from .bootstrap import bootstrap_selected
from .config import load_config, save_config
from .managers import MANAGERS
REPO="https://github.com/techmaster2013/pack.git"

def require_root():
 if hasattr(os,"geteuid") and os.geteuid()!=0: raise SystemExit("Pack needs root. Try again with sudo.")
def distro_id():
 p=Path("/etc/os-release")
 if not p.exists(): return platform.system().lower()
 v={}
 for line in p.read_text(errors="ignore").splitlines():
  if "=" in line: k,x=line.split("=",1); v[k]=x.strip().strip('"')
 return v.get("ID","unknown").lower()
def detect_native_manager():
 d=distro_id(); return next((n for n,m in MANAGERS.items() if d in m.native_distros),None)
def enabled(c): return [MANAGERS[n] for n in c.get("enabled_managers",[]) if n in MANAGERS]
def ensure_setup(c):
 if not c.get("setup_complete"): raise SystemExit("Pack hasn't been set up. Run: sudo pack setup")

def setup():
 require_root(); native=detect_native_manager(); names=list(MANAGERS)
 print(f"Pack setup 📦\nHost distro: {distro_id()}\nNative package manager: {native or 'unknown'}\n\nChoose managers by number, or 'all'.")
 for i,n in enumerate(names,1): print(f"{i}. {n}"+(" (native)" if n==native else ""))
 raw=input("\nManagers: ").strip().lower(); chosen=names[:] if raw=="all" else []
 if raw!="all":
  for token in re.split(r"[ ,]+",raw):
   try: name=names[int(token)-1]
   except (ValueError,IndexError): continue
   if name not in chosen: chosen.append(name)
 if not chosen: return print("No managers selected.")
 failed=bootstrap_selected(chosen,native); c={"enabled_managers":chosen,"native_manager":native,"setup_complete":True,"bootstrap_failed":failed}; save_config(c); sync_all(c,True)
 if failed: print("Unavailable: "+", ".join(failed))

def sync_all(c=None,skip_unavailable=False):
 require_root(); c=c or load_config(); ensure_setup(c); native=c.get("native_manager"); failed=[]; items=enabled(c)
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
def find_matches(pkg,c):
 native=c.get("native_manager"); found=[]; print(f"Searching for “{pkg}”…")
 for m in enabled(c):
  if m.available(native):
   try:
    if m.search(pkg,native): found.append(m.name)
   except OSError: pass
 return found
def search(pkg):
 c=load_config(); ensure_setup(c); found=find_matches(pkg,c)
 if not found: return print(f"No enabled manager found “{pkg}”.")
 for i,n in enumerate(found,1): print(f"{i}. {n}")
def choose(pkg,c):
 found=find_matches(pkg,c)
 if not found: raise SystemExit(f"No enabled manager found “{pkg}”.")
 for i,n in enumerate(found,1): print(f"{i}. {n}")
 while True:
  try: return found[int(input(f"Choose manager (1-{len(found)}): "))-1]
  except (ValueError,IndexError): print("Pick one of the listed numbers.")
def install(pkg):
 require_root(); c=load_config(); ensure_setup(c); native=c.get("native_manager"); n=choose(pkg,c); m=MANAGERS[n]
 if m.sync(native): raise SystemExit(f"{n} sync failed")
 code=m.install(pkg,native)
 if code==0: print(f"✓ Installed {pkg} with {n}")
 raise SystemExit(code)
def remove(pkg):
 require_root(); c=load_config(); ensure_setup(c); n=choose(pkg,c); raise SystemExit(MANAGERS[n].remove(pkg,c.get("native_manager")))
def list_packages():
 c=load_config(); ensure_setup(c); native=c.get("native_manager")
 for m in enabled(c):
  if m.available(native): print(f"\n=== {m.name} ==="); m.list_installed(native)
