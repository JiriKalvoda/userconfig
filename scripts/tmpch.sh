#!/bin/bash

d="$(mktemp -d)"
if [[ "$d" == "" ]]
then
	exit 1
fi

echo "Running firefox in $d"
echo

if [[ "$TMPCH_COLOR" != "" ]]
then
	# Firefox nemá CLI ekvivalent chromium --load-extension pro téma.
	# Rámeček/toolbar proto obarvíme přes userChrome.css v throwaway profilu.
	# TMPCH_COLOR se očekává jako CSS rgb() argument, tj. "R,G,B" (např. "255,0,0").
	mkdir -p "$d/chrome"
	cat > "$d/user.js" <<AMEN
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
AMEN
	cat > "$d/chrome/userChrome.css" <<AMEN
:root {
  --toolbar-bgcolor: rgb($TMPCH_COLOR) !important;
  --lwt-accent-color: rgb($TMPCH_COLOR) !important;
}
#navigator-toolbox {
  background-color: rgb($TMPCH_COLOR) !important;
}
AMEN
fi

#timeout 1 firefox --new-instance --profile "$d" "$@"
firefox --new-instance --profile "$d" "$@"
rm -r "$d"
