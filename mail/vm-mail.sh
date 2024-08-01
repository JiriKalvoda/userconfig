#!/bin/bash
set -ueo pipefail


vm="$(vm eval "${1:-+}")"

echo $vm

vm ssh $vm -- -- bin/unzip-mail - --output=mail "${@:2}"
vm vncapp $vm -- 'chromium --new-window mail/page/index.html'
