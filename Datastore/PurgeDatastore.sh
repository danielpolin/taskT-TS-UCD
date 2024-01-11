#!/bin/bash
cd /home/ccd/Data_logging/Datastore/
python3 Purge_Datastore.py 1>> /mnt/10TBHDD/data/logs/DataStorePurge.log 2>> /mnt/10TBHDD/data/logs/DataStorePurge.log&

