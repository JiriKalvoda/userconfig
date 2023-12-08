#!/bin/bash
set -euo pipefail

tmp=$(mktemp --suffix=pdf)
pages=`qpdf --show-npages  "$1" || true`;
if [ $pages -eq 2 ]; then
		echo -e " ** [PsPdfTool]\tBuilding booklet (from $pages pages) as landscape split document"
	paperjam 'select{1, 2: rotate(180), 1: rotate(180), 2} rotate(90) nup(2,1, paper=a4) rotate(-90)' "$1" "$tmp"
	lp -o Duplex=DuplexTumble -o XROutputMode=HighResolution "$tmp" "${@:2}"
else
		echo -e " ** [PsPdfTool]\tBuilding booklet (from $pages pages) as booklet"
	paperjam 'nup(1,paper=a5) book nup(2,paper=a4)' "$1" "$tmp"
	lp -o Duplex=DuplexTumble -o XRFold=BiFoldStaple -o XROutputMode=HighResolution "$tmp" "${@:2}"
fi
