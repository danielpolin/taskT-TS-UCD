import matplotlib
matplotlib.use("Agg")
import numpy, time, datetime, sys, os, serial, struct, subprocess
from pylab import *

sys.path.append('/home/ccd/cryostat/Function_Files/')
#import Email_Warning
import CryostatFill20230509
import Plots

cryostatfill = CryostatFill20230509.CryostatFill('dummy')

cryostatfill.StartFill()
