import sys,time,subprocess,glob
import numpy as np #General array managment and what have you
import matplotlib.pyplot as plt #For plotting charts and data
from astropy.io import fits #For processing .fits files
from itertools import cycle
sys.path.append('/home/ccd/ucd-scripts/python-lib')
import Stage
sys.path.append('/home/ccd/Focus/')
import FocusConfig

class Focus_Finder():
    def __init__(self):
        self.date=time.strftime("%Y%m%d")

        self.configfile='/home/ccd/sextractor/default-array_dither.sex'
        self.regfilename='/home/ccd/Analysis_Code/focuscurveareas.reg'
        self.imagedir='/mnt/10TBHDD/data/'+self.date
        self.focusdir='/home/ccd/Focus/'
        self.CCDtype=FocusConfig.CCDtype
        self.stage = Stage.Stage()

        self.lookingforfocus=True
        self.startingz=FocusConfig.zStart
        self.stepCount=FocusConfig.stepCount
        self.zstep=int((FocusConfig.zEnd-self.startingz)/(self.stepCount-1))
        self.iteration=0
        return
    
    def take_series(self,numimages,start,step):
        """Takes a series of images moving the stage in the negative z direction inbetween images."""
        pos=self.stage.go_to(z=start,focus=True)
        subprocess.run('ccs-script '+'/home/ccd/ucd-scripts/ucd-data.py '+self.focusdir+'lib/focusbias.cfg',check=True, shell=True)
        time.sleep(1)

        if numimages>1:
            for i in range(numimages-1):
                pos=self.stage.move_stage(z=step)
                subprocess.run('ccs-script '+self.focusdir+'lib/ucd-data.py '+self.focusdir+'lib/focusrun.cfg',check=True, shell=True)
                time.sleep(1)
    
    def get_last_series_files(self,numimages):
        files=np.array(glob.glob(self.imagedir+'/*.fits'))
        files.sort()
        files=files[-int(numimages):]
        if len(files)==0:
            print("No Files Found")
        return files
    
    def plot_series(self,files,save=True):
        """Plot the center postage stamps of a list of .fits files."""
        imagedata=[]
        zpos=[]
        for file in files:
            image=fits.getdata(file,4)
            image=image[1800:2000,100:300]
            imagedata.append(image)
            zpos.append(fits.getheader(file)["STAGEZ"])
        
        fig = plt.figure(1, figsize=(10,10))
        fig.patch.set_facecolor('white')
        for i in range(len(imagedata)):
            ax1=fig.add_subplot(int(self.stepCount/5),5,i+1)
            ax1.set_title(str(i)+": z = "+str(zpos[i]),fontsize=15)
            ax1.imshow(imagedata[i])
            ax1.axis('off')
        plt.tight_layout()
        plt.show()
        if save==True:
            fig.savefig(self.imagedir+"/Focus_Iteration_"+str(self.iteration)+".png")
        return zpos

    def reset_positions(self):
        reset=input("Reset positions? (y/n): ")
        if reset=="y" or reset=="Y" or reset=="yes" or reset=="Yes" or reset=="true" or reset=="True":
            tries=0
            while tries<4:
                try:
                    self.startingz=int(input("New starting z position: "))
                    farside=int(input("New far z position: "))
                    self.zstep=int((farside-self.startingz)/(self.stepCount-1))
                    return True
                except ValueError:
                    print("You must enter z positions as an integer.")
                    tries+=1
        return False
        
    def find_focus_range(self):
        """Iteratively gets closer to the focus position until you find a range of points 100mm on either side of focus"""
        while self.lookingforfocus==True:
            self.take_series(numimages=self.stepCount,start=self.startingz,step=self.zstep)
            files=self.get_last_series_files(numimages=self.stepCount)
            zpos=self.plot_series(files)

            #choose which images are best
            chosenimages=input("What are the edge images? (ex: 4,5): ")
            if chosenimages=="" or chosenimages=="None":
                reset=self.reset_positions()
                if reset==True:
                    continue
            tries=0
            while tries<4:
                try:
                    chosenimages=[int(number) for number in chosenimages.split(",")]
                    lowinput,highinput=min(chosenimages),max(chosenimages)
                    break
                except ValueError:
                    print("You must enter the chesen images as two integers in the format: 4,5")
                    chosenimages=input("What are the edge images? (ex: 4,5): ")
                    tries+=1
            
            highz=zpos[lowinput]
            lowz=zpos[highinput]
            print("Range selected z="+str(highz)+" to z="+str(lowz))

            self.startingz=highz
            self.zstep=int((lowz-self.startingz)/(self.stepCount-1))
            self.iteration+=1

            if highinput-lowinput>4 or abs(highz-lowz)<100 or abs(highinput-lowinput)==self.stepCount-1:
                self.lookingforfocus==False
                midpoint=int((highz+lowz)/2)
                self.startingz=midpoint+65
                self.zstep=int(-200/(self.stepCount-1))
                print("Center estimate at z="+str(midpoint))
                return
        return
    
    def plot_focus_polyfit(self,regtxt_all,zpos_all,size_all,save=True):
        
        now=time.strftime("%Y%m%d-%H:%M")
        working=True
        xmin=-999999999
        xmax=999999999
        minsize=3
        while working:
            minima=[]
            
            
            colors = ['b','g','r','c','m']
            lines = ["-","--","-.",":"]
            colorcycler = cycle(colors)

            fig = plt.figure(1, figsize=(10,10))
            fig.patch.set_facecolor('white')

            ax1=fig.add_subplot(1,1,1)
            ax1.set_xlabel('Z position [microns]',fontsize=20)
            ax1.set_ylabel('Pinhole x moment [pixels]',fontsize=20)

            for loc in np.unique(regtxt_all):
                plotcolor=next(colorcycler)
                g=np.where((regtxt_all==loc) & (size_all<minsize) & (xmin<zpos_all) & (xmax>zpos_all))[0]
                xvals,yvals=zpos_all[g],size_all[g]
                if len(xvals)>1:
                    #fit the xvals and yvals with a polynomial to find best focus
                    coeffs=np.polyfit(xvals,yvals,6)
                    polynom=np.poly1d(coeffs)
                    xlin=np.linspace(min(xvals),max(xvals),1000)
                    yfit=polynom(xlin)
                    best_foc=np.median(xlin[np.where(yfit==min(yfit))])
                    minima.append(best_foc)
                    ax1.plot(xvals,yvals,color=plotcolor,marker = 'o',linestyle = 'None',markersize = 10,label = loc+',z$_{foc}$='+str(float(best_foc))[:6]+", min$_{foc}$="+str(float(min(yfit)))[:5])
                    ax1.plot([best_foc,best_foc],[.6,min(yfit)],color=plotcolor)
                    ax1.plot(xlin,yfit,color=plotcolor,linewidth=5,alpha=.4)
            ax1.legend()
            tb=minima[0]-minima[4]
            rl=minima[3]-minima[1]
            ax1.set_title('Focus curve for locations around CCD\n'+now+'\nTopBottom: '+str(tb)[:5]+'um; Right-left: '+str(rl)[:5]+'um',fontsize=24)
            plt.tight_layout()
            plt.show()
            
            reset=input("Do you need to change plot parameters (y/n): ")
            if reset=="n" or reset=="N" or reset=="no" or reset=="No" or reset=="false" or reset=="False":
                working=False
                break
            else:
                tries=0
                while tries<4:
                    try:
                        newxmin=input("New min z position (blank for no change): ")
                        if newxmin!='':
                            xmin=float(newxmin)
                        newymin=input("New max z position (blank for no change): ")
                        if newymin!='':
                            ymin=float(newymin)
                        newminsize=input("New max pinhole x-moment (blank for no change): ")
                        if newminsize!='':
                            minsize=float(newminsize)
                        break
                    except ValueError:
                        print("You must enter a number or leave the input blank for all values.")
                        tries+=1   
        if save==True:
            savefigname=self.imagedir+"/"+now+'-focus_curve.png'
            fig.savefig(savefigname)
        if len(minima)<5:
            print("ERROR: Unable to find spot sources in all regions. Change plotted ranges or z range of sweep.")
            return
        print("Top to bottom distance "+str(tb)+"um. Right to Left "+str(rl)+"um")   
        if self.CCDtype=="ITL":
            if abs(tb)>abs(rl):
                thetachange=tb*0.1/40
                print("Top minimum far from Bottom. Increase stage rotation by "+str(thetachange)+" degrees.")
            else:
                screwturns=rl*.25/16
                print("Right minimum far from left. Rotate height screw by "+str(screwturns)+" turns clockwise from above.")
        elif self.CCDtype=="e2v":
            if abs(tb)<abs(rl):
                screwturns=rl*.1/40
                print("Increase stage rotation by "+str(screwturns)+" degrees.")
            else:
                thetachange=-tb*.25/16
                print("Rotate height screw by "+str(thetachange)+" turns clockwise from above.")
        else:
            print("You must set CCDtype='ITL' or 'e2v' in the config file.")               
        return minima
            
    def calculate_x_moments(self):
        numimages=20
        segdict=dict(zip(np.arange(1,17),['10','11','12','13','14','15','16','17','07','06','05','04','03','02','01','00']))
        zfilelist=self.get_last_series_files(numimages=numimages)
            
        #Read in a region file produced by making rectangle regions on individual segments of a mosaic iraf image in DS9. Save the region file as whatever name you like (enter below), making sure to save in the "ds9" format and "image" coords when it asks
        f=open(self.regfilename)
        lines=f.readlines()

        regions=[]
        for line in lines[3:]:
            if line[:6]=='# tile':
                tilenum=int(line.split()[2])
                #print "Tile number: "+str(tilenum)
            if line[:3]=='box':
                regnums,regend=line.split('#')
                yc,xc,ys,xs=[int(float(val)) for val in regnums[4:-4].split(',')]
                regtxt=regend.split('{')[1].split('}')[0]
                regions.append([tilenum,xc,yc,xs/2,ys/2,regtxt])

        # Gather the imaging data inside the region file, write it out to fits images for SExtractor to process, and read in the catalogs output. Delete the new fits images when done.
        #tilenum_all=[]
        #expnum_all=[]
        zpos_all=[]
        size_all=[]
        regtxt_all=[]
        for fitsfilename in zfilelist:
            expnumber=fitsfilename
            zpos=fits.getheader(fitsfilename)["STAGEZ"]
            for reg in regions:
                tilenum,xc,yc,xs,ys,regtxt=reg
                img=fits.getdata(fitsfilename,"SEGMENT"+segdict[tilenum])
                imsnip=img[int(xc-xs/2):int(xc+xs/2),int(yc-ys/2):int(yc+ys/2)]
                outname=fitsfilename[:-5]+"SEGMENT"+segdict[tilenum]+"snip.fits"
                fits.writeto(outname,imsnip,overwrite=True)
                test=subprocess.call(["source-extractor",outname,"-c",self.configfile,"-CATALOG_NAME",outname+'.cat'])
                cat=fits.getdata(outname+'.cat','LDAC_OBJECTS')
                size_med=np.median(cat['X2WIN_IMAGE'])
                subprocess.call(["rm",outname,outname+'.cat'])
                #tilenum_all.append(tilenum)
                #expnum_all.append(expnumber)
                zpos_all.append(zpos)
                size_all.append(size_med)
                regtxt_all.append(regtxt)

        #tilenum_all=np.array(tilenum_all)
        #expnum_all=np.array(expnum_all,dtype='int16')
        zpos_all=np.array(zpos_all)
        size_all=np.array(size_all)
        regtxt_all=np.array(regtxt_all)
        return regtxt_all,zpos_all,size_all    
            
    def find_focus_minima(self):
        """This function takes a sweep of images and fits the x and y moments of spots fount on the left, right, top bottom, and middle of the CCD. It then fits polynomials to the moments to find the minima"""
        working=True
        while working:
            running=True
            numimages=20
            step=-10
            while running:
                self.take_series(numimages=numimages,start=self.startingz,step=step)
                regtxt_all,zpos_all,size_all=self.calculate_x_moments()
                minima=self.plot_focus_polyfit(regtxt_all,zpos_all,size_all)

                arewedoneyet=input("Hit enter when you have adjusted screws and are ready to begin next sweep. Enter 'Done' to exit or readjust z range.")
                
                doweneedtoshiftz=input("Do you need to change the starting (high) z value? (y/n): ")
                shiftcondition=doweneedtoshiftz=="Y" or doweneedtoshiftz=="y" or doweneedtoshiftz=="yes" or doweneedtoshiftz=="Yes" or doweneedtoshiftz=="True" or doweneedtoshiftz=="true"
                
                if (arewedoneyet=='Done' or arewedoneyet=='done') and not shiftcondition:
                    running=False
                    working=False
                    bestfocus=minima+[minima[2]]
                    bestfocus=int(np.median(bestfocus))
                    print("Recommended best focus at z="+str(bestfocus))
                    tries=0
                    zFocus="No Focus Selected"
                    while tries<4:
                        try:
                            zFocus=input("Please enter your chosen z focus value: ")
                            zFocus=int(zFocus)
                            break
                        except ValueError:
                            print("You must enter z focus position as an integer.")
                            tries+=1
                    return zFocus
                
                if shiftcondition:
                    tries=0
                    while tries<4:
                        try:
                            self.startingz=int(input("New starting z position: "))
                            break
                        except ValueError:
                            print("You must enter z positions as an integer.")
                            tries+=1
        return
    
    def write_log_file(self,bestfocus):
        files=np.array(glob.glob(self.imagedir+'/*.fits'))
        files.sort()
        
        stringtowrite="This data was used to align and focus the "+str(self.CCDtype)+" CCD on "+str(self.date)+"\n\nBest Focus found at z="+str(bestfocus)+". \n\nThe following is a summary of the images in this directory:\n\n"
        file = open(self.imagedir+'/'+self.date+'-log.txt', 'a')
        file.write(stringtowrite)
        newiteration=self.iteration
        counter=0
        for i in range(self.iteration):
            out="Focus Sweep "+str(counter)+''':
    '''+files[int(-20-((newiteration)*self.stepCount))]+" - "+files[int(-21-((newiteration-1)*self.stepCount))]+"\n\n"
            file.write(out)
            counter+=1
            newiteration-=1
        out='''Final Focus Sweep: 
    '''+files[-20]+" - "+files[-1] 
        file.write(out)       
        file.close()
        
    def rename_directory(self):
        subprocess.run('mv '+self.imagedir+" "+self.imagedir+"-"+self.CCDtype+"_Focus",check=True, shell=True)
        
    def find_focus(self):
        
        self.find_focus_range()
        print("Focus Range found. Transitioning to finding x-Moment minima.")
        bestfocus=self.find_focus_minima()
        
        self.write_log_file(bestfocus)
        #zero encoders at focus
        self.stage.go_to_exact(z=bestfocus)
        self.rename_directory()
