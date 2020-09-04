# webrtc-tutorial peer 단말


1.  카메라 얻기 ( getUserMedia )
   - getUserMedia 를 사용하면 video, audio 장치와 연결하여 stream 객체를 얻을 수 있다
   - 자세한건 그때그때 doc을 참조하면 될듯싶다.
2. WebRTC 연결 ( RTCPeerConnection )
   - RTCPeerConnection 를 사용하여 WebRTC 관련 커넥션을 정의할 수 있다.
   - new RTCPeerConnection( [configuration ] ) 로 선언되는데, configuration 은 하나씩 테스트해보면 좋을것같다.
     - iceServer : 명시하지 않으면 자체 ICE 서버로 진행해야 하며, 자체 ICE서버가 없는경우 로컬 피어와 연결이 제한된다. 
3. 미디어 연결

