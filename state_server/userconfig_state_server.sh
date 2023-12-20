#!/bin/bash
set -ueo pipefail

dir=~/userconfig_state/$1

[[ -d $dir/state ]] && rm $dir/state -r
mkdir -p $dir/state 
cd $dir/state
tar --extract -f /dev/stdin
