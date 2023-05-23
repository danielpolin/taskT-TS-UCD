import numpy, time, datetime, sys, os, serial, struct, subprocess
import Tkinter as tk
import tkMessageBox
import random
root = tk.Tk()
root.withdraw()
sys.path.append('/home/ccd/cryostat/Function_Files/')
import CryostatFill
import Plots

cryostatfill = CryostatFill.CryostatFill('dummy')
try:
	messagelist=('       Way to go champ!       ','          You did it!          ','  Thank you for your service!  ','Congratulations on your achievement!','       Have a gold star!       ',"       You're the best!       ",'You have nothing to lose but your chains!','          Stay cool!          ','This is the greatest day of my life!')
	index=random.randint(0,len(messagelist)-1)
	Plots.ManualFill(cryostatfill)
	tkMessageBox.showinfo('Cryostat Manual Fill Successful', messagelist[index])
except Exception as e:
	try:
		cryostatfill.StopFill()
		tkMessageBox.showwarning('Cryostat Manual Fill Failed', 'Something went wrong. Valve successfully closed.')
	except:
		tkMessageBox.showwarning('Cryostat Manual Fill Failed', 'FAILED TO CLOSE VALVE. Go unplug the valve and Phidget!')
	
