#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin


confln resolv.conf /etc/
confln resolvconf.conf /etc/
confln dns.conf /etc/dnsmasq/
confln dns-in-2direct.conf /etc/dnsmasq/
confln dns-dnssec-in-2direct.conf /etc/dnsmasq/


init-service dnsmasq-dns root dnsmasq "--keep-in-foreground --conf-file=/etc/dnsmasq/dns.conf" ""
init-service -d dnsmasq-dns-in@ root ip "netns exec %i dnsmasq --keep-in-foreground --conf-file=/etc/dnsmasq/dns-in-%i.conf" ""
init-service -d dnsmasq-dns-dnssec-in@ root ip "netns exec %i dnsmasq --keep-in-foreground --conf-file=/etc/dnsmasq/dns-dnssec-in-%i.conf" ""

install_ok
