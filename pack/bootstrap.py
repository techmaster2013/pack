from __future__ import annotations
import shutil, subprocess
from . import environments
from .managers import MANAGERS, Manager

PACKAGE_NAMES={
 "apt":{"dnf":"dnf","flatpak":"flatpak","pip":"python3-pip","nix":"nix-bin","podman":"podman","snap":"snapd","cargo":"cargo","gem":"ruby-full","npm":"npm"},
 "dnf":{"flatpak":"flatpak","pip":"python3-pip","nix":"nix","podman":"podman","snap":"snapd","cargo":"cargo","gem":"ruby","npm":"npm"},
 "pacman":{"flatpak":"flatpak","pip":"python-pip","nix":"nix","podman":"podman","snap":"snapd","cargo":"rust","gem":"ruby","npm":"npm"},
 "apk":{"pip":"py3-pip","podman":"podman","cargo":"cargo","gem":"ruby","npm":"npm"},
}

def try_package(manager:Manager,target:str)->bool:
 package=PACKAGE_NAMES.get(manager.name,{}).get(target)
 if not package or not manager.host_available(): return False
 print(f"  trying {manager.name}: {package}")
 if manager.sync(manager.name): print(f"  ! {manager.name} metadata refresh failed; trying install with existing metadata")
 return manager.install(package,manager.name)==0

def ensure_podman(native):
 if shutil.which("podman"): return True
 if native in MANAGERS and try_package(MANAGERS[native],"podman") and shutil.which("podman"): return True
 return False

def bootstrap_manager(target,native):
 manager=MANAGERS[target]
 if environments.needs_isolation(target,native):
  if not ensure_podman(native): print(f"✗ couldn't install Podman, required to isolate {target}"); return False
  return environments.create_environment(target)
 if manager.host_available(): return True
 if native in MANAGERS and native!=target and try_package(MANAGERS[native],target) and manager.host_available(): return True
 for name,candidate in MANAGERS.items():
  if name not in {native,target} and try_package(candidate,target) and manager.host_available(): return True
 if target=="pip": return subprocess.call(["python3","-m","ensurepip","--upgrade"])==0
 print(f"✗ couldn't bootstrap {target}"); return False

def bootstrap_selected(selected,native):
 failed=[]
 for name in sorted(selected,key=lambda item:item!=native):
  print(f"\nPreparing {name}…")
  if bootstrap_manager(name,native): print(f"✓ {name} ready")
  else: failed.append(name)
 return failed
