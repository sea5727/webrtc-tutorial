# WebRTC

python3 ./simple-https-server 을 실행.




# webrtc-tutorial peer 단말

전체 순서는

getUserMedia -> RTCPeerConnection -> addTrack -> createOffer -> 


1. 카메라 얻기 ( getUserMedia )

   - getUserMedia 를 사용하면 video, audio 장치와 연결하여 stream 객체를 얻을 수 있다.

   - 자세한건 그때그때 doc을 참조하면 될듯싶다.

     

2. WebRTC 연결 ( RTCPeerConnection )
   - RTCPeerConnection 를 사용하여 WebRTC 관련 커넥션을 정의할 수 있다.
   - new RTCPeerConnection( [configuration ] ) 로 선언되는데, configuration 은 하나씩 테스트해보면 좋을것같다.
     
     - iceServer : 명시하지 않으면 자체 ICE 서버로 진행해야 하며, 자체 ICE서버가 없는경우 로컬 피어와 연결이 제한된다.  
     
       

3. addTrack

   - peer로 전달할 stream의 media track 을 PeerConnection(pc) 에 추가한다. 즉

     1번에서 사용한 api로 얻은 stream의 Track을 2.에서 얻은 PeerConnection(pc) 에 추가한다. 

     

4. SDP Offer 메시지 생성

   - createOffer를 사용하여 sdp를 생성한다.

     

5. SDP Offer

