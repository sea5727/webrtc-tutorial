import random
import ssl
import websockets
import asyncio
import os
import sys
import json
import argparse

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC
gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp

PIPELINE_DESC = '''
webrtcbin name=sendrecv bundle-policy=max-bundle stun-server=stun://stun.l.google.com:19302
 videotestsrc is-live=true pattern=ball ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay !
 queue ! application/x-rtp,media=video,encoding-name=VP8,payload=97 ! sendrecv.
 audiotestsrc is-live=true wave=red-noise ! audioconvert ! audioresample ! queue ! opusenc ! rtpopuspay !
 queue ! application/x-rtp,media=audio,encoding-name=OPUS,payload=96 ! sendrecv.
'''

from websockets.version import version as wsv

class WebRTCClient:
    def __init__(self, id_, peer_id, server):
        self.id_ = id_
        self.conn = None
        self.pipe = None
        self.webrtc = None
        self.peer_id = peer_id
        # self.server = server or 'wss://webrtc.nirbheek.in:8443'
        self.server = server or 'wss://192.168.0.34:9002'
        self.start_pipeline()

    async def connect(self):
        sslctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self.conn = await websockets.connect(self.server, ssl=sslctx)
        await self.conn.send('HELLO %d' % self.id_)

    async def setup_call(self):
        await self.conn.send('SESSION {}'.format(self.peer_id))

    def send_sdp_offer(self, offer):
        text = offer.sdp.as_text()
        print ('Sending offer:\n%s' % text)
        msg = json.dumps({'sdp': {'type': 'offer', 'sdp': text}})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send(msg))
        loop.close()

    def on_offer_created(self, promise, _, __):
        promise.wait()
        reply = promise.get_reply()
        offer = reply['offer']
        promise = Gst.Promise.new()
        # print('original offer sdp : ', offer.sdp.as_text())
        self.webrtc.emit('set-local-description', offer, promise)
        promise.interrupt()


        

    def on_negotiation_needed(self, element):
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, element, None)
        element.emit('create-offer', None, promise)

    def send_ice_candidate_message(self, _, mlineindex, candidate):
        icemsg = json.dumps({'ice': {'candidate': candidate, 'sdpMLineIndex': mlineindex}})
        # print('icemsg:', icemsg)
        # loop = asyncio.new_event_loop()
        # loop.run_until_complete(self.conn.send(icemsg))
        # loop.close()

    def on_incoming_decodebin_stream(self, _, pad):
        if not pad.has_current_caps():
            print (pad, 'has no caps, ignoring')
            return

        caps = pad.get_current_caps()
        assert (len(caps))
        s = caps[0]
        name = s.get_name()
        if name.startswith('video'):
            q = Gst.ElementFactory.make('queue')
            conv = Gst.ElementFactory.make('videoconvert')
            sink = Gst.ElementFactory.make('autovideosink')
            self.pipe.add(q, conv, sink)
            self.pipe.sync_children_states()
            pad.link(q.get_static_pad('sink'))
            q.link(conv)
            conv.link(sink)
        elif name.startswith('audio'):
            q = Gst.ElementFactory.make('queue')
            conv = Gst.ElementFactory.make('audioconvert')
            resample = Gst.ElementFactory.make('audioresample')
            sink = Gst.ElementFactory.make('autoaudiosink')
            self.pipe.add(q, conv, resample, sink)
            self.pipe.sync_children_states()
            pad.link(q.get_static_pad('sink'))
            q.link(conv)
            conv.link(resample)
            resample.link(sink)

    def on_incoming_stream(self, _, pad):
        if pad.direction != Gst.PadDirection.SRC:
            return

        decodebin = Gst.ElementFactory.make('decodebin')
        decodebin.connect('pad-added', self.on_incoming_decodebin_stream)
        self.pipe.add(decodebin)
        decodebin.sync_state_with_parent()
        self.webrtc.link(decodebin)

    def start_pipeline(self):
        self.pipe = Gst.parse_launch(PIPELINE_DESC)
        self.webrtc = self.pipe.get_by_name('sendrecv')
        
        self.webrtc.connect('on-ice-candidate', self.send_ice_candidate_message)
        self.webrtc.connect('pad-added', self.on_incoming_stream)
        self.pipe.set_state(Gst.State.PLAYING)

        offer = 'v=0\no=- 249052402997811464 2 IN IP4 127.0.0.1\ns=-\nt=0 0\na=group:BUNDLE 0 1\na=extmap-allow-mixed\na=msid-semantic: WMS\nm=audio 9 UDP/TLS/RTP/SAVPF 111 103 104 9 0 8 106 105 13 110 112 113 126\nc=IN IP4 0.0.0.0\na=rtcp:9 IN IP4 0.0.0.0\na=ice-ufrag:09iz\na=ice-pwd:TDNEa4DNQNu5vntI7paNKKgV\na=ice-options:trickle\na=fingerprint:sha-256 4F:12:50:51:FE:1A:76:0E:74:6D:79:31:DB:C0:E5:42:41:4F:AA:9D:AA:C9:29:AD:A2:49:6E:F3:AF:0F:3A:14\na=setup:actpass\na=mid:0\na=extmap:1 urn:ietf:params:rtp-hdrext:ssrc-audio-level\na=extmap:2 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time\na=extmap:3 http://www.ietf.org/id/draft-holmer-rmcat-transport-wide-cc-extensions-01\na=extmap:4 urn:ietf:params:rtp-hdrext:sdes:mid\na=extmap:5 urn:ietf:params:rtp-hdrext:sdes:rtp-stream-id\na=extmap:6 urn:ietf:params:rtp-hdrext:sdes:repaired-rtp-stream-id\na=sendrecv\na=rtcp-mux\na=rtpmap:111 opus/48000/2\na=rtcp-fb:111 transport-cc\na=fmtp:111 minptime=10;useinbandfec=1\na=rtpmap:103 ISAC/16000\na=rtpmap:104 ISAC/32000\na=rtpmap:9 G722/8000\na=rtpmap:0 PCMU/8000\na=rtpmap:8 PCMA/8000\na=rtpmap:106 CN/32000\na=rtpmap:105 CN/16000\na=rtpmap:13 CN/8000\na=rtpmap:110 telephone-event/48000\na=rtpmap:112 telephone-event/32000\na=rtpmap:113 telephone-event/16000\na=rtpmap:126 telephone-event/8000\nm=video 9 UDP/TLS/RTP/SAVPF 96 97 98 99 100 101 122 102 121 127 120 125 107 108 109 124 119 123 118 114 115 116 35\nc=IN IP4 0.0.0.0\na=rtcp:9 IN IP4 0.0.0.0\na=ice-ufrag:09iz\na=ice-pwd:TDNEa4DNQNu5vntI7paNKKgV\na=ice-options:trickle\na=fingerprint:sha-256 4F:12:50:51:FE:1A:76:0E:74:6D:79:31:DB:C0:E5:42:41:4F:AA:9D:AA:C9:29:AD:A2:49:6E:F3:AF:0F:3A:14\na=setup:actpass\na=mid:1\na=extmap:14 urn:ietf:params:rtp-hdrext:toffset\na=extmap:2 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time\na=extmap:13 urn:3gpp:video-orientation\na=extmap:3 http://www.ietf.org/id/draft-holmer-rmcat-transport-wide-cc-extensions-01\na=extmap:12 http://www.webrtc.org/experiments/rtp-hdrext/playout-delay\na=extmap:11 http://www.webrtc.org/experiments/rtp-hdrext/video-content-type\na=extmap:7 http://www.webrtc.org/experiments/rtp-hdrext/video-timing\na=extmap:8 http://www.webrtc.org/experiments/rtp-hdrext/color-space\na=extmap:4 urn:ietf:params:rtp-hdrext:sdes:mid\na=extmap:5 urn:ietf:params:rtp-hdrext:sdes:rtp-stream-id\na=extmap:6 urn:ietf:params:rtp-hdrext:sdes:repaired-rtp-stream-id\na=sendrecv\na=rtcp-mux\na=rtcp-rsize\na=rtpmap:96 VP8/90000\na=rtcp-fb:96 goog-remb\na=rtcp-fb:96 transport-cc\na=rtcp-fb:96 ccm fir\na=rtcp-fb:96 nack\na=rtcp-fb:96 nack pli\na=rtpmap:97 rtx/90000\na=fmtp:97 apt=96\na=rtpmap:98 VP9/90000\na=rtcp-fb:98 goog-remb\na=rtcp-fb:98 transport-cc\na=rtcp-fb:98 ccm fir\na=rtcp-fb:98 nack\na=rtcp-fb:98 nack pli\na=fmtp:98 profile-id=0\na=rtpmap:99 rtx/90000\na=fmtp:99 apt=98\na=rtpmap:100 VP9/90000\na=rtcp-fb:100 goog-remb\na=rtcp-fb:100 transport-cc\na=rtcp-fb:100 ccm fir\na=rtcp-fb:100 nack\na=rtcp-fb:100 nack pli\na=fmtp:100 profile-id=2\na=rtpmap:101 rtx/90000\na=fmtp:101 apt=100\na=rtpmap:122 VP9/90000\na=rtcp-fb:122 goog-remb\na=rtcp-fb:122 transport-cc\na=rtcp-fb:122 ccm fir\na=rtcp-fb:122 nack\na=rtcp-fb:122 nack pli\na=fmtp:122 profile-id=1\na=rtpmap:102 H264/90000\na=rtcp-fb:102 goog-remb\na=rtcp-fb:102 transport-cc\na=rtcp-fb:102 ccm fir\na=rtcp-fb:102 nack\na=rtcp-fb:102 nack pli\na=fmtp:102 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42001f\na=rtpmap:121 rtx/90000\na=fmtp:121 apt=102\na=rtpmap:127 H264/90000\na=rtcp-fb:127 goog-remb\na=rtcp-fb:127 transport-cc\na=rtcp-fb:127 ccm fir\na=rtcp-fb:127 nack\na=rtcp-fb:127 nack pli\na=fmtp:127 level-asymmetry-allowed=1;packetization-mode=0;profile-level-id=42001f\na=rtpmap:120 rtx/90000\na=fmtp:120 apt=127\na=rtpmap:125 H264/90000\na=rtcp-fb:125 goog-remb\na=rtcp-fb:125 transport-cc\na=rtcp-fb:125 ccm fir\na=rtcp-fb:125 nack\na=rtcp-fb:125 nack pli\na=fmtp:125 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42e01f\na=rtpmap:107 rtx/90000\na=fmtp:107 apt=125\na=rtpmap:108 H264/90000\na=rtcp-fb:108 goog-remb\na=rtcp-fb:108 transport-cc\na=rtcp-fb:108 ccm fir\na=rtcp-fb:108 nack\na=rtcp-fb:108 nack pli\na=fmtp:108 level-asymmetry-allowed=1;packetization-mode=0;profile-level-id=42e01f\na=rtpmap:109 rtx/90000\na=fmtp:109 apt=108\na=rtpmap:124 H264/90000\na=rtcp-fb:124 goog-remb\na=rtcp-fb:124 transport-cc\na=rtcp-fb:124 ccm fir\na=rtcp-fb:124 nack\na=rtcp-fb:124 nack pli\na=fmtp:124 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=4d001f\na=rtpmap:119 rtx/90000\na=fmtp:119 apt=124\na=rtpmap:123 H264/90000\na=rtcp-fb:123 goog-remb\na=rtcp-fb:123 transport-cc\na=rtcp-fb:123 ccm fir\na=rtcp-fb:123 nack\na=rtcp-fb:123 nack pli\na=fmtp:123 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=64001f\na=rtpmap:118 rtx/90000\na=fmtp:118 apt=123\na=rtpmap:114 red/90000\na=rtpmap:115 rtx/90000\na=fmtp:115 apt=114\na=rtpmap:116 ulpfec/90000\na=rtpmap:35 flexfec-03/90000\na=rtcp-fb:35 goog-remb\na=rtcp-fb:35 transport-cc\na=fmtp:35 repair-window=10000000\n'
        print('offer sdp : ' , offer)
        sdp = offer
        res, sdpmsg = GstSdp.SDPMessage.new()
        GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
        offer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.OFFER, sdpmsg)
        promise = Gst.Promise.new()
        self.webrtc.emit('set-remote-description', offer, promise)
        promise.interrupt()

        direction_a = GstWebRTC.WebRTCRTPTransceiverDirection.SENDONLY
        caps_a = Gst.caps_from_string("application/x-rtp,media=audio,encoding-name=OPUS,payload=111")
        direction_v = GstWebRTC.WebRTCRTPTransceiverDirection.SENDONLY
        caps_v = Gst.caps_from_string("application/x-rtp,media=video,encoding-name=VP8,payload=96")
        
        self.webrtc.emit('add-transceiver', direction_a, caps_a)
        self.webrtc.emit('add-transceiver', direction_v, caps_v)

        promise = Gst.Promise.new_with_change_func(self.on_answer_created, None, None)
        self.webrtc.emit('create-answer', None, promise)

    def on_answer_created(self, promise, user_data, __):
        '''
        '''
        conn = user_data
        print('on_answer_created')
        promise.wait()
        reply = promise.get_reply()
        answer = reply['answer']
        promise = Gst.Promise.new()
        print('answer sdp :', answer.sdp.as_text())
        print('set-local-description')
        self.webrtc.emit('set-local-description', answer, promise)
        promise.interrupt()
        # self.send_sdp_answer(conn, answer)



    def handle_sdp(self, message):
        assert (self.webrtc)
        msg = json.loads(message)
        if 'sdp' in msg:
            sdp = msg['sdp']
            assert(sdp['type'] == 'answer')
            sdp = sdp['sdp']
            print ('Received answer:\n%s' % sdp)
            res, sdpmsg = GstSdp.SDPMessage.new()
            GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
            answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
            promise = Gst.Promise.new()
            self.webrtc.emit('set-remote-description', answer, promise)
            promise.interrupt()
        elif 'ice' in msg:
            ice = msg['ice']
            candidate = ice['candidate']
            sdpmlineindex = ice['sdpMLineIndex']
            self.webrtc.emit('add-ice-candidate', sdpmlineindex, candidate)

    def close_pipeline(self):
        self.pipe.set_state(Gst.State.NULL)
        self.pipe = None
        self.webrtc = None

    async def loop(self):
        assert self.conn
        async for message in self.conn:
            print(f'message:{message}')
            if message == 'HELLO':
                await self.setup_call()
            elif message == 'SESSION_OK':
                self.start_pipeline()
            elif message.startswith('ERROR'):
                print (message)
                self.close_pipeline()
                return 1
            else:
                self.handle_sdp(message)
        self.close_pipeline()
        return 0

    async def stop(self):
        if self.conn:
            await self.conn.close()
        self.conn = None


def check_plugins():
    needed = ["opus", "vpx", "nice", "webrtc", "dtls", "srtp", "rtp",
              "rtpmanager", "videotestsrc", "audiotestsrc"]
    missing = list(filter(lambda p: Gst.Registry.get().find_plugin(p) is None, needed))
    if len(missing):
        print('Missing gstreamer plugins:', missing)
        return False
    return True


if __name__=='__main__':
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument('peerid', help='String ID of the peer to connect to')
    parser.add_argument('--server', help='Signalling server to connect to, eg "wss://127.0.0.1:8443"')
    parser.add_argument('--port', default=9002)
    args = parser.parse_args()

    s = WebRTCClient(args.peerid, args.server, args.port)
    
    loop = asyncio.get_event_loop()
    loop.run_forever()

    # loop.run_until_complete(c.connect())
    # res = loop.run_until_complete(c.loop())
    sys.exit()

