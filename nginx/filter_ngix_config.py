#!/bin/python3
import tempfile, subprocess
import os, sys
from pathlib import Path

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("args", nargs='+', help="source:target")
args = parser.parse_args()

CLONE_NEWNS = 0x00020000  # Mount namespace

def unshare(flags):
    import ctypes
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    result = libc.unshare(flags)
    if result != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def err(*args):
	print(*args, file=sys.stderr)

def setup_overlay():
	upper_dir = tempfile.mkdtemp()
	work_dir = tempfile.mkdtemp()
	mount_dir = tempfile.mkdtemp()
	lower_dir = "/"

	# Přepnutí do nového filesystem namespace
	try:
		os_unshare = os.unshare
	except AttributeError:
		unshare(CLONE_NEWNS)
	else:
		os.unshare(os.CLONE_NEWNS)

	# Nastavení private mount propagace
	subprocess.run(["mount", "--make-rprivate", "/"], check=True)

	# Vytvoření overlay mountu
	options = f"lowerdir={lower_dir},upperdir={upper_dir},workdir={work_dir}"
	subprocess.run(["mount", "-t", "overlay", "overlay", "-o", options, mount_dir], check=True)

	# Ponechání v novém mountu
	return mount_dir
	#os.chdir(mount_dir)
	#os.system("/bin/bash")  # Otevře shell v novém namespace s overlay filesystemem

overlay = Path(setup_overlay())
# subprocess.run(['ls', overlay])

class DirPair:
	def __init__(self, source, target):
		self.source = Path(source)
		self.target = Path(target)
		self.overlay_source = overlay/str(self.source.absolute())[1:]
		self.overlay_target = overlay/str(self.target.absolute())[1:]
		self.output = {}

def test():
	p = subprocess.run(['chroot', overlay, 'nginx', '-t'], stderr=subprocess.PIPE)
	return p.stderr.decode() if p.returncode else None

#dirs = [DirPair('/etc/nginx/sites.d', '/etc/nginx/sites_checked.d'), DirPair('/etc/nginx/default_host.d', '/etc/nginx/default_host_checked.d'), ]
dirs = [DirPair(*x.split(":")) for x in args.args]


for dp in dirs:
	for f in dp.overlay_target.iterdir():
		os.remove(f)

if (tr := test()):
	err("Error in main config, exiting:")
	err(tr)
	exit(1)

for dp in dirs:
	for f in os.listdir(dp.overlay_source):
		os.symlink(dp.source.absolute()/f, dp.overlay_target/f)
		if (tr := test()):
			err(f"Error in {dp.source/f}:")
			err(tr)
			dp.output[f] = False
		else:
			dp.output[f] = True
		os.remove(dp.overlay_target/f)
	for f, val in dp.output.items():
		if val:
			os.symlink(dp.source.absolute()/f, dp.overlay_target/f)

for dp in dirs:
	for f, val in dp.output.items():
		is_installed = (dp.target/f).exists()
		if is_installed != val:
			if val:
				os.symlink(dp.source.absolute()/f, dp.target/f)
				print(f"Enabling {dp.source/f}")
			else:
				os.remove(dp.target/f)
				print(f"Disabling {dp.source/f}")
