#!/bin/sh
 
# -q quiet
# -c number of pings to perform
FILE="/var/log/ping_server.log"
 
ping -q -c2 opinion.berkeley.edu > /dev/null
 
if [ $? -eq 0 ]
then
    echo "ok"
else
    DATE=`date '+%Y-%m-%d %H:%M:%S'`
    sudo echo "Server down at ${DATE}" > $FILE
fi