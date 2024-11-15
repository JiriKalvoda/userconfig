#!/bin/env python3
import argparse
import datetime
import sys, os
import time
from datetime import datetime, timedelta, date
import datetime as dt

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
        time.sleep(1)

if args.subparser == 'log':
    print(args.job)
    with open(filename, 'a') as f:
        f.write(f"{datetime.now().astimezone().isoformat()}\t{args.job}\t\n")

if args.subparser == 'stats':
    by_days = {}

    def divide_per_days(activity, topic, from_time, to_time):
        for d in [from_time.date() + timedelta(days=x) for x in range(10)]:
            lim_f = datetime.combine(d, dt.time(0)).astimezone()
            lim_t = datetime.combine(d, dt.time(0)).astimezone()+timedelta(hours=24)
            f = max(min(from_time, lim_t), lim_f)
            t = max(min(to_time, lim_t), lim_f)
            if t-f:
                by_days.setdefault(d, {}).setdefault(activity, {}).setdefault(topic, timedelta())
                by_days[d][activity][topic] += t-f

    with open(filename, 'r') as f:
        data = [l.split('\t') for l in f.read().split('\n') if l]
        total_time = {}
        topics = {}
        for x, y in zip(data, data[1:]):
            activity = x[1]
            if len(x) >= 2 and x[2]:
                topics[x[1]] = x[2]
            if activity:
                divide_per_days(activity, topics.get(activity, "__default__"), datetime.fromisoformat(x[0]), datetime.fromisoformat(y[0]))
                t = datetime.fromisoformat(y[0]) - datetime.fromisoformat(x[0])
                total_time.setdefault(activity, timedelta())
                total_time[activity] += t
        for d, x in by_days.items():
            for activity, y in x.items():
                print(d, activity)
                for topic, time in y.items():
                    print(topic, time)
                print()


        for k, v in total_time.items():
            print(k, v)


