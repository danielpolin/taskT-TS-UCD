#!/bin/bash
cd /home/ccd/Data_logging/MasterDataLog/
python3 MasterDataLog.py 1>> /mnt/10TBHDD/data/logs/MasterDataLog/cronjob.log 2>> /mnt/10TBHDD/data/logs/MasterDataLog/cronjoberrors.log&

