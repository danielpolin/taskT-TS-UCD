#This is the main script which should be called to focus the LSST beam Simulator.
#Daniel Polin 2023

import sys, subprocess
sys.path.append('/home/ccd/Focus/lib/')
import FocusFinder

subprocess.run('ccs-script lib/sphereOn.py',check=True, shell=True)

subprocess.run('ln -sf /home/ccd/Focus/lib/acquirefocus.py /home/ccd/ccs/etc/acquire.py',check=True, shell=True)
print("Symlink to aquire.py changed to focus version")

try:
    focus=FocusFinder.Focus_Finder()

    focus.find_focus()
except KeyboardInterrupt:
    print("Focusing failed. Turning off light.")

subprocess.run('ln -sf /home/ccd/ucd-scripts/lib/acquire.py /home/ccd/ccs/etc/acquire.py',check=True, shell=True)
print("Symlink to aquire.py changed to normal version")
subprocess.run('ccs-script lib/sphereOff.py',check=True, shell=True)

