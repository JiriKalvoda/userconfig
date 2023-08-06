const int adrlen = 5;
const char adr [adrlen][1000] =
{
	"/sys/class/backlight/amdgpu_bl0/brightness",
	"/sys/devices/pci0000:00/0000:00:02.0/drm/card0/card0-eDP-1/intel_backlight/brightness",
	"/sys/devices/pci0000:00/0000:00:02.0/drm/card1/card1-eDP-1/intel_backlight/brightness",
	"/sys/devices/pci0000:00/0000:00:08.1/0000:03:00.0/backlight/amdgpu_bl0/brightness",
	"/sys/class/backlight/rpi_backlight/brightness",
};


const int lightMin = 2;
const int lightMax = 255;
