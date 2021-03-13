#!/usr/bin/python
# taken from http://www.piware.de/2011/01/creating-an-https-server-in-python/
# generate server.xml with the following command:
#    openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
# run as follows:
#    python simple-https-server.py
# then in your browser, visit:
#    https://localhost:4443

import BaseHTTPServer, SimpleHTTPServer
import ssl

home = '/home/ysh8361/workspace/webrtc/webrtc-tutorial'
port = 4444
print('open port :', port)
httpd = BaseHTTPServer.HTTPServer(('0.0.0.0', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket (httpd.socket, certfile=home + '/public.crt', keyfile=home + '/private.key', server_side=True)
# httpd.socket = ssl.wrap_socket (httpd.socket, certfile='/home/ysh8361/workspace/bin/server.pem', server_side=True)
httpd.serve_forever()
