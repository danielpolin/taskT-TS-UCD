import datetime
import Tkinter as tk
import tkMessageBox
import random
root = tk.Tk()
root.withdraw()
try:
    f = open('/home/ccd/cryostat/Log_Files/dewarfill_log.dat','a')
    now=datetime.datetime.now()
    written=now.strftime("%Y-%m-%d-%H:%M:%S")+'\n'
    f.write(written)
    f.close()

    messagelist=('       Way to go champ!       ','          You did it!          ','  Thank you for your service!  ','Congratulations on your achievement!','       Have a gold star!       ',"       You're the best!       ",'You have nothing to lose but your chains!','          Stay cool!          ','This is the greatest day of my life!')
    index=random.randint(0,len(messagelist)-1)  
    tkMessageBox.showinfo('Dewar Fill Successfully Logged', messagelist[index]+'\nLog time: '+now.strftime("%Y-%m-%d-%H:%M:%S"))
except:
    tkMessageBox.showwarning('Dewar Fill Log Failed', 'Something went wrong with logging code!')
