# jolla: Arch Linux kontejner na Sailfish OS

Plnohodnotný Arch Linux ARM (aarch64) se systemd jako PID 1, běžící v crun
kontejneru na telefonu Jolla (Sailfish OS 5.2, kernel 6.12, Android 16 BSP,
MediaTek + Mali). Kontejner netvoří bezpečnostní bariéru: root uvnitř = root
venku, sdílený síťový, UTS a IPC namespace, hostitelský `/dev` a `/sys`.
Vlastní má jen mount, PID a cgroup namespace (ty vyžaduje systemd jako init).

Rootfs kontejneru je **build artefakt**: recept generuje blach (`jk.py`, stroj
`major`, systém `os_system`), staví ho rootfs na hopiku, telefon si verze tahá
rsyncem přes ssh. Na telefonu zůstává jen crun, config a pár skriptů.

## Tok

```
# hopik
blach/rootfsgen/gen.py jk-major -V v1 | rootfs/build.py
          # arch_base flavour alarm (Arch Linux ARM, snapshot v arch_cache), arch_pkg,
          # klon userconfig, jolla/container/init.sh uvnitř stromu, manifest
# telefon
arch-fetch v1        # rsync --link-dest, ověření manifestu -> /home/arch/versions/v1
arch-activate v1     # current -> versions/v1, restart arch-container.service
```

Pin "last" v `arch_snapshot` se při generování rozloží na den, takže cache
klíč se mění jednou denně; snapshot ALARM databází si bere `arch_cache` při
prvním fetchi a dál servíruje jen z cache (jako Alpine).

## Rozložení

| Soubor | Kam | Účel |
|---|---|---|
| `container/init.sh` | běží při **buildu** uvnitř stromu | masky služeb, defaultuser uid 100000 + hostitelské gid, locale, profile.d, `hybris` wrapper, dbus-broker |
| `container/files/` | `/etc/profile.d/sfos.sh`, journald drop-in, `/usr/local/bin/hybris` | linkováno confln z `/etc/userconfig` ve stromu |
| `init.sh` | telefon, sysconfig | crun, bundle, skripty, unita |
| `config.json` | `/etc/arch-container/` | OCI bundle, root = overlay `/home/arch/root` |
| `fetch.conf` | `/etc/arch-container/` | builder, cesta k datům, device |
| `arch-container.service` | `/etc/systemd/system/` | hostitelská unita, `Delegate=yes` |
| `bin/arch-fetch`, `arch-activate` | `/usr/local/bin/` | stažení verze, přepnutí |
| `bin/arch-run`, `arch-stop` | `/usr/local/bin/` | overlay mount, hybris symlinky, crun (volá unita) |
| `bin/arch-exec`, `arch-shell` | `/usr/local/bin/` | root shell / shell jako defaultuser s GUI prostředím |

Na telefonu pod `/home/arch` (LUKS `/home`): `versions/<ver>/fs` (store,
hardlinky mezi verzemi), `overlay/<ver>/{upper,work}` (stav per verze),
`home` (persistentní `/home/defaultuser`, mimo overlay), `root` (mountpoint
overlaye), `hybris-lib` (symlinky generované při startu), `current`, `previous`.

## Instalace na telefonu

```
devel-su
pkcon install git rsync
git clone <userconfig> /etc/userconfig     # sysconfig = cesta musí začínat /etc
/etc/userconfig/jolla/init.sh
arch-fetch -l; arch-fetch v1; arch-activate v1
```

Root telefonu potřebuje ssh klíč na `jiri@hopik` (viz `fetch.conf`).
`container/init.sh` musí být commitnutý a pushnutý v userconfigu, než se
staví: builder ho klonuje z `git_userconfig_remotes`.

Možná nástraha: Sailfish má busybox verze `ln`, `tar`, `diff`. Pokud `confln`
spadne na `ln -sr`, nainstalovat GNU coreutils.

## Jak to funguje

- **Wayland:** Lipstick poslouchá na `/run/display/wayland-0` (world rw).
  Bindujeme `/run/display` a `/run/user/100000`; `profile.d/sfos.sh` nastaví
  `WAYLAND_DISPLAY`, session D-Bus a PulseAudio socket pro uid 100000.
  Sailfish OS 5.1+ má v Lipsticku xdg_shell, takže Qt6/GTK4 klienti se připojí přímo.
- **GPU:** hostitelské `/usr/lib64` je v kontejneru jako `/sfos/lib64` (ro).
  `arch-run` při každém startu vygeneruje `/home/arch/hybris-lib` se symlinky
  na soubory libhybris RPM (`rpm -ql`), bindnuté jako `/opt/hybris/lib`.
  Wrapper `hybris <cmd>` nastaví `LD_LIBRARY_PATH`, `EGL_PLATFORM=wayland`,
  `HYBRIS_EGLPLATFORM=wayland`. Bez wrapperu běží mesa (llvmpipe). Android
  část: bind `/system`, `/vendor`, `/apex`, `/usr/libexec/droid-hybris`, uzly
  `/dev/mali0`, `/dev/dma_heap/*`, `/dev/__properties__` přes hostitelský
  `/dev`. Jen GLES, ne desktop GL. Build je na hostiteli nezávislý,
  aktualizace libhybris na telefonu se promítne sama.
- **cgroupy:** hostitel (systemd 238) je hybridní. V kontejneru mountujeme
  cgroup2 na `/sys/fs/cgroup`; cgroup namespace dá Arch systemd jeho podstrom
  jako root. Kontrolery na v2 straně nejsou, systemd běží bez resource
  control. `cgroupsPath` míří do cgroupu hostitelské unity, proto `Delegate=yes`.
- **Overlay:** lower = `versions/<ver>/fs`, upper per verze. Ruční `pacman -S`
  přežije restart, ne update verze; co má přežít, patří do receptu.
- **Zastavení:** `arch-stop` pošle initu SIGRTMIN+3 (čistý poweroff systemd).
- **Capabilities:** všechny kromě `CAP_SYS_BOOT` (omyl uvnitř by jinak mohl
  restartovat telefon; systemd s `container=oci` reboot(2) sám nevolá).
- **hostname:** `/etc/hostname` se ve stromu maže; UTS je sdílený.
- **DNS:** `arch-run` kopíruje `/etc/resolv.conf` při startu (connman ho přepisuje).

## Ověření

```
systemctl status arch-container
arch-exec systemctl is-system-running; arch-exec systemctl --failed
arch-exec cat /proc/1/cgroup; arch-exec ls /sys/fs/cgroup
arch-shell wayland-info | head -40          # musí obsahovat xdg_wm_base
arch-shell foot                             # okno v Lipsticku, shm, bez GPU
arch-shell glmark2-es2-wayland              # llvmpipe baseline
arch-shell hybris glmark2-es2-wayland       # libhybris, Mali
HYBRIS_LD_DEBUG=1 arch-shell hybris glmark2-es2-wayland   # ladění linkeru
```

## Stav

- [x] rootfs: `arch_cache` flavour `alarm` (snapshoty, pool, .sig), `arch_base`/`arch_pkg` s pinem ve stromu (selftest OK)
- [x] blach: `System.arch_flavour`, `ArchBase(flavour)`, `Manifest`, `userconfig.jolla_container`, `major.os_system`
- [ ] build `jk-major` na hopiku (qemu-user aarch64 binfmt, `arch_cache.py serve`)
- [ ] fáze 1: kontejner + systemd nastartuje bez failed unit
- [ ] fáze 2a: foot se zobrazí jako okno v Lipsticku
- [ ] fáze 2b: `hybris glmark2-es2-wayland` jede na Mali
- [ ] fáze 3: Qt6 / GTK4 / Firefox s hybrisem
- [ ] později: spouštění z launcheru (sudo je v repu jolla), zvuk, Xwayland
