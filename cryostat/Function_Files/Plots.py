 #!/usr/bin/env python
#Author: Daniel Polin

import matplotlib
matplotlib.use("Agg")
import numpy, time, datetime, sys, os, serial, struct, subprocess, urllib2
from pylab import *

import Email_Warning
import Lakeshore_335
import CryostatFill
import CryostatConfig
#************************************* SUBROUTINES ***********************************************

def CheckIfFileExists(filename):
    """
    Check if a file exists.

    Args:
    - filename (str): The name of the file to check.

    Returns:
    - True if the file exists, False otherwise.
    """
    try:
        FileSize = os.path.getsize(filename)
        return True
    except (OSError, IOError):
        return False

def ReadEndOfFile(filename, n):
    """
    Retrieves the last n lines of a file.

    Args:
    - filename (str): The name of the file to read the end of.
    - n (int): The number of lines to retrieve.

    Returns:
    - Returns the last n columns as numpy arrays of strings.
    """
    proc=subprocess.Popen(['tail','-n',str(n),filename], stdout=subprocess.PIPE)
    soutput,sinput=proc.communicate()
    lines = soutput.decode().split('\n')
    lines.pop() # Strip last line, which is empty
    
    output=numpy.transpose([line.split() for line in lines])
    
    return output


def MakeTemperaturePlot(Time, Temp_A, Temp_B, filltimes, filldurations, dewartimes):

    Temp_to_Fill = CryostatConfig.Temp_to_Fill # This is the temp to trigger a fill
    now=datetime.datetime.now()
    tendaysago=now-datetime.timedelta(days=10)
    
    fig = plt.figure(1, figsize=(20,12))
    fig.patch.set_facecolor('white')
    now=datetime.datetime.now()
    if now-Time[-1] > datetime.timedelta(minutes=15):
        fig.suptitle("WARNING NOT UPDATING TEMPERATURE: Last Measurement: "+str(Time[-1]),color='r',fontsize=20)
    else:
        fig.suptitle("Last Measurement: "+str(Time[-1]))
        
    #plot cryostat temp      
    ax1=fig.add_subplot(4,2,1)
    ax1.plot(Time,Temp_A,'b',label='Cryostat Temperature')
    ax1.plot([tendaysago,now],[Temp_to_Fill,Temp_to_Fill],linestyle = 'dotted', color = 'red',label="Temperature to Trigger Cryostat Fill")
    TAmin=min(Temp_A)
    TAmax=max(Temp_A)
    TAtenth=(TAmax-TAmin)/10.0
    TAmin=TAmin-TAtenth
    TAmax=max(Temp_to_Fill,TAmax)+TAtenth
    ax1.plot([filltimes[0],filltimes[0]],[TAmin,TAmax],color='g',linestyle='dotted',label='Cryostat Filled')
    ax1.set_ylim(TAmin,TAmax)
    if Temp_A[-1]>Temp_to_Fill and Temp_A[-2]>Temp_to_Fill:
        ax1.set_title("WARNING!! CRYOSTAT TEMPERATURE HIGH!!",color='r',fontsize=20)
    else:
        ax1.set_title("Cryostat Cold Plate Temperature: "+str(Temp_A[-1])+"$^\circ$C")
    ax1.set_xlim(tendaysago,now)
    ax1.set_xlabel("Date and Time")
    ax1.set_ylabel("Cryostat Temperature ($^\circ$C)")
    ax1.legend(loc='upper left')

    #plot CCD Temp
    ax2=fig.add_subplot(4,2,3)
    ax2.plot(Time,Temp_B,'r',label='CCD Temperature')
    TBmin=min(Temp_B)
    TBmax=max(Temp_B)
    TBtenth=(TBmax-TBmin)/10.0
    TBmin=TBmin-TBtenth
    TBmax=TBmax+TBtenth
    if len(filltimes)>20:
        for i in range(20):
            ax1.plot([filltimes[-i-1], filltimes[-i-1]],[TAmin, TAmax],color='g',linestyle = 'dotted')
            ax2.plot([filltimes[-i-1], filltimes[-i-1]],[TBmin, TBmax],color='g',linestyle = 'dotted')
    else:
        for i in filltimes:
            ax1.plot([i, i],[TAmin, TAmax],color='g',linestyle = 'dotted')
            ax2.plot([i, i],[TBmin, TBmax],color='g',linestyle = 'dotted')
    ax2.plot([filltimes[0],filltimes[0]],[TBmin,TBmax],color='g',linestyle='dotted',label='Cryostat Filled')
    ax2.set_xlabel("Date and Time")
    ax2.set_ylabel("CCD Temperature ($^\circ$C)")
    if Temp_B[-1]>-99.0:
        ax2.set_title("WARNING!! CCD TEMPERATURE HIGH!!",color='r',fontsize=20)
    else:
        ax2.set_title("CCD Temperature: "+str(Temp_B[-1])+"$^\circ$C")
    ax2.set_ylim(TBmin,TBmax)
    ax2.set_xlim(tendaysago,now)
    ax2.legend(loc='upper left')
    
    #plot cryostat fill durations vs time
    durmin=min(filldurations)
    durmax=max(filldurations)
    durtenth=(durmax-durmin)/10.0
    durmin=durmin-durtenth
    durmax=durmax+durtenth
    ax3=fig.add_subplot(4,2,2)
    ax3.plot(filltimes,filldurations,'go',label='Cryostat Fill Durations')
    ax3.set_xlabel("Date and Time")
    ax3.set_ylabel("Cryostat Fill Duration (s)")
    ax3.set_title("Cryostat last filled at: "+str(filltimes[-1]))
    ax3.set_ylim(durmin,durmax)
    ax3.legend(loc='upper left')
    
    #plot histogram of fill durations
    ax4=fig.add_subplot(4,2,4)
    ax4.hist(filldurations,color='g',edgecolor='k',linewidth=1,alpha=0.75)
    ax4.set_xlabel("Cryostat fill durations (s)")
    ax4.set_ylabel("Count")
    ax4.set_title("Median Cryostat Fill Time: "+str("{:.2f}".format(numpy.median(filldurations)))+'s')
    
    #plot time between cryostat fills
    timebetweenfills=[]
    for i in range(len(filltimes)-1):
    	diff=filltimes[i+1]-filltimes[i]
    	timebetweenfills.append(diff)
    ax5=fig.add_subplot(4,2,5)
    timebetweenfills=[tbf.total_seconds()/3600.0 for tbf in timebetweenfills]
    ax5.plot(filltimes[1:],timebetweenfills,'mo',label='Hours Between Cryostat Fills')
    diffmin=min(timebetweenfills)
    diffmax=max(timebetweenfills)
    difftenth=(diffmax-diffmin)/10.0
    diffmin=diffmin-difftenth
    diffmax=diffmax+difftenth
    if len(dewartimes)>20:
        for i in range(20):
            ax3.plot([dewartimes[-i-1], dewartimes[-i-1]],[durmin, durmax],color='c',linestyle = 'dotted',)
            ax5.plot([dewartimes[-i-1], dewartimes[-i-1]],[diffmin, diffrmax],color='c',linestyle = 'dotted',)
    else:
        for i in dewartimes:
            ax3.plot([i, i],[durmin, durmax],color='c',linestyle = 'dotted')
            ax5.plot([i, i],[diffmin, diffmax],color='c',linestyle = 'dotted')
    ax3.plot([dewartimes[0],dewartimes[0]],[TAmin,TAmax],color='c',linestyle='dotted',label='Dewar Filled')
    ax5.plot([dewartimes[0],dewartimes[0]],[TAmin,TAmax],color='c',linestyle='dotted',label='Dewar Filled')
    ax5.set_xlabel("Date and Time")
    ax5.set_ylim(diffmin,diffmax)
    ax5.set_ylabel("Time Between Cryostat Fills (hr)")
    ax5.legend(loc='upper left')

    #plot histogram of time between cryostat fills                                                      
    ax6=fig.add_subplot(4,2,7)
    ax6.hist(timebetweenfills,color='m',edgecolor='k',linewidth=1,alpha=0.75)
    ax6.set_xlabel("Time between cryostat fills (hr)")
    ax6.set_ylabel("Count")
    medianfilltime=numpy.median(timebetweenfills)
    ax6.set_title("Median Time Between Cryostat Fills: "+str("{:.1f}".format(medianfilltime))+'hr')
    
    timetillcryofill=datetime.timedelta(hours=medianfilltime)-(now-filltimes[-1])
    cryostd=numpy.std(timebetweenfills)
    ax5.set_title("Cryostat will fill in "+str('{:.1f}'.format(timetillcryofill.total_seconds()/3600.0))+"$\pm$"+str('{:.1f}'.format(cryostd))+"hr")
    
    #plot time between dewar fills
    timebetweendewar=[]
    for i in range(len(dewartimes)-1):
        diff=dewartimes[i+1]-dewartimes[i]
        timebetweendewar.append(diff)
    timebetweendewar=[tbf.total_seconds()/86400.0 for tbf in timebetweendewar]
    ax7=fig.add_subplot(4,2,6)
    ax7.plot(dewartimes[1:],timebetweendewar,'co',label='Days Between Dewar Fills')
    fillsbetweendewar=[]
    filltimes=np.array(filltimes)
    dewartimes=np.array(dewartimes)
    for dewarfill in range(len(dewartimes)-1):
        betweentimes=filltimes[filltimes>dewartimes[dewarfill]]
        betweentimes=betweentimes[betweentimes<dewartimes[dewarfill+1]]
        fillsbetweendewar.append(len(betweentimes))
    fillssincelastdewar=len(filltimes[filltimes>dewartimes[-1]])
    ax7.plot(dewartimes[1:],fillsbetweendewar,'go',label='Cryostat Fills Between Dewar Fills')
    ax7.set_xlabel("Date and Time Dewar Filled")
    ax7.set_ylabel("Number Between Dewar Fills \n(days/Cryostat Fills)")
    ax7.legend(loc='upper left')

    #plot histogram of times between dewar fills
    ax8=fig.add_subplot(4,2,8)
    binmin=min(min(fillsbetweendewar),min(timebetweendewar))
    binmax=max(max(fillsbetweendewar),max(timebetweendewar))
    binhund=(binmax-binmin)/100.0
    bins=np.linspace(binmin-binhund,binmax+binhund,10)
    ax8.hist(fillsbetweendewar,bins=bins,color='g',edgecolor='k',linewidth=1,alpha=0.5,label='Cryostat Fills Between Dewar Fills')
    ax8.hist(timebetweendewar,bins=bins-binhund,color='c',edgecolor='k',linewidth=1,alpha=0.5,label='Days Between Dewar Fills')
    ax8.set_xlabel("Time between Dewar fills (days)")
    ax8.set_ylabel("Count")
    mediandewar=numpy.median(timebetweendewar)
    mediancryostatfills=numpy.median(fillsbetweendewar)
    ax8.set_title("Median Time Between Dewar Fills: "+str("{:.1f}".format(mediandewar))+'days or '+str("{:.0f}".format(mediancryostatfills))+' Cryostat Fills')
    timetilldewarfill=(datetime.timedelta(days=mediandewar)-(now-dewartimes[-1])).total_seconds()/86400.0
    ax8.legend(loc='upper left')
    if timetilldewarfill<0:
        ax7.set_title("Time To Fill the Dewar!",color='r',fontsize=20)
    else:
        dewarstd=numpy.std(timebetweendewar)
        ax7.set_title("Fill the Dewar in "+str('{:.1f}'.format(timetilldewarfill))+"$\pm$"+str('{:.1f}'.format(dewarstd))+' days or '+str("{:.0f}".format(mediancryostatfills-fillssincelastdewar))+' Cryostat Fills')
    plt.tight_layout(rect=[0,0.03,1,0.95])
    savefig("/home/ccd/cryostat/temperature_graph.png")
    return

def CheckIfStillRunning():
    # This checks if the last cron job is still running.
    # We don't want to keep launching jobs if the last one has hung up
    if CheckIfFileExists("/home/ccd/cryostat/Log_Files/CronStillRunning"):
        print("Cron Job still running. Quitting\n")
        sys.stdout.flush()
        file = open('/home/ccd/cryostat/Log_Files/CronStillRunning','r')
        line = file.readline()
        file.close()
        lastminute = int(line.split()[4].split(':')[1])
        currentminute = datetime.datetime.now().minute
        if currentminute - lastminute < 15:
            # Only send a warning the first time it fails so as not to spam inboxes.
            Warning('Cryostat cron job appears to have stopped running')
    file = open('/home/ccd/cryostat/Log_Files/CronStillRunning','w')
    file.write("Job started at "+str(datetime.datetime.now())+" is still running\n")
    file.close()
    return

def ReadTempsAndHandleCryostatFill(cryostatfill):
    # Reads the temperatures and manages the Cryostat fill
    lake = Lakeshore_335.Lakeshore('dummy')
    lake.Initialize_Serial()
    lake.Read_Temp()
    NumTries = 0
    # Added the following loop to prevent occasional bogus 999.0 readings
    while lake.Temp_A > 900.0 and NumTries < 5:
        time.sleep(0.5)
        lake.Read_Temp()
        NumTries += 1

    date = datetime.datetime.now()
    out = date.strftime("%Y-%m-%d-%H:%M:%S")+' '+str(lake.Temp_A)+' '+ str(lake.Temp_B)+'\n'
    file = open('/home/ccd/cryostat/Log_Files/temperature_log.dat', 'a')
    file.write(out)
    file.close()

    # Cryostat Autofill
    # This file has the parameters that control the autofill
    Cryostat_is_Cold = CryostatConfig.Cryostat_is_Cold
    # Change this flag to turn off automatic Cryostat fill and E-Mail warnings
    # 1 = Autofill enabled; 0 = autofill disabled
    Temp_to_Fill = CryostatConfig.Temp_to_Fill # This is the temp to trigger a fill
    Min_Fill_Time = CryostatConfig.Min_Fill_Time # This is the minimum fill time
    Fill_Time_Limit = CryostatConfig.Fill_Time_Limit # This is the maximum fill time
    Overflow_Temp_Limit = CryostatConfig.Overflow_Temp_Limit
    # This is the temp on the overflow monitor that stops the fill

    if Cryostat_is_Cold == 1 and lake.Temp_A > Temp_to_Fill:
        (TempTime, Temp_A, Temp_B) = ReadEndOfFile('/home/ccd/cryostat/Log_Files/temperature_log.dat', 2)
        if Temp_A[0] > Temp_to_Fill:
            lake.Read_Temp()
            NumTries = 0
            # Added the following loop to prevent occasional bogus 999.0 readings
            while lake.Temp_A > 900.0 and NumTries < 5:
                time.sleep(0.5)
                lake.Read_Temp()
                NumTries += 1
            if lake.Temp_A > Temp_to_Fill:
                # This sequence ensures that a fill only happens if
                # we have three readings in a row over the set point.
                # Now we also check that a fill has not occurred in the last 3 hours
                filltime, fillduration = ReadEndOfFile('/home/ccd/cryostat/Log_Files/fill_log.dat', 1) # Get last fill
                lastfill=datetime.datetime.strptime(filltime[0],'%Y-%m-%d-%H:%M:%S')
                if datetime.datetime.now()-lastfill>datetime.timedelta(hours=3):
                    start_fill_status = cryostatfill.StartFill()
                    time.sleep(0.1)
                    if start_fill_status:
                        time.sleep(0.1)
                        startfill = time.time()
                        elapsed = 0.0
                        temp = Overflow_Temp_Limit + 1.0
                        difftemp = 0.0
                        overflowfile = open('/home/ccd/cryostat/Log_Files/overflow_log.dat','a')
                        time.sleep(0.1)
                        # while elapsed < Fill_Time_Limit and difftemp < 0.8 and temp > Overflow_Temp_Limit: OLD
                        while elapsed < Min_Fill_Time or (elapsed < Fill_Time_Limit and temp > Overflow_Temp_Limit):
                            # Stop the fill when we reach time limit or detect LN2 overflow
                            # or detect that the valve is no longer open (open:state=True)
                            lasttemp = temp
                            [state, temp] = cryostatfill.MeasureOverFlowTemp()
                            difftemp = lasttemp - temp
                            # We will terminate the fill if the temp reading drops below Overflow_Temp_Limit and Min_Fill_Time is exceeded.
                            line = date.strftime("%Y-%m-%d-%H:%M:%S")+' '+str(temp)+'\n'
                            overflowfile.write(line)
                            elapsed = time.time() - startfill
                            if state:
                                valve_state = "Open"
                            if not state:
                                # Break out of the loop if the valve doesn't stay open
                                valve_state = "Closed"
                                break
                            time.sleep(0.25)
                        if state:
                            cryostatfill.LogFill(fill_time=elapsed)
                        print("Terminated fill loop. Elapsed = %f, Overflow temp = %f, Valve state = %s\n"%(elapsed,temp,valve_state))
                        sys.stdout.flush()
                        overflowfile.close()
                    stop_fill_status = cryostatfill.StopFill()
                    NumTries = 0
                    while not stop_fill_status and NumTries < 5: # Try 5 times to make sure valve is closed
                        time.sleep(0.5)
                        stop_fill_status = cryostatfill.StopFill()
                        NumTries += 1
                    if not stop_fill_status:
                        eWarning('Failure terminating Cryostat fill!!!!')

    if Cryostat_is_Cold == 1 and lake.Temp_A > -190.0:
        eWarning('Warning. Cryostat Temp > -190 C')
    return

def ManualFill(cryostatfill):
    date = datetime.datetime.now()
    
    Min_Fill_Time = 5 # This is the minimum fill time
    Fill_Time_Limit = CryostatConfig.Fill_Time_Limit # This is the maximum fill time
    Overflow_Temp_Limit = CryostatConfig.Overflow_Temp_Limit
    start_fill_status = cryostatfill.StartFill()
    time.sleep(0.1)
    if start_fill_status:
        time.sleep(0.1)
        startfill = time.time()
        elapsed = 0.0
        temp = Overflow_Temp_Limit + 1.0
        difftemp = 0.0
        overflowfile = open('/home/ccd/cryostat/Log_Files/overflow_log.dat','a')
        time.sleep(0.1)
        # while elapsed < Fill_Time_Limit and difftemp < 0.8 and temp > Overflow_Temp_Limit: OLD
        while elapsed < Min_Fill_Time or (elapsed < Fill_Time_Limit and temp > Overflow_Temp_Limit):
            # Stop the fill when we reach time limit or detect LN2 overflow
            # or detect that the valve is no longer open (open:state=True)
            lasttemp = temp
            [state, temp] = cryostatfill.MeasureOverFlowTemp()
            difftemp = lasttemp - temp
            # We will terminate the fill if the temp reading drops below Overflow_Temp_Limit and Min_Fill_Time has elapsed
            overflowtime=datetime.datetime.now()
            line = overflowtime.strftime("%Y-%m-%d-%H:%M:%S")+' '+str(temp)+'\n'
            overflowfile.write(line)
            elapsed = time.time() - startfill
            if state:
                valve_state = "Open"
            if not state:
                # Break out of the loop if the valve doesn't stay open
                valve_state = "Closed"
                break
            time.sleep(0.25)
        if state:
            cryostatfill.LogFill(fill_time=elapsed)
        print("Terminated fill loop. Elapsed = %f, Overflow temp = %f, Valve state = %s\n"%(elapsed,temp,valve_state))
        sys.stdout.flush()
        overflowfile.close()
    stop_fill_status = cryostatfill.StopFill()
    NumTries = 0
    while not stop_fill_status and NumTries < 5: # Try 5 times to make sure valve is closed
        time.sleep(0.5)
        stop_fill_status = cryostatfill.StopFill()
    return

#   This routine both sends a warning to the email list in Email_Warning
#   and also writes the warning to disk under the file named "send_warning"
def eWarning(warning):
    try:
        subject = "Cryostat Warning issued " + time.asctime()
        w_file = open('/home/ccd/cryostat/Log_Files/send_warning', 'w')
        w_file.write(subject + ":: ")
        w_file.write(warning)
        w_file.close()
        Email_Warning.Send_Warning(subject, warning)
    except:
        pass
