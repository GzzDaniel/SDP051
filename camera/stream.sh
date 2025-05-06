/usr/bin/libcamera-vid \
    -t 0 \
    --width 1280 --height 720 \
    --inline \
    --vflip --hflip \
    --flush \
    --nopreview \
    -o - | \
/usr/bin/ffmpeg \
    -re \
    -use_wallclock_as_timestamps 1 \
    -f h264 \
    -thread_queue_size 4096 \
    -i - \
    -c:v copy \
    -an \
    -f flv \
    "rtmp://a.rtmp.youtube.com/live2/jk5j-4wme-qzdk-wqd3-34ut" \
    -loglevel warning \
    -stats