#!/bin/bash
# writes epg data as json to stdout
# args: URL channel_name loops totaltime
# calculate curl  --maxtime to end in case of stalled connection
let maxtime=$4+20
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [[ "$5" == satip ]]
then
    CMD="ffmpeg  -hide_banner -fflags discardcorrupt -copyts -probesize 8000000 -rtsp_flags +satip_raw -i \"$1\" -enc_time_base -1 -max_muxing_queue_size 4096 -muxdelay 0 -ignore_unknown -map 0 -c copy -f data  -y -"
else
    CMD="curl --connect-timeout 20 --max-time $maxtime -s \"$1\""
fi
eval $CMD  | node "$DIR/epg_grap.js" "$2" "$3" "$4"
#exit ${PIPESTATUS[0]} #fails on ffmpeg, as it finds no media stream and throws an error code :-(
exit 0
# ~/PlayGround/ffmpeg-test/ffmpeg/ffmpeg  -hide_banner -fflags discardcorrupt -copyts -probesize 8000000 -rtsp_flags +satip_raw -i 'satip://192.168.1.99:554/?src=1&freq=11362&pol=h&ro=0.35&msys=dvbs2&mtype=8psk&plts=on&sr=22000&fec=23&pids=0,17,18' -enc_time_base -1 -max_muxing_queue_size 4096 -muxdelay 0 -ignore_unknown -map 0 -c copy -f data  -y -
