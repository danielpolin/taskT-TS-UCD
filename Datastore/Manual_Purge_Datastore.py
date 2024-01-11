import time,datetime,numpy
from subprocess import check_output

filecheck=check_output("stat /mnt/10TBHDD/data/* |grep 'File\|Modify'",shell=True)
filecheck=str(filecheck)
filecheck=filecheck.split('File')
now=datetime.datetime.now()

for i in range(len(filecheck)):
    filecheck[i]=filecheck[i].split('\\n')
del(filecheck[0])
for i in filecheck:
    del(i[-1])
    i[0]=i[0][2:]
    i[1]=i[1][8:-9]
    i[1]=(now-datetime.datetime.strptime(i[1],'%Y-%m-%d %H:%M:%S.%f')).total_seconds()/3600.0
filecheck=numpy.array(filecheck)


tsaprecheck=check_output(["/home/ccd/ccs/bin/store <checkdatastore.txt"],shell=True)
tsaprecheck=str(tsaprecheck)
tsaprecheck=tsaprecheck.split('\\n')
print(now.strftime("%Y-%m-%d-%H:%M:%S")+" Initially "+tsaprecheck[-3]+".")
time.sleep(3)

output=["Deleting","Deleting","Deleting"]
while output[-3][:8]=="Deleting":
    output=check_output(["/home/ccd/ccs/bin/store <purgedatastore.txt"],shell=True)
    output=str(output)
    output=output.split('\\n')
    time.sleep(1)

check=check_output(["/home/ccd/ccs/bin/store <checkdatastore.txt"],shell=True)
check=str(check)
check=check.split('\\n')
print("Data store purged. Currently "+check[-3]+'. \n')
