#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

confln suspender.py ~/bin/ -E
