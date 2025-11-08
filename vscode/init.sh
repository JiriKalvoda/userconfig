#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln keybindings.json ~/.config/VSCodium/User/
confln settings.json ~/.config/VSCodium/User/

extensions="
asvetliakov.vscode-neovim
rooveterinaryinc.roo-cline
"
#leanprover.lean4
#ms-dotnettools.vscode-dotnet-runtime
#tamasfe.even-better-toml
#muhammad-sammy.csharp

for ext in $extensions
do
	r vscodium --install-extension $ext
done

install_ok
