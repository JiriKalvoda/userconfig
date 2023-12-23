#!/bin/python3
import sys, os
import argparse 
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()
parser.add_argument("--root", default='/')
subparsers = parser.add_subparsers(dest="command") # this line changed
parser_long = subparsers.add_parser('long')
parser_short = subparsers.add_parser('short')
parser_i3 = subparsers.add_parser('i3')
args = parser.parse_args()

def load_last_snapshots():
    snapshots = {}
    try:
        last_dir = args.root+"/.snapshoter/last"
        for device in os.listdir(last_dir):
            with open(last_dir+'/'+device) as f:
                d = datetime.fromtimestamp(int(f.read()))
                snapshots[device] = d
    except FileNotFoundError:
        return {}
    return snapshots

no_color = "\033[39m"
def age_to_color(age):
    S = age.total_seconds()
    d = S/60/60/24
    if S < 15*60:
        return "\033[96m" # CYAN
    if d < 3:
        return "\033[92m" # GREEN
    if d < 14:
        return "\033[93m" # YELLOW
    return "\033[91m" # RED

def format_age(age):
    S = age.total_seconds()
    if S < 3*60:
        return f"{int(S)} s"
    M = int((S+30)/60)
    if M < 3*60:
        return f"{M} min"
    H = int((S/60 + 30)/60)
    if M < 3*24:
        return f"{H} h"
    d = int((S/60/60 + 12)/24)
    return f"{d} days"

def verdict(snapshots):
    now = datetime.now()
    ages = [now-x for x in sorted(snapshots.values(), reverse=True)]
    if len(ages) == 0:
        return (5, "No snapshot yet!")
    if ages[0].total_seconds()/24/60/60 > 14:
        return (4, "All snapshots too old!")
    if len(ages) == 1:
        return (3, "No secondary snapshot!")
    if ages[1].total_seconds()/24/60/60 > 30:
        return (2, "Secondary snapshot too old!")
    if ages[0].total_seconds()/24/60/60 > 2:
        return (1, "Primary snapshot could be newer.")
    if ages[1].total_seconds()/24/60/60 > 7:
        return (1, "Secondary snapshot could be newer.")
    return (0, "Very nice!")

verdict_id_to_color=["\033[92m", "\033[93m", "\033[91m", "\033[95m", "\033[95m", "\033[95m"]
verdict_id_to_color_i3=[None, "yellow", "red", "magenta", "magenta", "magenta"]

def pprint_snapshots(snapshots):
    now = datetime.now()
    for device, date in sorted(snapshots.items(), key=lambda x:x[1], reverse=True):
        age = now - date
        color = age_to_color(age)
        print(f"{device:15}{color}{date} -> {format_age(age)} old{no_color}")

def print_long_log(snapshots):
    print("\033[1mSnapshots:\033[21m")
    pprint_snapshots(snapshots)
    verdict_id, verdict_str = verdict(snapshots)
    print(f"Verdict: \033[1m{verdict_id_to_color[verdict_id]}{verdict_str}{no_color}\033[21m")

def print_short_log(snapshots):
    verdict_id, verdict_str = verdict(snapshots)
    print(f"Snapshots: \033[1m{verdict_id_to_color[verdict_id]}{verdict_str}{no_color}\033[21m")

def print_i3(snapshots):
    verdict_id, verdict_str = verdict(snapshots)
    if verdict_id_to_color_i3[verdict_id]:
        print(f'[{{"color": "{verdict_id_to_color_i3[verdict_id]}", "full_text":"{verdict_str}"}}]', flush=True)
    else:
        print(f'[]', flush=True)





if args.command == "long" or not args.command:
    print_long_log(load_last_snapshots())
if args.command == "short":
    print_short_log(load_last_snapshots())
if args.command == "i3":
    while True:
        import time
        print_i3(load_last_snapshots())
        time.sleep(30)

