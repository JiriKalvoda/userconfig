#!/bin/bash

d="$(mktemp -d)"
if [[ "$d" == "" ]]
then
	exit 1
fi

echo "Running chromium in $d"
echo

if [[ "$TMPCH_COLOR" != "" ]]
then
	mkdir $d/Default
#	cat > $d/Default/Preferences <<AMEN
#{
#  "extensions": {
#    "theme": {
#      "id": "ogpbofebdcjdefeaglkbdhoappklpblc",
#      "pack": "$d/theme"
#    }
#  }
#}
#AMEN
	mkdir $d/theme
	cat > $d/theme/manifest.json <<AMEN
{
  "manifest_version": 3,
  "name": "${TMPCH_THEME_NAME:-Color variant theme}",
  "version": "1.0",
  "description": "Color variant theme",
  "theme": {
    "colors": {
      "frame": [$TMPCH_COLOR]
    }
  }
}
AMEN
	color_args=--load-extension=$d/theme
fi

#timeout 1 chromium --disable-features=ExtensionManifestV2Unsupported,ExtensionManifestV2Disabled --user-data-dir="$d" "$@"
chromium --disable-features=ExtensionManifestV2Unsupported,ExtensionManifestV2Disabled --user-data-dir="$d" $color_args "$@"
rm -r "$d"
