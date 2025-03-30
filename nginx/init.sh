#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
is_sysconfig=true
install_begin

confln filter_ngix_config.py /etc/nginx/
confln nginx.conf /etc/nginx/
confln blattes_client.crt /etc/nginx/
confln default_host /etc/nginx/
confln sites.d/default_host /etc/nginx/sites.d/ d
confln default_host.d/ifconfig /etc/nginx/default_host.d/ d
confln default_host.d/users /etc/nginx/default_host.d/ d
confln filter_ngix_config.conf /etc/systemd/system/nginx.service.d/ c

mkdir -p /etc/nginx/sites_checked.d
mkdir -p /etc/nginx/default_host_checked.d


install_ok
