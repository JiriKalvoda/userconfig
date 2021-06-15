#!/bin/bash
cd "$(dirname "$0")"

confln snapshoter ~/bin/
confln "snapshoter.devices-$(hostname)" ~/snapshoter.devicespec
