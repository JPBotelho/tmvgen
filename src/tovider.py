import time
import sys
import os
from pathlib import Path
from pathlib import PurePath
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool
from threading import Lock

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

def main():
    print("test")
    numArgs = len(sys.argv)
    print("Total Arguments: ", numArgs)
    
    p = Path(os.getcwd())
    m.dirsToProcess.append(p)
    processDirectory()
    print("Is valid directory:", p.is_dir())
    
    while(True):  
        # print("EXECUTED")  
        if( m.activeJobs == 0 and len(m.jobQueue) == 0 
           and len(m.dirsToProcess) == 0):
            print("ALL JOBS FINISHED")
            return    
        if m.activeJobs < m.maxJobs:
            if len(m.jobQueue) > 0:
                startJob(m.jobQueue.pop())
            else:
                if(len(m.dirsToProcess) > 0):
                    print("Processing new directory")
                    processDirectory()                    
    
    

    
    

def processDirectory():
    if len(m.dirsToProcess) == 0:
        return
    dir = m.dirsToProcess.pop()
    print(dir.resolve())
    
    # FFMPEG requires files to be in a list
    # for concat without reencoding
    if(m.genFolder and not m.reenc):
        f = open(m.cacheFolder + f"list{m.currCacheId}.txt", "w")    
        m.currCacheId += 1
        m.listCacheDict[dir] = f
        
    
    for child in dir.iterdir():
        if child.is_dir():
            m.dirsToProcess.append(child)
            
        file = PurePath(child)
        if(child.suffix in m.validAudioFiles):
            #todo: keep track of length in case of folder video
            #todo: keep track of bitrate in case of folder video
            
            # Job can be started automatically
            if(len(m.jobQueue) == 0 and m.activeJobs < m.maxJobs):
                startJob(child.resolve())
            else:
                m.jobQueue.append(child.resolve())
                
            if(m.genFolder and not m.reenc):
                f.write(f"file 'file:{child.resolve()}'\n")
                
        elif(child.suffix in m.validImageExtensions):
            m.imgCacheDict[dir] = child
            
    if(m.genFolder):            
        m.jobQueue.append(dir.resolve())
        if not m.reenc:
            f.close()
        
def startJob(job):
    print("Started job: ", job)

    # to-do: bitrate
    p = PurePath(job)
    outputFile = job.resolve().__str__().replace(p.suffix, ".mp4")
    m.mutex.acquire()
    m.activeJobs += 1
    m.mutex.release()
    #command = f"ffmpeg -y -i  \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid]\" -map [vid]:v -map 0:a -t 378 -r 1 -movflags +faststart \"{outputFile}\""
    command = f"ffmpeg -y -i \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid];[vid]loop=loop=-1:size=1:start=0[vid2]\" -map [vid2]:v -map 0:a -b:a 320k -shortest -r 1 -movflags +faststart \"{outputFile}\""
    
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
    
    
    
    

def jobCallback(future):
    # todo: fix result.args being messed up
    print("Finished: " + future._result.args)
    if future.exception() is not None:
        print("Exception encountered!")
    else:
        print("Job finished")
        
    m.mutex.acquire()
    m.activeJobs -= 1
    m.mutex.release()
    
    

                
            
        
    

if __name__ == '__main__':
    main()