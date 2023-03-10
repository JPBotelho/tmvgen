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
    startTime = datetime.now()
    
    p = Path(os.getcwd())
    m.dirsToProcess.append(p)
    tryProcessDirectory()
    
    while(True):  
        if( m.activeJobs == 0 and len(m.jobQueue) == 0 
           and len(m.dirsToProcess) == 0):
            elapsedSeconds = (datetime.now() - startTime).total_seconds()
            print(f"\nFinished {m.completedJobs} jobs in {elapsedSeconds}s")
            return    
        if m.activeJobs < m.maxJobs:
            if len(m.jobQueue) > 0:
                startJob(m.jobQueue.pop(0))
            else:
                if(len(m.dirsToProcess) > 0):                    
                    tryProcessDirectory()                    
    
    

    
    

def tryProcessDirectory():
    numFiles = 0
    f = None    
    
    if len(m.dirsToProcess) == 0:
        print("\nNo more directories to process!")
        return
    dir = m.dirsToProcess.pop(0)
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
    audioFiles = []
    jobs = []
    minBitrate = sys.maxsize
    length = 0
    image = None
    for child in dir.iterdir():
        if child.is_dir():
            if m.recursive:
                m.dirsToProcess.append(child)
            
        file = PurePath(child)
        if(child.suffix in m.validAudioFiles): 
            audioFiles.append(child)           
        elif(child.suffix in m.validImageExtensions):
            m.imgCacheDict[dir] = child
            image = child
    
   
    if(len(audioFiles) <= 0):
        return []
    
    
    for audioFile in audioFiles:        
        fileBitrate = getBitrate(audioFile)
        
        # Individual file commands can be one of three:
        # Generate from embedded cover art (-loop filter) (snglEmbedded)
        # Generate from embedded cover art (extract image to cache first) (snglExternal)
        # Generate from folder image (snglExternal)
        
        outputFile = replaceWithMP4(audioFile)
        if(not m.extractImg):
            command = cGen.snglEmbedded(audioFile, outputFile, fileBitrate)
        else:
            if(image is not None):
                coverImg = image
                command = cGen.snglExternal(audioFile, coverImg, outputFile, fileBitrate)
            else:
                # extract cover image for this file
                coverImg = m.cacheFolder + f"({m.currCacheId}).png"
                m.imgCacheDict[dir] = coverImg
                extractCmd = cGen.extractImage(audioFile, coverImg)+"&"                    
                command = f"{extractCmd}{cGen.snglExternal(audioFile, coverImg, outputFile, fileBitrate)}"
        

        jobs.append(command)
        
        minBitrate = min(minBitrate, fileBitrate)
        length += getLength(audioFile)
        
    if(m.genFolder):
        folderList = m.cacheFolder + f"{dir.name}({m.currCacheId}).txt"
        f = open(folderList, "w")
        f.write(f" #{length}#{minBitrate}\n")        
        for audioFile in audioFiles:
            f.write(f"file 'file:{audioFile.resolve()}'\n")
        f.close()
        
        folderCommand = cGen.folderList(m.imgCacheDict[dir], folderList, str(dir)+"/folderVideo.mp4")
        jobs.append(folderCommand)
        
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
    
    print("\nStarting Job... ")
    if(m.printJobs):
        print(f"\n{job}")
    
    f = m.pool.submit(subprocess.run, job, shell=True, stderr=subprocess.DEVNULL)
    f.add_done_callback(jobCallback)
    

def jobCallback(future):
    timeDiff = datetime.now() - m.jobStartTime[future._result.args]
    secsElapsed = timeDiff.total_seconds()
    print(f"\nFinished Job after {secsElapsed}s: ")
    if(m.printJobs):
        print(f"\f{future._result.args}")
    if future.exception() is not None:
        print("\nException encountered!")
    
    m.mutex.acquire()
    m.activeJobs -= 1
    m.completedJobs += 1
    m.mutex.release()
    
    
# bitrate in kbps
def getBitrate(file):
    return 320

# playtime in seconds
def getLength(file):
    return 9
                
            
        
    

if __name__ == '__main__':
    main()