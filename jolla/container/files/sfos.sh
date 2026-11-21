# Prostředí pro GUI aplikace zobrazované v Lipsticku (Sailfish OS).
# Platí pro uid 100000 (defaultuser), který sdílíme s hostitelem.
if [ "$(id -u)" = 100000 ]; then
	export XDG_RUNTIME_DIR=/run/user/100000
	export WAYLAND_DISPLAY=/run/display/wayland-0
	export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket
	export PULSE_SERVER=unix:/run/user/100000/pulse/native
	export QT_QPA_PLATFORM=wayland
	export GDK_BACKEND=wayland
	export SDL_VIDEODRIVER=wayland
	export MOZ_ENABLE_WAYLAND=1
fi
