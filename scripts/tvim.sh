#!/bin/bash


# if [[ "$EDITOR" != "" ]]
# then
# 	if which nvim >/dev/null 2>/dev/null
# 	then
# 		EDITOR=nvim
# 	else
# 		EDITOR=vim
# 	fi
# fi

terminal -e vim "$@"
