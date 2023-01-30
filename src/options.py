from threading import Lock
from concurrent.futures import ThreadPoolExecutor as Pool
import os
# 1: 83
# 2: 58
# 3: 57.94
# 4: 56
# 8: 56 
class options:
    validAudioFiles = [ ".flac", ".mp3" ]
    validImageExtensions = [ ".png", ".jpg", ".jpeg" ]

    # generate videos per track
    genIndiv = True
    extractImg = True
    
    # generate videos per folder
    genFolder = True
    # reencode audio streams
    reenc = False

    # ----- GLOBAL JOB VARIABLES
    dirsToProcess = []
    jobQueue = []
    maxJobs = 8
    activeJobs = 0
    completedJobs = 0
    
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
    
    # Job -> Time it was started
    jobStartTime = {}
    
    def __init__(self): 
        pass       
        # ----- CONFIG