import time
import sys
import os
from pathlib import Path
from pathlib import PurePath
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool
from threading import Lock
dirsToProcess = []
jobQueue = []

maxJobs = 5
activeJobs = 0

genIndiv = True
genFolder = False
genId = 0
reenc = False

validAudioFiles = [ ".flac", ".mp3" ]

pool = Pool(max_workers=maxJobs)

mutex = Lock()

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
                print("Started new job")
                startJob(jobQueue.pop())
            else:
                if(len(dirsToProcess) > 0):
                    print("Processing new directory")
                    processDirectory()
                    
        # implement main loop
    

    
    

def processDirectory():
    global activeJobs, maxJobs
    dir = dirsToProcess.pop()
    
    # FFMPEG requires files to be in a list
    # for concat without reencoding
    if(genFolder and not reenc):        
        f = open(dir.resolve() / "list.txt", "w")    
    for child in dir.iterdir():
        if child.is_dir():
            dirsToProcess.append(child)
            
        file = PurePath(child)
        if(child.suffix in validAudioFiles):
            # Job can be started automatically
            if(len(jobQueue) == 0 and activeJobs < maxJobs):
                startJob(child.resolve())
            else:
                jobQueue.append(child.resolve())
                
            if(genFolder and not reenc):
                f.write(f"file 'file:{child.resolve()}'\n")
    if(genFolder):            
        jobQueue.append(dir.resolve())
        if not reenc:
            f.close()
            
def startJob(job):
    global genId
    global activeJobs
    
    genId += 1
    #print(job)
    # to-do: bitrate
    p = PurePath(job)
    outputFile = job.resolve().__str__().replace(p.suffix, ".mp4")
    mutex.acquire()
    activeJobs += 1
    mutex.release()
    #command = f"ffmpeg -y -i  \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid]\" -map [vid]:v -map 0:a -t 378 -r 1 -movflags +faststart \"{outputFile}\""
    command = f"ffmpeg -i \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid];[vid]loop=loop=-1:size=1:start=0[vid2]\" -map [vid2]:v -map 0:a -b:a 320k -shortest -r 1 -movflags +faststart \"{outputFile}\""
    f = pool.submit(subprocess.call, command, shell=True)
    f.add_done_callback(jobCallback)
    
    
    
    
    return

def jobCallback(future):
    global activeJobs
    if future.exception() is not None:
        print("Exception encountered!")
    else:
        print("Job finished")
        
    mutex.acquire()
    activeJobs -= 1
    mutex.release()
    
    

                
            
        
    

if __name__ == '__main__':
    main()