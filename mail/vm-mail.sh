#!/bin/bash
set -ueo pipefail


x="$(vm  extended_name "${1:-+}")"
id=$(echo "$x" | head -n1)
user=$(echo "$x" | head -n2 | tail -n1)

echo $user@$id

vm ssh $user@$id -- -- bin/unzip-mail - --output=mail "${@:2}"
vm vncapp $user@$id -- 'chromium --new-window mail/page/index.html'
