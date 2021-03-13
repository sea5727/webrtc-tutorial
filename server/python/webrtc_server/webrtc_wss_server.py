import random
import ssl
import websockets
import asyncio
import os
import sys
import json
import argparse
import pathlib

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC
gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp


def check_plugins():
    needed = ["opus", "vpx", "nice", "webrtc", "dtls", "srtp", "rtp",
              "rtpmanager", "videotestsrc", "audiotestsrc"]
    missing = list(filter(lambda p: Gst.Registry.get().find_plugin(p) is None, needed))
    if len(missing):
        print('Missing gstreamer plugins:', missing)
        return False
    return True


class WebRTCServer:
    def __init__(self, server, port):
        '''
        '''
        self.port = port
        self.server = server
        self.pipe = None
        self.webrtc = None 
        self.ssl_context = None

    async def serve(self):
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        public_pem = pathlib.Path('/home/ysh8361/workspace/webrtc/webrtc-tutorial/public.crt')
        private_pem = pathlib.Path('/home/ysh8361/workspace/webrtc/webrtc-tutorial/private.key')
        self.ssl_context.load_cert_chain(public_pem, private_pem)
        print(f'type: {type(self.port)}, port:{self.port}')
        self.server = websockets.serve(self.on_message, "0.0.0.0", self.port, ssl=self.ssl_context)

    def start_pipeline(self, conn):
        '''
        '''
        self.pipe = Gst.Pipeline.new("player")
        self.webrtc = Gst.ElementFactory.make("webrtcbin", 'recv')
        self.webrtc.set_property('stun-server', 'stun://stun.l.google.com:19302')
        self.pipe.add(self.webrtc)

        self.webrtc.connect('pad-added', self.on_incoming_stream)
        self.webrtc.connect('on-ice-candidate', self.send_ice_candidate_message, conn)
        
        self.pipe.set_state(Gst.State.PLAYING)

    def on_incoming_stream(self, _, pad):
        '''
        '''
        print('on_incoming_stream')
        if pad.direction != Gst.PadDirection.SRC:
            return

        decodebin = Gst.ElementFactory.make('decodebin')
        decodebin.connect('pad-added', self.on_incoming_decodebin_stream)
        self.pipe.add(decodebin)
        decodebin.sync_state_with_parent()
        self.webrtc.link(decodebin)

    def send_ice_candidate_message(self, element, mlineindex, candidate, user_data):
        '''
        '''
        conn = user_data
        icemsg = json.dumps({'ice': {'candidate': candidate, 'sdpMLineIndex': mlineindex, 'sdpMid': mlineindex}})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(conn.send(icemsg))
        loop.close()


    def on_answer_created(self, promise, user_data, __):
        '''
        '''
        conn = user_data
        print('on_answer_created', user_data)
        promise.wait()
        reply = promise.get_reply()
        answer = reply['answer']
        promise = Gst.Promise.new()
        print('set-local-description', user_data)
        self.webrtc.emit('set-local-description', answer, promise)
        promise.interrupt()
        self.send_sdp_answer(conn, answer)

    def send_sdp_answer(self, conn, answer):
        '''
        '''
        print('send_sdp_answer')
        text = answer.sdp.as_text()
        print(f'{text}')
        msg = json.dumps({'sdp': {'type': 'answer', 'sdp': text}})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(conn.send(msg))
        loop.close()

    async def on_message(self, conn, path):
        while True:
            data = await conn.recv();
            print(f'{data}')
            datas = data.split(' ')
            if datas[0] == 'HELLO':
                await conn.send('HELLO')  
            elif datas[0] == 'SESSION':
                await conn.send('SESSION_OK')
            else:
                msg = json.loads(data)
                if 'sdp' in msg:
                    sdp = msg['sdp']
                    assert(sdp['type'] == 'offer')
                    sdp = sdp['sdp']
                    self.start_pipeline(conn)
                    print('set-remote-description')

                    res, sdpmsg = GstSdp.SDPMessage.new()
                    GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
                    offer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.OFFER, sdpmsg)
                    promise = Gst.Promise.new()
                    self.webrtc.emit('set-remote-description', offer, promise)
                    promise.interrupt()
                    
                    promise = Gst.Promise.new_with_change_func(self.on_answer_created, conn, None)
                    self.webrtc.emit('create-answer', None, promise)

                elif 'ice' in msg:
                    print('[RECV] ice:', msg)
                    ice = msg['ice']
                    candidate = ice['candidate']
                    sdpmlineindex = ice['sdpMLineIndex']
                    self.webrtc.emit('add-ice-candidate', sdpmlineindex, candidate)
                    
if __name__ == '__main__':
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help='wss listen port', default=9002)
    parser.add_argument('--server', help='Signalling server to connect to, eg "wss://127.0.0.1:8443"')
    args = parser.parse_args()

    s = WebRTCServer(args.server, args.port)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(s.serve())
    loop.run_until_complete(s.server)
    loop.run_forever()