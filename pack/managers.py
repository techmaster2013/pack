from __future__ import annotations
import os, shutil, subprocess
from dataclasses import dataclass
from . import environments

SYSTEM_MANAGERS={"apt","dnf","pacman","apk","snap"}

@dataclass(frozen=True)
class Manager:
    name:str; binary:str; search_cmd:tuple[str,...]; sync_cmd:tuple[str,...]; install_cmd:tuple[str,...]; remove_cmd:tuple[str,...]; list_cmd:tuple[str,...]; native_distros:tuple[str,...]=()
    def host_available(self): return shutil.which(self.binary) is not None
    def available(self,native=None): return environments.environment_ready(self.name) if environments.needs_isolation(self.name,native) else self.host_available()
    def _run(self,command,native=None,capture=False,write=False):
        if not command: return subprocess.CompletedProcess([],0,"","") if capture else 0
        if environments.needs_isolation(self.name,native): return environments.run(self.name,command,capture=capture)
        command=list(command)
        # Pack stays a normal-user program. Elevate only host system-manager writes.
        if write and self.name in SYSTEM_MANAGERS and hasattr(os,"geteuid") and os.geteuid()!=0:
            command=["sudo",*command]
        if capture: return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        return subprocess.call(command)
    def search(self,pkg,native=None):
        r=self._run([*self.search_cmd,pkg],native,True); return r.returncode==0 and bool(r.stdout.strip())
    def sync(self,native=None): return self._run(list(self.sync_cmd),native,write=True)
    def install(self,pkg,native=None):
        if self.name=="nix": pkg=f"nixpkgs#{pkg}"
        return self._run([*self.install_cmd,pkg],native,write=True)
    def remove(self,pkg,native=None): return self._run([*self.remove_cmd,pkg],native,write=True)
    def list_installed(self,native=None): return self._run(list(self.list_cmd),native)

MANAGERS={
 "apt":Manager("apt","apt",("apt-cache","search","--names-only"),("apt","update"),("apt","install","-y"),("apt","remove","-y"),("dpkg-query","-W"),("debian","ubuntu","linuxmint","pop","zorin")),
 "dnf":Manager("dnf","dnf",("dnf","search"),("dnf","makecache","--refresh"),("dnf","install","-y"),("dnf","remove","-y"),("dnf","list","installed"),("fedora","rhel","centos")),
 "flatpak":Manager("flatpak","flatpak",("flatpak","search"),("flatpak","update","--appstream"),("flatpak","install","-y","flathub"),("flatpak","uninstall","-y"),("flatpak","list")),
 "pacman":Manager("pacman","pacman",("pacman","-Ss"),("pacman","-Syu","--noconfirm"),("pacman","-S","--needed","--noconfirm"),("pacman","-R","--noconfirm"),("pacman","-Q"),("arch","manjaro","endeavouros")),
 "pip":Manager("pip","python3",("python3","-m","pip","index","versions"),(),("python3","-m","pip","install"),("python3","-m","pip","uninstall","-y"),("python3","-m","pip","list")),
 "nix":Manager("nix","nix",("nix","search","nixpkgs"),("nix-channel","--update"),("nix","profile","install"),("nix","profile","remove"),("nix","profile","list")),
 "apk":Manager("apk","apk",("apk","search"),("apk","update"),("apk","add"),("apk","del"),("apk","info"),("alpine",)),
 "snap":Manager("snap","snap",("snap","find"),("snap","refresh"),("snap","install"),("snap","remove"),("snap","list")),
 "brew":Manager("brew","brew",("brew","search"),("brew","update"),("brew","install"),("brew","uninstall"),("brew","list")),
 "cargo":Manager("cargo","cargo",("cargo","search"),(),("cargo","install"),("cargo","uninstall"),("cargo","install","--list")),
 "gem":Manager("gem","gem",("gem","search","-r"),(),("gem","install"),("gem","uninstall","-aIx"),("gem","list")),
 "npm":Manager("npm","npm",("npm","search"),(),("npm","install","-g"),("npm","uninstall","-g"),("npm","list","-g","--depth=0")),
}
