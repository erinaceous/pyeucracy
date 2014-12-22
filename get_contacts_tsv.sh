#!/bin/bash

if [ "$ECOST_USER" = "" ]; then
    echo '$ECOST_USER is unset.' > /dev/stderr
    exit 1
fi
if [ "$ECOST_PASSWORD" = "" ]; then
    echo '$ECOST_PASSWORD is unset.' > /dev/stderr
    exit 1
fi

curtime=`date '+%s'`
lastdate=`stat contacts.tsv | fgrep Modify | sed 's/^Modify: //g'`
lasttime=`date --date="$lastdate" '+%s'`
lasttime_plus_minute=`echo "$lasttime + 60" | bc`

if [ "$curtime" -gt "$lasttime_plus_minute" ]; then
    python2 get_contacts_tsv.py -u $ECOST_USER -p $ECOST_PASSWORD 1070 > contacts.tsv
fi
cat contacts.tsv
