#!/bin/bash
set -e

API_IP_1="${api_ip_1}"
API_IP_2="${api_ip_2}"

sudo dnf update -y
sudo dnf install -y haproxy

sudo bash -c "cat > /etc/haproxy/haproxy.cfg << EOF
global
    log /dev/log local0
    maxconn 4096
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms

frontend http-in
    bind *:80
    default_backend api-servers

backend api-servers
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server api1 $API_IP_1:8000 check inter 5s
    server api2 $API_IP_2:8000 check inter 5s

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
EOF"

sudo systemctl enable haproxy
sudo systemctl start haproxy

echo "HAProxy setup complete"
