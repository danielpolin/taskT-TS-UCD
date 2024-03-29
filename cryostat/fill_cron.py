 #!/usr/bin/env python
#Author: Daniel Polin, Craig Lage

import matplotlib
matplotlib.use("Agg")
import numpy, time, datetime, sys, os, serial, struct, subprocess
from pylab import *
sys.path.append('/home/ccd/cryostat/Function_Files')
import Plots
import Email_Warning
import Lakeshore_335
import CryostatFill

date = datetime.datetime.now()
starttime=time.time()
print("Starting. Current time = "+date.strftime("%Y-%m-%d-%H:%M:%S"))
sys.stdout.flush()

Plots.CheckIfStillRunning() # Make sure there isn't another job still running.

cryostatfill = CryostatFill.CryostatFill('dummy')

#Fill the Cryostat if it needs to be filled
try:
    Plots.ReadTempsAndHandleCryostatFill(cryostatfill)
except Exception as e:
    print("Failure in Temp read or Cryostat Fill. Exception of type %s and args = \n"%type(e).__name__, e.args)    
    sys.stdout.flush()
    cryostatfill.StopFill() # In case of failure, make sure cryostat fill valve is closed

#Make the Temperature Plot
(TempTime, Temp_A, Temp_B) = Plots.ReadEndOfFile('/home/ccd/cryostat/Log_Files/temperature_log.dat',1500)
TempTime=[datetime.datetime.strptime(t,'%Y-%m-%d-%H:%M:%S') for t in TempTime]
Temp_A = [float(temp) for temp in Temp_A]
Temp_B = [float(temp) for temp in Temp_B]

(filltimes,filldurations) = Plots.ReadEndOfFile('/home/ccd/cryostat/Log_Files/fill_log.dat',100)
filltimes=[datetime.datetime.strptime(t,'%Y-%m-%d-%H:%M:%S') for t in filltimes]
filldurations = [float(duration) for duration in filldurations]

dewartimes=Plots.ReadEndOfFile('/home/ccd/cryostat/Log_Files/dewarfill_log.dat',100)
dewartimes=[datetime.datetime.strptime(t,'%Y-%m-%d-%H:%M:%S') for t in dewartimes[0]]

Plots.MakeTemperaturePlot(TempTime, Temp_A, Temp_B, filltimes, filldurations, dewartimes)

# Delete file which indicates we are still running.
command = "rm /home/ccd/cryostat/Log_Files/CronStillRunning"
delfile = subprocess.Popen(command, shell=True)
subprocess.Popen.wait(delfile)

sys.stdout.flush()

#upload the temperature graph to the webpage
command ='scp /home/ccd/cryostat/temperature_graph.png lsst@emerald.physics.ucdavis.edu:/var/www/html/storm/temperature_graph.png'
copygraph = subprocess.Popen(command, shell=True)
subprocess.Popen.wait(copygraph)

endtime=time.time()
elapsed = endtime-starttime
finaltime=datetime.datetime.now()
print("Current time = "+ finaltime.strftime("%Y-%m-%d-%H:%M:%S"))
print("Done. Elapsed time = "+str(elapsed))
