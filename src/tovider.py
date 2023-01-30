import time
import sys
import os
from pathlib import Path
from pathlib import PurePath
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool
from threading import Lock

from cmdGen import cmdGen
class options:
    validAudioFiles = [ ".flac", ".mp3" ]
    validImageExtensions = [ ".png", ".jpg", ".jpeg" ]

    # generate videos per track
    genIndiv = True

    # generate videos per folder
    genFolder = True
    # reencode audio streams
    reenc = False

    # ----- GLOBAL JOB VARIABLES
    dirsToProcess = []
    jobQueue = []
    maxJobs = 5
    activeJobs = 0

    # MULTITHREADING
    pool = Pool(max_workers=maxJobs)
    mutex = Lock()

    # CACHE
    cacheFolder = os.path.dirname(os.path.realpath(__file__)) + "\\cache\\"
    currCacheId = 0

    # Directory -> Path to cover image in cache 
    imgCacheDict = {}

    # Directory -> Path to list.txt file in cache
    listCacheDict = {}
    
    def __init__(self): 
        pass       
        # ----- CONFIG
        
m = options() 
cGen = cmdGen(overwrite=True)

def main():
    p = Path(os.getcwd())
    m.dirsToProcess.append(p)
    processDirectory()
    
    while(True):  
        # print("EXECUTED")  
        if( m.activeJobs == 0 and len(m.jobQueue) == 0 
           and len(m.dirsToProcess) == 0):
            return    
        if m.activeJobs < m.maxJobs:
            if len(m.jobQueue) > 0:
                startJob(m.jobQueue.pop())
            else:
                if(len(m.dirsToProcess) > 0):                    
                    processDirectory()                    
    
    

    
    

def tryProcessDirectory():
    numFiles = 0
    f = None    
    
    if len(m.dirsToProcess) == 0:
        print("No more directories to process!")
        return
    dir = m.dirsToProcess.pop()
    jobs = processDirectory(dir)
    for job in jobs:
        m.jobQueue.append(job)
        
def startJob(job):
    if(job.is_dir()):
        return
    print("Started job: ", job)

    # to-do: bitrate
    p = PurePath(job)
    inputPath = job.resolve().__str__()
    suffix = p.suffix
    outputFile = job.resolve().__str__().replace(p.suffix, ".mp4")
    m.mutex.acquire()
    m.activeJobs += 1
    m.mutex.release()
    #command = f"ffmpeg -y -i  \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid]\" -map [vid]:v -map 0:a -t 378 -r 1 -movflags +faststart \"{outputFile}\""
    #command2 = f"ffmpeg -y -i \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid];[vid]loop=loop=-1:size=1:start=0[vid2]\" -map [vid2]:v -map 0:a -b:a 320k -shortest -r 1 -movflags +faststart \"{outputFile}\""
    command = cGen.snglEmbedded(job, outputFile, 320)
    #to-do: remove stdout from showing
    f = m.pool.submit(subprocess.run, command, shell=True, stderr=subprocess.DEVNULL)
    f.add_done_callback(jobCallback)
    
    
def startFileJob(job):
    fileDir = job.parents[0]
    
    # there was no image in the folder
    if m.imgCacheDict[fileDir] is None:
        # extract image from file
        #if it fails, cancel the job
        pass    
    return

def startDirectoryJob(job):
    # no image was found in the folder, or was able to be extracted
    # from the files.
    # the folder job always runs last.
    if m.imgCacheDict[job] is None:
        return
    return
    
# returns list of jobs (for files and folder, if applicable)
# writes .txt to cache with: 
#   lowest bitrate
#   total length
#   audio files in directory 
#
# side effects:
# appends subdirectories to directoriesToProcess
def processDirectory(dir):
    jobs = []
    minBitrate = sys.maxsize
    length = 0
    imageFound = False
    lastAudioFile = None
    for child in dir.iterdir():
        if child.is_dir():
            m.dirsToProcess.append(child)
            
        file = PurePath(child)
        if(child.suffix in m.validAudioFiles):            
            audioFile = child.resolve()
            
            lastAudioFile = audioFile
            jobs.append(audioFile)
            minBitrate = min(minBitrate, getBitrate(audioFile))
            length += getLength(audioFile)
            
        elif(child.suffix in m.validImageExtensions):
            m.imgCacheDict[dir] = child
            imageFound = True
            
    if(len(jobs) > 0):
        m.currCacheId += 1
        f = open(m.cacheFolder + f"{dir.name}({m.currCacheId}).txt", "w")
        f.write(f" #{length}#{minBitrate}\n")
        
        for job in jobs:
            f.write(f"file 'file:{job}'\n")
        f.close()
        if(m.genFolder):
            jobs.append(dir)
        
    return jobs
    
    

def jobCallback(future):
    # todo: fix result.args being messed up
    print("Finished Job: " + future._result.args)
    if future.exception() is not None:
        print("Exception encountered!")
    
    m.mutex.acquire()
    m.activeJobs -= 1
    m.mutex.release()
    
    
# bitrate in kbps
def getBitrate(file):
    return 6

# playtime in seconds
def getLength(file):
    return 9
                
            
        
    

if __name__ == '__main__':
    main()