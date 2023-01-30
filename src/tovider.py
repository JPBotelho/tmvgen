import time
import sys
import os
from pathlib import Path
from pathlib import PurePath
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool
from threading import Lock

from cmdGen import cmdGen
from options import options
        
m = options() 
cGen = cmdGen(overwrite=True)

def main():
    p = Path(os.getcwd())
    m.dirsToProcess.append(p)
    tryProcessDirectory()
    
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
                    tryProcessDirectory()                    
    
    

    
    

def tryProcessDirectory():
    numFiles = 0
    f = None    
    
    if len(m.dirsToProcess) == 0:
        print("\nNo more directories to process!")
        return
    dir = m.dirsToProcess.pop()
    jobs = processDirectory(dir)
    for job in jobs:
        m.jobQueue.append(job)
        
def startJob(job):
    m.mutex.acquire()
    m.activeJobs += 1
    m.mutex.release()
    
    print("\nStarting Job: ", job)
    
    f = m.pool.submit(subprocess.run, job, shell=True, stderr=subprocess.DEVNULL)
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
            
            fileBitrate = getBitrate(audioFile)
            
            command = cGen.snglEmbedded(audioFile, replaceWithMP4(audioFile), fileBitrate)

            jobs.append(command)
            
            minBitrate = min(minBitrate, fileBitrate)
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
            pass
            # jobs.append(dir)
            # todo: generate folder ffmpeg command
        
    return jobs
    
def replaceWithMP4(file):
    p = PurePath(file)
    inputPath = file.resolve().__str__()
    outputFile = inputPath.replace(p.suffix, ".mp4")
    return outputFile

def jobCallback(future):
    print("\nFinished Job: " + future._result.args)
    if future.exception() is not None:
        print("\nException encountered!")
    
    m.mutex.acquire()
    m.activeJobs -= 1
    m.mutex.release()
    
    
# bitrate in kbps
def getBitrate(file):
    return 320

# playtime in seconds
def getLength(file):
    return 9
                
            
        
    

if __name__ == '__main__':
    main()