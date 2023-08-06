pages=`qpdf --show-npages  "$1"`;
if [ $pages -eq 2 ]; then
		echo -e " ** [PsPdfTool]\tBuilding booklet (from $pages pages) as landscape split document"
	paperjam 'spaper(a4r,297mm,210mm) select{1 2 1 2} nup(2,1,paper=a4r)' "$1" "$2"
else
		echo -e " ** [PsPdfTool]\tBuilding booklet (from $pages pages) as booklet"
	paperjam 'nup(1,paper=a5) book nup(2,paper=a4)' "$1" "$2"
fi