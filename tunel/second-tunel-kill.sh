#!/bin/bash

cd ~/.tunel
cmdprefix=second-tunel

. config-default
. config

killall $cmdprefix-echo -q
killall $cmdprefix-ssh -q
