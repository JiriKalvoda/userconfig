#!/bin/env python3
import subprocess
import re
import datetime
td = datetime.timedelta

VERDICT_WRONG = 2
VERDICT_WARN = 1
VERDICT_GOOD = 0

inf = float('inf')

def format_timedelta(td: datetime.timedelta) -> str:
	seconds = int(td.total_seconds())
	days  = seconds // 86400  # 1 day = 86400 seconds
	hours = seconds // 3600  # 1 hour = 3600 seconds
	minutes = seconds // 60 # 1 minute = 60 seconds

	if days > 3:
		return f"{days} days"
	if hours > 3:
		return f"{hours} hours"
	if minutes > 5:
		return f"{minutes} minute"
	return f"{seconds} second"

def run(*args):
    p = subprocess.run(args, check=True, stdout=subprocess.PIPE)
    return p.stdout.decode()

def verdict(val, verdict=VERDICT_WRONG, good=None, warn=None, format=str):
	global total_verdict
	if warn:
		if warn[0] <= val <= warn[1]:
			verdict = VERDICT_WARN
	if good:
		if good[0] <= val <= good[1]:
			verdict = VERDICT_GOOD
	total_verdict = max(total_verdict, verdict)
	return f"\033[1;{ {VERDICT_GOOD:32, VERDICT_WARN:33, VERDICT_WRONG:31}[verdict] }m{format(val)}\033[0m"

#print(df('/', ssh=['ssh', 'root@radeu1.meteopress.cz']))
#print(df('/', ssh=['ssh', 'root@radeu1.meteopress.cz'], inodes=True))

total_verdict = 0

print("NETWORK")
print("========")
nft_data = run("nft", "list", "ruleset")
print(f"NFT length:   {verdict(len(nft_data), good=(100,inf))}")

print("USERS")
print("=====")
with open("/etc/shaddow")
nft_data = run("nft", "list", "ruleset")
print(f"NFT length:   {verdict(len(nft_data), good=(100,inf))}")
