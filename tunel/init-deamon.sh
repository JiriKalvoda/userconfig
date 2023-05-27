#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

install_begin

init-service tunel "$1" tunel
init-service -d second-tunel "$1" second-tunel d

install_ok
