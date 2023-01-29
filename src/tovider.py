import time
import sys
import os
from pathlib import Path
from pathlib import PurePath
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool
from threading import Lock


# CONFIG
validAudioFiles = [ ".flac", ".mp3" ]
validImageExtensions = [ ".png", ".jpg", ".jpeg" ]
genIndiv = True
genFolder = True
genId = 0
reenc = False

# GLOBAL JOB VARIABLES
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
def main():
    global activeJobs
    print("test")
    numArgs = len(sys.argv)
    print("Total Arguments: ", numArgs)
       
    p = Path(os.getcwd())
    dirsToProcess.append(p)
    processDirectory()
    print("Is valid directory:", p.is_dir())
    
    while(True):  
        # print("EXECUTED")  
        if( activeJobs == 0 and len(jobQueue) == 0 and len(dirsToProcess) == 0):
            print("ALL JOBS FINISHED")
            return    
        if activeJobs < maxJobs:
            if len(jobQueue) > 0:
                startJob(jobQueue.pop())
            else:
                if(len(dirsToProcess) > 0):
                    print("Processing new directory")
                    processDirectory()                    
       
    

    
    

def processDirectory():
    global activeJobs, maxJobs, currCacheId
    if len(dirsToProcess) == 0:
        return
    dir = dirsToProcess.pop()
    print(dir.resolve())
    
    imageFound = False
    audioTrack = None
    # FFMPEG requires files to be in a list
    # for concat without reencoding
    if(genFolder and not reenc):
        f = open(cacheFolder + f"list{currCacheId}.txt", "w")    
        currCacheId += 1
        listCacheDict[dir] = f
        
    
    for child in dir.iterdir():
        if child.is_dir():
            dirsToProcess.append(child)
            
        file = PurePath(child)
        if(child.suffix in validAudioFiles):
            #todo: keep track of length in case of folder video
            #todo: keep track of bitrate in case of folder video
            
            # Keep track of an audio track in case image was not found
            # In order to extract embedded cover image
            audioTrack = child
            
            # Job can be started automatically
            if(len(jobQueue) == 0 and activeJobs < maxJobs):
                startJob(child.resolve())
            else:
                jobQueue.append(child.resolve())
                
            if(genFolder and not reenc):
                f.write(f"file 'file:{child.resolve()}'\n")
                
        elif(child.suffix in validImageExtensions):
            imgCacheDict[dir] = child
            
    if(genFolder):            
        jobQueue.append(dir.resolve())
        if not reenc:
            f.close()
            
def startJob(job):
    global genId
    global activeJobs
    
    print("Started job: ", job)

    # to-do: bitrate
    p = PurePath(job)
    outputFile = job.resolve().__str__().replace(p.suffix, ".mp4")
    mutex.acquire()
    activeJobs += 1
    mutex.release()
    #command = f"ffmpeg -y -i  \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid]\" -map [vid]:v -map 0:a -t 378 -r 1 -movflags +faststart \"{outputFile}\""
    command = f"ffmpeg -y -i \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid];[vid]loop=loop=-1:size=1:start=0[vid2]\" -map [vid2]:v -map 0:a -b:a 320k -shortest -r 1 -movflags +faststart \"{outputFile}\""
    
    #to-do: remove stdout from showing
    
    f = pool.submit(subprocess.run, command, shell=True, stderr=subprocess.DEVNULL)
    f.add_done_callback(jobCallback)
    
    
    
    
    return

def jobCallback(future):
    global activeJobs
    # todo: fix result.args being messed up
    print("Finished: " + future._result.args)
    if future.exception() is not None:
        print("Exception encountered!")
    else:
        print("Job finished")
        
    mutex.acquire()
    activeJobs -= 1
    mutex.release()
    
    

                
            
        
    

if __name__ == '__main__':
    main()