#!/bin/bash
cd /home/ccd/cryostat/
python fill_cron.py 1>> Log_Files/AutoFill.log 2>> Log_Files/AutoFill.log&

