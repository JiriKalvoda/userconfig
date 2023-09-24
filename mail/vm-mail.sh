
x=$(vm  extended_name ${1:+})
name=$(echo "$x" | head -n2 | tail -n1)
user=$(echo "$x" | head -n1)


vm ssh $user@$name unzip-mail - --output=mail
vm vncapp $user@$name chromium --new-window mail/page/index.html
