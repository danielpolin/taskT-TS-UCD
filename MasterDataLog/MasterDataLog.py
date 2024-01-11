import DataLogConfig,time,datetime

date = datetime.datetime.now()
starttime=time.time()

print("Starting. Current time = "+date.strftime("%Y-%m-%d-%H:%M:%S"))
new,logged,unlogged=DataLogConfig.append_masterlog()
print(str(new)+" New logs written. "+str(logged)+" Total logged directories. "+str(unlogged)+" Directories not logged.")
endtime=time.time()
elapsed = endtime-starttime
print("Done. Elapsed time = "+str(elapsed))
