sudo apt install v4l2loopback-dkms
sudo modprobe v4l2loopback devices=1 card_label="loopback 1" exclusive_caps=1,1,1,1,1,1,1,1

#for CamOn stream just forward rstp source
ffmpeg -r 10 -i rtsp://192.168.0.1:8080/video/h264 -f v4l2 /dev/video2

# for OBS, configure output to udp and then forward
ffmpeg -r 10 -i udp://localhost:2345 -f v4l2 /dev/video2

# select obs recording to udp
arbitray port on local ip:
udp://127.0.0.1:2345

# container format, a few of them work
mpegts MPEG-2 Transport Stream


