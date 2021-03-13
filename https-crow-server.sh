#!/bin/sh
openssl genrsa -out https-crow-server-private.key 2048
openssl rsa -in https-crow-server-private.key -pubout -out https-crow-server-public.key
openssl req -new -key https-crow-server-private.key -out https-crow-server-private.csr -config https-crow-server.conf
openssl req -x509 -days 3650 -key https-crow-server-private.key -in https-crow-server-private.csr -out https-crow-server-private.crt  -config https-crow-server.conf -extensions req_ext
