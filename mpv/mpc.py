#!/usr/bin/env python3
import sys, os
import subprocess
import tempfile
from pathlib import Path

from lib import *
import utils

def read(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


identificator_to_parse = sys.argv[1]

identificators = []

i = 0
while i < len(identificator_to_parse):
    if identificator_to_parse[i] in IDENTIFICATORS:
        identificators.append([IDENTIFICATORS[identificator_to_parse[i]]])
    i += 1

class Player:
    def __init__(self, pointer_dir):
        self.pointer_dir = pointer_dir
        self.identificators = read(Path(pointer_dir, "identificators")).split("\n")

    def socket_path(self):
        return Path(self.pointer_dir, "socket")

    def debug_print(self):
        print(self)
        print(self.identificators)
        print()

def parsse_player(pointer_dir):
    if read(Path(pointer_dir, "status")) != "redy":
        return None
    player = Player(pointer_dir)

    return player

@utils.output_is_list
def load_players():
    for it in os.listdir(POINTERS_DIR):
        player = parsse_player(Path(POINTERS_DIR, it))
        if player is not None:
            yield player



all_players = load_players()

for i in all_players: i.debug_print()

selected_players = []

for ident in identificators:
    for p in all_players:
        if len(set(p.identificators).intersection(set(ident))):
            selected_players.append(p)
    if len(selected_players): break


print("Selected:")
for i in selected_players: i.debug_print()

subprocess.run(["socat", "-", load_players()[0].socket_path()])




