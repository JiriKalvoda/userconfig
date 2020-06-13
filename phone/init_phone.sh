#! /usr/bin/bash
cd "$(dirname "$0")"

cp sshd-start sshd-stop ~/../usr/bin/
chmod +x ~/../usr/sshd-start ~/../usr/sshd-stop
