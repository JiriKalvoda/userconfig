#!/bin/bash
cd "$(dirname "$0")"

gcc tunel-server.c  -o ~/bin/tunel-server
