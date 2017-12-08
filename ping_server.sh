#!/bin/sh
 
# -q quiet
# -c number of pings to perform
 
ping -q -c2 google.com > /dev/null
 
if [ $? -eq 0 ]
then
    echo "ok"
fi