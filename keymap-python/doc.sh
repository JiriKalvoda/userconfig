
if [[ "$#" != "2" ]]
then
	echo "usage: $0 [souce-file.mk] [output file without extension]"
	exit 1
fi
dir="$(dirname "$(readlink -f "$0")")"

"$dir/tex.py" "$1" > "$2".tex && pdfcsplain "$2".tex
