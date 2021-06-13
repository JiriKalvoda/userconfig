#!/bin/bash

cd ~/.tunel
cmdprefix=second-tunel

. config

killall $cmdprefix-echo -q
killall $cmdprefix-ssh -q
