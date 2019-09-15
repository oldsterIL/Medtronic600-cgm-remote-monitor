#!/bin/bash

file_status=/tmp/status.txt

lsusb | grep "1a79:6210" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # Flash enable
    if [ -f "$file_status" ]; then
        # file found, send sms
        echo "Device found" > /var/spool/gammu/outbox/OUT+79-YOUR-PHONE.txt
        rm -f $file_status
    fi
else
    # Flash disable!!!
    if [ ! -f "$file_status" ]; then
        # file not found, send sms
        echo "No device!!!" > /var/spool/gammu/outbox/OUT+79-YOUR-PHONE.txt
        echo "no device" > $file_status
    fi
fi
