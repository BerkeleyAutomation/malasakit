#!/bin/sh
 
FILE="/var/log/ping_server.log"
URL="https://opinion.berkeley.edu/pcari/en/landing/"

# Captures the status code of the request
OUTPUT=$(curl --write-out %{http_code} --silent --output /dev/null "$URL")

if [ $OUTPUT == 200 ]
then
    echo "ok"
else
    DATE=`date '+%Y-%m-%d %H:%M:%S'`
    sudo echo "Server down at ${DATE}" >> $FILE
fi

