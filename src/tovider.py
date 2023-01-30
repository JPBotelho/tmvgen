from datetime import datetime
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
            
            # Individual file commands can be one of three:
            # Generate from embedded cover art (-loop filter) (snglEmbedded)
            # Generate from embedded cover art (extract image to cache first)
            # NOTIMPLEMENTED Generate from folder image (snglExternal)
            
            outputFile = replaceWithMP4(audioFile)
            if(not m.extractImg):
                command = cGen.snglEmbedded(audioFile, outputFile, fileBitrate)
            else:
                if(imageFound):
                    coverImg = m.imgCacheDict[dir]
                else:
                    coverImg = m.cacheFolder + f"{child.name}({m.currCacheId}).png"
                    extractCmd = cGen.extractImage(child, coverImg)+"&"                    
                command = f"{extractCmd}{cGen.snglExternal(audioFile, coverImg, outputFile, fileBitrate)}"
            

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
            #folderImage = m.imgCacheDict[dir]
            #folderCommand = cGen.folderList()
            pass
            # jobs.append(dir)
            # todo: generate folder ffmpeg command
        
    return jobs
    
def replaceWithMP4(file):
    p = PurePath(file)
    inputPath = file.resolve().__str__()
    outputFile = inputPath.replace(p.suffix, ".mp4")
    return outputFile

def startJob(job):
    m.mutex.acquire()
    m.activeJobs += 1
    m.mutex.release()
    
    m.jobStartTime[job] = datetime.now()
    
    print("\nStarting Job: ", job)
    
    f = m.pool.submit(subprocess.run, job, shell=True, stderr=subprocess.DEVNULL)
    f.add_done_callback(jobCallback)
    

def jobCallback(future):
    timeDiff = datetime.now() - m.jobStartTime[future._result.args]
    secsElapsed = timeDiff.total_seconds()
    print(f"\nFinished Job after {secsElapsed}s: " + future._result.args)
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