import numpy as np
import time,subprocess,datetime,sys,glob,random
from astropy.io import fits
sys.path.append('/home/ccd/ucd-scripts/python-lib')
import Email_Warning

sequencerfilename="" #update this between runs
gaincfgfile="gainestimation.cfg"
sequencercfgfile="sequencerrun.cfg"
ptcresolution=40
ptcmaxADU=80000.0
persistenceADUlevel=400000.0
lowsuperflatADUlevel=5000.0
highsuperflatADUlevel=50000.0
standardinstensityperADU=0.0001332119195492821
ptcmaxintensity=standardinstensityperADU*80000

date=time.strftime("%Y%m%d")
imagedir='/mnt/10TBHDD/data/'+date

def take_gain_flats(cfgfile):
    try:
        subprocess.run('ccs-script /home/ccd/ucd-scripts/ucd-data.py '+cfgfile,check=True, shell=True)
        power_light("off")
    except:
        power_light("off")
    return
    
def calculate_gains(imagedir):
    fitsfiles=np.array(glob.glob(imagedir+'/*.fits'))
    filetypes=np.array([fits.getheader(name)["IMGTYPE"] for name in fitsfiles])
    flats=fitsfiles[np.where(filetypes=="FLAT")]
    biases=fitsfiles[np.where(filetypes=="BIAS")]
    if len(flats)!=2:
        raise Exception("wrong number of fits images for gain estimation")
    fitsfiles.sort()

    biasmedian=np.median(np.array([fits.getdata(bias,3) for bias in biases]))
    lowmedian=np.median(fits.getdata(flats[0],3))
    highmedian=np.median(fits.getdata(flats[1],3))
    lowdiff=lowmedian-biasmedian
    highdiff=highmedian-biasmedian

    intensityperADUlow=(1/lowdiff)
    intensityperADUhigh=(5/highdiff)
    intensityperADU=(intensityperADUlow+intensityperADUhigh)/2

    levels='''Bias level: '''+str(biasmedian)+'''
Low flat level: '''+str(lowmedian)+''' ADU
High flat level: '''+str(highmedian)+''' ADU

Lamp intensity per ADU: '''+str(intensityperADU)+" %"
    file = open(imagedir+'/gaininfo.txt', 'w')
    file.write(levels)
    file.close()
    
    return intensityperADU

def find_ptc_values(resolution,intensityperADU,ptcmaxintensity):
    minlamp=0.3
    minexp=1.0
    maxexp=15.0
    maxlamp=67.9
    bad1=6.4
    bad2=12
    ints=np.linspace(0.3,ptcmaxintensity,resolution)
    
    #flat pairs
    exp=minexp
    explist=[]

    for i in ints:
        if minlamp<=i/exp<=bad1 or bad2<=i/exp<=maxlamp:
            explist.append(str(exp)+"   "+str("{:.2f}".format(i/exp))+"  2,")
        elif bad1<=i/exp<=bad2:
            explist.append(str(exp*2)+"   "+str("{:.2f}".format(i/(exp*2)))+"  2,")
        elif i/exp>=maxlamp:
            while i/exp>=maxlamp:
                exp+=0.5
            explist.append(str(exp)+"   "+str("{:.2f}".format(i/exp))+"  2,")
    random.shuffle(explist)
    explist[-1]=explist[-1][:-1]
    ptcintensities=explist[0]
    for i in explist[1:]:
        ptcintensities=ptcintensities+'''
    '''+i
    return ptcintensities
    
def find_persistence(intensityperADU,ADUlevel):
    maxlamp=67.9
    persistenceintensities=intensityperADU*ADUlevel
    persistenceexposure=1
    while persistenceintensities>=maxlamp:
        persistenceexposure*=2
        persistenceintensities/=2
    persistence=str(persistenceexposure)+"  "+str("{:.2f}".format(persistenceintensities))
    return persistence
    
def make_cfg(filename,intensityperADU,lowsuperflatADUlevel,highsuperflatADUlevel,ptc,persistence):
    cfgfile='''#UCD Sequencer test file
# 
# Acquisition sequences to run
[ACQUIRE]
bias1
bias2
bias3
bias4
dark
superflat
ptc
persistenceflats
persistencedarks

[DESCRIPTION]
A full run for a given sequencer file.

[BIAS1]
ACQTYPE=bias
LOCATIONS = R21/Reb0        # locations to read
COUNT     = 5              # number of bias frames
EXTRADELAY = 0

[BIAS2]
ACQTYPE=bias
LOCATIONS = R21/Reb0        # locations to read
COUNT     = 5              # number of bias frames
EXTRADELAY = 15

[BIAS3]
ACQTYPE=bias
LOCATIONS = R21/Reb0        # locations to read
COUNT     = 5              # number of bias frames
EXTRADELAY = 30

[BIAS4]
ACQTYPE=bias
LOCATIONS = R21/Reb0        # locations to read
COUNT     = 5              # number of bias frames
EXTRADELAY = 60

[DARK]
LOCATIONS=R21/Reb0
DESCRIPTION=Darks.
BCOUNT=    1      # number of bias frames per dark image
dark= 30  5,      # integration time and image count for dark set
      180 5,
      360 5

[SUPERFLAT]
ACQTYPE=flat
DESCRIPTION  = Superflat with 20 flats at 5000 and 50000 ADU.
LOCATIONS    = R21/Reb0     # Locations to read
BCOUNT       = 1            # number of bias frames per flat set
WL           = r            # wavelength filter to use for the flats

flat =  1  '''+str("{:.2f}".format(intensityperADU*lowsuperflatADUlevel))+'''   25,    
        1  '''+str("{:.2f}".format(intensityperADU*highsuperflatADUlevel))+'''   25
        
        
[PTC]
ACQTYPE=flat
DESCRIPTION  = Superflat with 20 flats at 5000 and 50000 ADU.
LOCATIONS    = R21/Reb0     # Locations to read
BCOUNT       = 1            # number of bias frames per flat set
WL           = r            # wavelength filter to use for the flats
flat = '''+ptc+'''

[PERSISTENCEFLATS]
ACQTYPE=flat
DESCRIPTION  = Superflat with 20 flats at 5000 and 50000 ADU.
LOCATIONS    = R21/Reb0     # Locations to read
BCOUNT       = 21            # number of bias frames per flat set
WL           = r            # wavelength filter to use for the flats
flat = '''+persistence+'''  1

[PERSISTENCEDARKS]
ACQTYPE=dark
LOCATIONS=R21/Reb0
DESCRIPTION=Darks.
BCOUNT=    0      # number of bias frames per dark image
dark= 15   40'''
    file = open(filename, 'w')
    file.write(cfgfile)       
    file.close()
    return
    
def power_light(state):
    if state=="off" or state=="OFF" or state=="Off":
        subprocess.run('ccs-script /home/ccd/ucd-scripts/scripts/sphereOff.py',check=True, shell=True)
    elif state=="on" or state=="ON" or state=="On":
        subprocess.run('ccs-script /home/ccd/ucd-scripts/scripts/sphereOn.py',check=True, shell=True)

def remove_fits_files(imagedir):
    subprocess.run('rm '+imagedir+'/TS_C_*',check=True, shell=True)
    
def copy_file_to_imagedir(file):
    subprocess.run('cp '+file+" "+imagedir,check=True, shell=True)
    
def eWarning(warning):
    try:
        subject = "Run Finished " + time.asctime()
        w_file = open('/home/ccd/ucd-scripts/python-lib/send_warning', 'w')
        w_file.write(subject + ":: ")
        w_file.write(warning)
        w_file.close()
        Email_Warning.Send_Warning(subject, warning)
    except:
        pass

def full_gain_calculation():
    take_gain_flats(gaincfgfile)
    intenperADU=calculate_gains(imagedir)
    ptc=find_ptc_values(ptcresolution,intenperADU,ptcmaxintensity)
    persistence=find_persistence(intenperADU,persistenceADUlevel)
    cfgwords=make_cfg(sequencercfgfile,intenperADU,lowsuperflatADUlevel,highsuperflatADUlevel,ptc,persistence)
    remove_fits_files(imagedir)
    copy_file_to_imagedir(sequencercfgfile)

full_gain_calculation()    
