pages=`qpdf --show-npages  "$1"`;
if [ $pages -eq 2 ]; then
		echo -e " ** [PsPdfTool]\tBuilding booklet (from $pages pages) as landscape split document"
	paperjam 'nup(2,paper=a4) rotate(90)' "$1" "$2"
else
		echo -e " ** [PsPdfTool]\tBuilding booklet (from $pages pages) as booklet"
	paperjam 'nup(1,paper=a5) book nup(2,paper=a4)' "$1" "$2"
fi
