#!/bin/bash

BACKUPLIST=/usr/local/backup/backup.list.txt
BACKUPSERVER=XXX.com
BACKUPEXCLUDELIST=/usr/local/backup/exclude.list.txt
DAYOFWEEK=`date +%a`

ssh -p 1964 -o stricthostkeychecking=no -i /usr/local/backup/id_backup $BACKUPSERVER -l databackup /usr/bin/logger "_____$HOSTNAME backup starting_____"

if [ "$DAYOFWEEK" = "Sun" ]
then
        /bin/nice -n 10 \
        rsync -LxqRaze 'ssh -p 1964 -o stricthostkeychecking=no -i /usr/local/backup/id_backup' \
        `cat $BACKUPLIST` \
        --exclude-from=$BACKUPEXCLUDELIST \
        --delete \
        databackup@$BACKUPSERVER:$HOSTNAME \
        2>/dev/null
else
        /bin/nice -n 10 \
        rsync -LxqRaze 'ssh -p 1964 -o stricthostkeychecking=no -i /usr/local/backup/id_backup' \
        `cat $BACKUPLIST` \
        --exclude-from=$BACKUPEXCLUDELIST \
        databackup@$BACKUPSERVER:$HOSTNAME \
        2>/dev/null
fi

ssh -p 1964 -o stricthostkeychecking=no -i /usr/local/backup/id_backup $BACKUPSERVER -l databackup /usr/bin/logger "_____$HOSTNAME backup complete_____"
