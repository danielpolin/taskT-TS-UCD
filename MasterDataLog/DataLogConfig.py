import numpy,time,datetime,subprocess,os

datadir="/mnt/10TBHDD/data/"
daystocheckcutoff=7

def get_subdirectories(directory):
    """
    Returns an array of subdirectories in the given directory.

    Args:
    - directory (str): The path to the directory.

    Returns:
    - list: A list containing the names of subdirectories in the specified directory.
    """
    subdirectories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return subdirectories

def find_recent_directories(directory,dayscutoff):
    """
    Finds directories that have been modified within a specified number of days.

    Args:
    - directory (str): The path to the directory to search for recently modified directories.
    - dayscutoff (float): The threshold in days for considering directories as recent modifications.

    Returns:
    - recentfiles (list): A list of directory names that have been modified within the specified dayscutoff.
    """
    filecheck=subprocess.check_output("stat "+directory+"* |grep 'File\|Modify'",shell=True)
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
        i[1]=(now-datetime.datetime.strptime(i[1],'%Y-%m-%d %H:%M:%S.%f')).total_seconds()/86400.0
    filecheck=numpy.array(filecheck)
    filecheck=numpy.array(filecheck)
    recentfiles=[]
    for file in filecheck:
        if float(file[1])<dayscutoff:
            recentfiles.append(file[0])
    return recentfiles

def remove_elements(original_array, elements_to_remove):
    """
    Removes specified elements from the original array.

    Args:
    - original_array (list): The original array.
    - elements_to_remove (list): The elements to be removed from the original array.

    Returns:
    - list: A new array with elements removed.
    """
    return [element for element in original_array if element not in elements_to_remove]

def read_text_file(file_path):
    """
    Reads a text file with two columns and imports data into two arrays.

    Args:
    - file_path (str): The path to the text file.

    Returns:
    - tuple: A tuple containing two arrays representing the data from the two columns.
    """
    column1 = []
    column2 = []

    with open(file_path, 'r') as file:
        for line in file:
            # Assuming columns are separated by a space (you can change it based on your file format)
            data = line.strip().split()
            
            # Assuming there are at least two columns in each line
            column1.append(data[0])
            column2.append(data[1])

    return column1, column2

def get_unlogged_directories(directory):
    """
    Retrieves a list of subdirectories within a specified directory that are not logged as 'logged' in a log file.

    Args:
    - directory (str): The path to the directory to search for unlogged subdirectories.

    Returns:
    - list: A list of subdirectories that are not logged as 'logged' in the 'directories.txt' log file.
    """
    subdirectories=get_subdirectories(directory)
    logged=read_text_file(datadir+"logs/MasterDataLog/directories.txt")
    logged=logged[0][logged[1]=='logged']
    subdirectories=remove_elements(subdirectories, logged)
    return subdirectories
    

def log_finished_directory(directory,status):
    """
    Logs the status of a directory in the 'directories.txt' log file, providing a record of the directory's status.

    Args:
    - directory (str): The directory to be logged.
    - status (str): The status to be appended to the directory in the log file.
    """
    file = open(datadir+'logs/MasterDataLog/directories.txt', 'a')
    file.write(directory+" "+status+"\n")
    file.close()
    return True

def find_directory_log(directory):
    """
    Finds the log file associated with the specified directory.

    Args:
    - directory (str): The directory for which to find the log file.

    Returns:
    - str: The filename of the log file associated with the provided directory.
    """
    logfile=subprocess.check_output("ls "+datadir+directory+"/20??????-log.txt",shell=True)
    logfile=str(logfile)
    return logfile[2:-3]

def sort_masterlog(html_file,newcount,totallogged,totalunlogged):
    with open(html_file, 'r') as file:
        html_content = file.read()
    html_content=html_content.split("<b>")
    html_content=html_content[1:]
    html_content.sort()
    file = open(html_file, 'w')
    date=time.strftime("%Y%m%d")
    file.write("<p>Last Updated: "+date+"</p>")
    file.write("<p>"+str(newcount)+" New logs written. "+str(totallogged)+" Total logged directories. "+str(totalunlogged)+" Directories not logged. </p>")
    for entry in html_content[::-1]:
        file.write("<b>"+entry)
    file.close()
    return
        
def write_to_master_log(filename,directory):
    """
    Reads the content of a file, formats it as HTML paragraphs, and appends it to the MasterLog.html file.

    Args:
    - filename (str): The path to the input file.
    - directory (str): The name of the directory the referenced data is in.

    Returns:
    - None
    """
    html_string = ""
    with open(filename, 'r') as infile:
        for paragraph in infile.read().split('\n'):
            html_string += "<p>" + paragraph+ "</p>"
    file = open(datadir+'logs/MasterDataLog/MasterLog.html', 'a')
    string_to_write="<b>"+directory+"</b> <br> <p>"+html_string+"</p> <br>"
    file.write(string_to_write)
    file.close()
    return

def upload_masterlog(logfile):
    command ='scp '+logfile+' lsst@emerald.physics.ucdavis.edu:/var/www/html/storm/datalog.html'
    copylog = subprocess.Popen(command, shell=True)
    subprocess.Popen.wait(copylog)

def append_masterlog():
    subdirectories=get_subdirectories(datadir)
    subdirectories.sort()
    recordeddirs=read_text_file(datadir+"logs/MasterDataLog/directories.txt")
    logged=[]
    newcount=0
    for pair in range(len(recordeddirs[0])):
        if recordeddirs[1][pair]=="logged":
            logged.append(recordeddirs[0][pair])
    unloggeddirectories=remove_elements(subdirectories, logged)
    file = open(datadir+'logs/MasterDataLog/directories.txt', 'w')
    file.write(logged[0]+" logged\n")
    for directory in logged[1:]:
        file.write(directory+" logged\n")
    file.close()
    newunloggeddirs=[]
    logupdated=False
    for directory in unloggeddirectories:
        try:
            logname=find_directory_log(directory)
            write_to_master_log(logname,directory)
            log_finished_directory(directory,"logged")
            logupdated=True
            newcount+=1
        except:
            newunloggeddirs.append(directory)
    for directory in newunloggeddirs:
        log_finished_directory(directory,"unlogged")
    totallogged=newcount+len(logged)-1
    totalunlogged=len(subdirectories)-totallogged-1    
    if logupdated:
        sort_masterlog(datadir+'logs/MasterDataLog/MasterLog.html',newcount,totallogged,totalunlogged)
    upload_masterlog(datadir+'logs/MasterDataLog/MasterLog.html')
    return newcount,totallogged,totalunlogged
