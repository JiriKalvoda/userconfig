#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln filter_ngix_config.py /etc/nginx/
confln nginx.conf /etc/nginx/
confln blattes_client.crt /etc/nginx/
confln sites.d/default_host /etc/nginx/sites.d/ d
confln default_host.d/ifconfig /etc/nginx/default_host.d/ d

install_ok
