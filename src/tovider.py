import time
import sys
import os
from pathlib import Path
from pathlib import PurePath
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool

dirsToProcess = []
jobQueue = []

maxJobs = 2
activeJobs = 0

genIndiv = True
genFolder = False

reenc = False

validAudioFiles = [ ".flac", ".mp3" ]

pool = Pool(max_workers=maxJobs)


def main():
    print("test")
    numArgs = len(sys.argv)
    print("Total Arguments: ", numArgs)
       
    p = Path(os.getcwd())
    dirsToProcess.append(p)
    processDirectory()
    print("Is valid directory:", p.is_dir())
    
    while(True):
        # implement main loop
        break
    

    
    

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
                activeJobs += 1
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
    print(job)
    # to-do: bitrate
    command = f"ffmpeg -y -i  \"{job}\" -filter_complex \"[0:v]scale=-1:-1[vid]\" -map [vid]:v -map 0:a -t 378 -r 1 -movflags +faststart \"output{activeJobs}.mp4\""
    f = pool.submit(subprocess.call, command, shell=True)
    f.add_done_callback(jobCallback)
    return

def jobCallback(future):
    if future.exception() is not None:
        print("Exception encountered!")
    else:
        print("Job finished")
    
    

                
            
        
    

if __name__ == '__main__':
    main()