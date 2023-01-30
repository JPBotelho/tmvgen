class cmdGen:

    owflg = "-y"
    
    def __init__(self, overwrite):
        if overwrite == True:
            owflg = "-y"
        else:
            owflg = "-n"
        
    
    # input file (must have embedded cover image)
    # output file
    # bitrate
    def snglEmbedded(self, inp, out, br):
        command = (f"ffmpeg {self.owflg} -i \"{inp}\" "
                   "-filter_complex \"[0:v]scale=-1:-1[vid];"
                   "[vid]loop=loop=-1:size=1:start=0[vid2]\" "
                   "-map [vid2]:v " 
                   "-map 0:a " 
                   f"-b:a {br}k " 
                   f"-shortest -r 1 -movflags +faststart \"{out}\"")
        # print(command)
        return command

    # input file
    # cover image file
    # output file
    # bitrate
    def snglExternal(self, inp, img, out, br):
        command = (f"ffmpeg {self.owflg} -loop 1 -framerate 1 " 
                  f"-i \"{img}\" "
                  f"-i \"{inp}\" "
                  "-map 0:v " 
                  "-map 1:a " 
                  f"-b:a {br}k "
                  f"-shortest -r 1 -movflags +faststart \"{out}\"")
        return command
    
    # input directory
    # cover image file
    # output file
    # bitrate
    def folderReencode(self, inputDir, img, out, br):
        return
    
    # input directory
    # cover image file
    # list.txt containing the files to concat
    # output file
    # bitrate
    def folderList(self, inputDir, img, list, out, br):
        return
    
    
    # concatenates together video files generated for the albums
    # input directory
    # output file
    # bitrate
    def folderConcat(self, inputDir, out, br):
        return
    
    # extracts embedded cover art 
    # does not check if cover art exists
    # input file
    # output image
    def extractImage(self, file, out):
        command = f"ffmpeg {self.owflg} -i \"{file}\" -an -vcodec copy \"{out}\""
        return command
    


c = cmdGen(True)
c.snglEmbedded("input.mp3", "output.mp4", "320")