#!/bin/env python3
import argparse
import datetime
import sys, os
import time

filename = os.environ['HOME']+'/work_log'

def get_current_state():
    import os

    with open(filename, 'rb') as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()

    out =  last_line.split('\t')
    while len(out)<3:
        out.append(None)
    return out

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='subparser')

parser_a = subparsers.add_parser('i3status')

parser_a = subparsers.add_parser('log')
parser_a.add_argument('job', default='', nargs="?")

parser_a = subparsers.add_parser('stats')


args = parser.parse_args()
if args.subparser == 'i3status':
    while True:
        try:
            cs = get_current_state()
            job = cs[1]
            if job:
                print(f'[{{"color": "orange", "full_text":"{job}"}}]', flush=True)
            else:
                print('[]', flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
        time.sleep(3)

if args.subparser == 'log':
    print(args.job)
    with open(filename, 'a') as f:
        f.write(f"{datetime.datetime.now().astimezone().isoformat()}\t{args.job}\t\n")

if args.subparser == 'stats':
    with open(filename, 'r') as f:
        data = [l.split('\t') for l in f.read().split('\n') if l]
        total_time = {}
        for x, y in zip(data, data[1:]):
            activity = x[1]
            if activity:
                t = datetime.datetime.fromisoformat(y[0]) - datetime.datetime.fromisoformat(x[0])
                total_time.setdefault(activity, datetime.timedelta())
                total_time[activity] += t
        for k, v in total_time.items():
            print(k, v)


