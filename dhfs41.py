import re

def extract_bits(numb, position, tam):
    return (numb >> (position + 1 - tam)) & ((1 << tam) - 1)

class DHFS41:
    def __init__(self, DEBUG=False):
        self.PART_TABLE_OFF = 0x3C00
        self.DESC_SIZE = 32
        self.imgLoaded = False
        self.disk      = None
        self.nParts = 0

        self.DEBUG = DEBUG
        self.config={}
        self.config['DEBUG'] = DEBUG
        self.config['CARVE_SIGNAT'] = re.compile(b"^\x44\x48\x49\x49")

    def getNumbDescs(self, pIndx):
        return len(self.alldescs[pIndx]) // self.DESC_SIZE

    def getDesc(self, pIndx, dIndx):
        posDesc = dIndx * self.DESC_SIZE
        return self.alldescs[pIndx][posDesc: posDesc+self.DESC_SIZE]

    def getDescType(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return  int.from_bytes(desc[0:1], byteorder='little')

    def getBeginDesc(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[24:28], byteorder='little')

    def getNextDesc(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[12:16], byteorder='little')

    def getPrevDesc(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[20:24], byteorder='little')

    def getLastDesc(self, pIndx, dIndx):
        nextDesc = self.getNextDesc(pIndx, dIndx)
        if nextDesc == 0:
            return dIndx
        return self.getLastDesc(pIndx, nextDesc)

    def getNumberFrags(self, pIndx, dIndx):
        if self.getDescType(pIndx, dIndx) == 1:
            desc = self.getDesc(pIndx, dIndx)
            return int.from_bytes(desc[2:4], byteorder='little') + 1
        else:
            return self.getNumberFrags(pIndx,
                            self.getBeginDesc(pIndx, dIndx))

    def getFragNumber(self, pIndx, dIndx):
        if self.getDescType(pIndx, dIndx) == 1:
            return 0

        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[2:4], byteorder='little')

    def getCamera(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[1:2], byteorder='little') - 48 + 1

    def decodeTimeStamp(self, ts):
        return extract_bits(ts, 31, 6), extract_bits(ts, 25, 4), \
               extract_bits(ts, 21, 5), extract_bits(ts, 16, 5), \
               extract_bits(ts, 11, 6), extract_bits(ts, 5, 6)

    def getTimeStamps(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return (int.from_bytes(desc[4:8], byteorder='little'),
                int.from_bytes(desc[8:12], byteorder='little'))

    def getBeginTimeStamp(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[4:8], byteorder='little')

    def getEndTimeStamp(self, pIndx, dIndx):
        desc = self.getDesc(pIndx, dIndx)
        return int.from_bytes(desc[8:12], byteorder='little')

    def getBeginDate(self, pIndx, dIndx):
        beginTimeStamp = self.getBeginTimeStamp(pIndx, dIndx)
        return self.timeStampToDate(beginTimeStamp)

    def getBeginTime(self, pIndx, dIndx):
        beginTimeStamp = self.getBeginTimeStamp(pIndx, dIndx)
        return self.timeStampToTime(beginTimeStamp)

    def getEndTime(self, pIndx, dIndx):
        endTimeStamp = self.getEndTimeStamp(pIndx, dIndx)
        return self.timeStampToTime(endTimeStamp)

    def timeStampToDate(self, timestamp):
        year, month, day, _, _, _ = self.decodeTimeStamp(timestamp)
        return f"20{year:02d}-{month:02d}-{day:02d}"

    def timeStampToTime(self, timestamp):
        _, _, _, hour, minute, sec = self.decodeTimeStamp(timestamp)
        return f"{hour:02d}:{minute:02d}:{sec:02d}"

    def timeStampToHuman(self, timestamp):
        year, month, day, hour, minute, sec = self.decodeTimeStamp(timestamp)
        return f"20{year:02d}-{month:02d}-{day:02d} "+\
               f"{hour:02d}:{minute:02d}:{sec:02d}"

    def DecodeDesc(self, pIndx, dIndx):
        dic = {
            'descType'     : self.getDescType(pIndx, dIndx),
            'camera'       : self.getCamera(pIndx, dIndx),
            'begTime'      : self.timeStampToHuman(self.getBeginTimeStamp(pIndx, dIndx)),
            'endTime'      : self.timeStampToHuman(self.getEndTimeStamp(pIndx, dIndx)),
            'numFrag'      : self.getFragNumber(pIndx, dIndx),
            'totFrags'     : self.getNumberFrags(pIndx, dIndx),
            'beginDesc'    : self.getBeginDesc(pIndx, dIndx),
            'prevDesc'     : self.getPrevDesc(pIndx, dIndx),
            'nextDesc'     : self.getNextDesc(pIndx, dIndx),
            'sizeLast'     : self.getLastFragSize(pIndx, dIndx),
            'totalSize'    : self.getVideoSize(pIndx, dIndx),
            'hex'          : " ".join([f"{x:02x}" for x in self.getDesc(pIndx, dIndx)])
        }
        return dic

    def loadPartTable(self):
        self.PART_OFFS = []
        self.SB_OFFS   = []

        self.disk.seek(self.PART_TABLE_OFF+0x34)
        partInfo = self.disk.read(64)

        self.nParts = 0
        blkSize = 512
        while partInfo[:4] != b"\xAA\x55\xAA\x55":
            self.SB_OFFS.append(int.from_bytes(partInfo[20:24],
                                                byteorder='little') * blkSize)
            self.PART_OFFS.append(int.from_bytes(partInfo[48:56],
                                                byteorder='little') * blkSize)
            partInfo = self.disk.read(64)
            self.nParts += 1

    def getNumPartitions(self):
        return self.nParts

    def loadImage(self, path):
        if self.imgLoaded:
            self.disk.close()
            self.imgLoaded = False

        self.disk = open(path, "rb")
        if self.disk.read(7) in [b'DHFS4.1']:
            self.loadPartTable()

            #TODO: It needs processing each partition
            self.disk.seek(self.PART_OFFS[0] + self.SB_OFFS[0] + 0x10)
            self.firstDate = int.from_bytes(self.disk.read(4), byteorder='little')
            self.lastDate = int.from_bytes(self.disk.read(4), byteorder='little')

            self.disk.seek(self.PART_OFFS[0] + self.SB_OFFS[0] + 0x2c)
            self.BLK_SIZE = int.from_bytes(self.disk.read(4), byteorder='little')
            self.FRAG_SIZE = int.from_bytes(self.disk.read(4),byteorder='little') * self.BLK_SIZE

            self.disk.seek(self.PART_OFFS[0] + self.SB_OFFS[0] + 0x38)
            self.FRAG_RESERVED = (int.from_bytes(self.disk.read(4), byteorder='little'))

            self.disk.seek(self.PART_OFFS[0] + self.SB_OFFS[0] + 0xF8)
            self.logsOffset = int.from_bytes(self.disk.read(4), byteorder='little') * self.BLK_SIZE

            self.imgLoaded = True
            self.loadDescs()
            self.printMetaData()
            #print ("Last offset: ", self.PART_OFFS[0] + self.VID_OFF + self.NUM_FRAGS*self.FRAG_SIZE )

        return self.imgLoaded

    def getImageMetaData(self):
        if self.imgLoaded:
            message  =  "*"*20+" Disk Metadata "+"*"*20+"\n"
            message += f"Block size: {self.BLK_SIZE}\n"
            message += f"Fragment Size: {self.FRAG_SIZE}\n"
            message += f"Fragments Reserved: {self.FRAG_RESERVED}/partition\n"
            for pIndx in range(self.nParts):
                partStart = self.PART_OFFS[pIndx]
                message += "-"*20+f" Partition {pIndx} "+"-"*20+"\n"
                message += f"\tDescriptors offset: {partStart + self.DESC_OFF[pIndx]}\n"
                message += f"\tNumber of fragmentes: {self.NUM_FRAGS[pIndx]}\n"
                message += f"\tVideos offset: {partStart + self.VID_OFF[pIndx]}\n"
                message += "\tVideos offset after reserved: "
                message += f"{partStart + self.VID_OFF[pIndx] + self.FRAG_RESERVED*self.FRAG_SIZE}\n"
            return message
        else:
            return "No image loaded!!!"

    def printMetaData(self):
        print (self.getImageMetaData())

    def getDescTypes(self, pIndx):
        allDescTypes = {}
        for indx in range(self.NUM_FRAGS[pIndx]):
            descType = self.getDescType(pIndx, indx)
            allDescTypes[descType] = allDescTypes.get(descType, 0) + 1
        return allDescTypes

    def getLastFragSize(self, pIndx, dIndx):
        if self.getDescType(pIndx, dIndx) == 1:
            desc = self.getDesc(pIndx, dIndx)
            return int.from_bytes(desc[16:20], byteorder='little')* self.BLK_SIZE
        else:
            return self.getLastFragSize(pIndx,
                            self.getBeginDesc(pIndx, dIndx))

    def getFragsInVideo(self, pIndx, dIndx):
        allFrags = []
        begDesc = dIndx
        numFrags = self.getNumberFrags(pIndx, dIndx)

        idx = 0
        while dIndx != 0 and dIndx != 0xFFFFFFFF:
            allFrags.append(dIndx)
            idx += 1
            dIndx = self.getNextDesc(pIndx, dIndx)

        if  self.DEBUG and (idx > numFrags):
            print (f"\t\tVideo {begDesc} in partition {pIndx} has more frags "+
                   "than in main desc. 'Extract' will use greater size!")
        return allFrags

    def getMainDescs(self, pIndx):
        if self.imgLoaded:
            for dIndx in range(self.NUM_FRAGS[pIndx]):
                descType  = self.getDescType(pIndx, dIndx)
                descBegTime, descEndTime = self.getTimeStamps(pIndx, dIndx)

                if (descType in [1]) and descBegTime != descEndTime:
                    yield dIndx
        return

    def getFreeDescs(self, pIndx):
        if self.imgLoaded:
            for dIndx in range(self.NUM_FRAGS[pIndx]):
                descType  = self.getDescType(pIndx, dIndx)
                if descType == 0:
                    yield dIndx
        return

    def getDirtyDescs(self, pIndx):
        if self.imgLoaded:
            for dIndx in range(self.NUM_FRAGS[pIndx]):
                descType  = self.getDescType(pIndx, dIndx)

                if descType == 2:
                    beginDesc = self.getBeginDesc(pIndx, dIndx)
                    fragsInBegin = self.fragsInVideos[pIndx].get(beginDesc, [])
                    if dIndx not in fragsInBegin:
                        yield dIndx
        return

    def loadDescs(self):
        self.DESC_OFF = []
        self.VID_OFF = []
        self.NUM_FRAGS = []
        self.alldescs = []
        self.numVideos = []

        for partOff in self.PART_OFFS:
            self.disk.seek(partOff + self.SB_OFFS[0] + 0x44)
            self.DESC_OFF.append(int.from_bytes(self.disk.read(4),
                                        byteorder='little') * self.BLK_SIZE)
            self.VID_OFF.append(int.from_bytes(self.disk.read(4),
                                        byteorder='little') * self.BLK_SIZE)
            self.NUM_FRAGS.append(int.from_bytes(self.disk.read(4),
                                        byteorder='little'))

            self.disk.seek(partOff + self.DESC_OFF[-1])
            self.alldescs.append(self.disk.read(self.DESC_SIZE * self.NUM_FRAGS[-1]))

        self.fragsInVideos = []
        self.freeFrags = []
        self.dirtyFrags = []

        for pIndx in range(self.nParts):
            if self.DEBUG:
                print ("Partition: ", pIndx)
                print ("\tGetting desc types...")
            allDescTypes = self.getDescTypes(pIndx)

            if self.DEBUG:
                print ("\tLinking fragments to each main desc...")
            fragsInVideos = {}
            for indx in self.getMainDescs(pIndx):
                fragsInVideos[indx] = self.getFragsInVideo(pIndx, indx)
            self.fragsInVideos.append(fragsInVideos)

            if self.DEBUG:
                print ("\tGetting free fragments...")
            self.freeFrags.append([])
            for indx in self.getFreeDescs(pIndx):
                self.freeFrags[pIndx].append(indx)

            if self.DEBUG:
                print ("\tGetting dirty fragments...")
            self.dirtyFrags.append([])
            for indx in self.getDirtyDescs(pIndx):
                self.dirtyFrags[pIndx].append(indx)


        #print ("Fragmentos encadeados em videos", fragsInVideos)
        #print ("Fragmentos alocdos", fragsAloc)


        '''
        fd = open("logs.bin", "wb")
        self.disk.seek(0)
        fd.write(self.disk.read(self.VID_OFF[0]+2120*2**21))
        fd.close()
        '''

    def getSlackSize(self, pIndx, dIndx):
        if self.getDescType(pIndx, dIndx) == 1:
            desc = self.getDesc(pIndx, dIndx)
            return self.FRAG_SIZE - self.getLastFragSize(pIndx, dIndx)
        else:
            return self.getSlackSize(pIndx,
                            self.getBeginDesc(pIndx, dIndx))

    def getVideoSize(self, pIndx, dIndx):
        return ((self.getNumberFrags(pIndx, dIndx) - 1) * self.FRAG_SIZE +
                self.getLastFragSize(pIndx, dIndx))

    def readFrag(self, pIndx, fIndx):
        self.disk.seek(self.PART_OFFS[pIndx] + self.VID_OFF[pIndx] +
                        fIndx * self.FRAG_SIZE)
        return self.disk.read(self.FRAG_SIZE)

    def readLastFrag(self, pIndx, fIndx):
        self.disk.seek(self.PART_OFFS[pIndx] + self.VID_OFF[pIndx] +
                        fIndx * self.FRAG_SIZE)
        return self.disk.read(self.getLastFragSize(pIndx, fIndx))

    def readSlackFrag (self, pIndx, fIndx):
        posSlack = self.getLastFragSize(pIndx, fIndx)
        self.disk.seek(self.PART_OFFS[pIndx] + self.VID_OFF[pIndx] +
                        fIndx * self.FRAG_SIZE + posSlack)
        return self.disk.read(self.FRAG_SIZE - posSlack)

    def saveVideoAt (self, pIndx, dIndx, path, logFunc = None):
        if self.imgLoaded:
            date     = self.getBeginDate(pIndx, dIndx)
            begin    = self.getBeginTime(pIndx, dIndx)
            end      = self.getEndTime(pIndx, dIndx)
            cam      = self.getCamera(pIndx, dIndx)
            totFrag  = self.getNumberFrags(pIndx, dIndx)

            fileName = f"Video-p{pIndx}-{dIndx:06d}-{date.replace('-','')}-"
            fileName += f"{begin.replace(':','')}-{end.replace(':','')}-"
            fileName += f"ch{cam:02d}.h264"
            fullName = path+"/"+fileName

            with open (fullName, "wb") as fdOut:
                frags = self.fragsInVideos[pIndx][dIndx]
                idx = 0
                for idx in range(len(frags) - 1):
                    fdOut.write(self.readFrag(pIndx, frags[idx]))
                    idx += 1
                    if logFunc:
                        logFunc(f"Saving {fileName} ({idx*100/len(frags):4.2f}%)")
                fdOut.write(self.readLastFrag(pIndx, frags[idx]))
                fdOut.close()
            return fileName
        else:
            return None

    def saveSlackAt (self, idx, pIndx, dIndx, path, logFunc = None):
        if self.imgLoaded and self.getSlackSize(pIndx, dIndx) > 0:
            date     = self.getBeginDate(pIndx, dIndx)
            begin    = self.getBeginTime(pIndx, dIndx)
            end      = self.getEndTime(pIndx, dIndx)
            cam      = self.getCamera(pIndx, dIndx)
            sizeLast = self.getCamera(pIndx, dIndx)
            fileName = f"{idx:04d}-Slack-p{pIndx}-{dIndx:06d}-"
            fileName += f"{date.replace('-','')}-"
            fileName += f"{begin.replace(':','')}-{end.replace(':','')}-"
            fileName += f"ch{cam:02d}.h264"
            fullName = path+"/"+fileName

            with open (fullName, "wb") as fdOut:
                if logFunc:
                    logFunc(f"Saving {fileName}")

                lastDesc = self.fragsInVideos[pIndx][dIndx][-1]
                fdOut.write(self.readSlackFrag(pIndx, lastDesc))
                fdOut.close()
            return fileName
        else:
            return None


    def saveRecAtFree (self, pIndx, path, logFunc):
        nVideos = 0
        fileD = None
        signature = self.config['CARVE_SIGNAT']

        for indx in self.freeFrags[pIndx]:
            fragData = self.readFrag(pIndx, indx)

            #Looks for signature in first 32 bytes
            if signature.search(fragData[:32]):
                if fileD:
                    nVideos += 1
                    fileD.close()

                fileName = f"FragFree-{indx:06d}.h264"
                fileD = open(path+"/"+fileName, "wb")
                fileD.write(fragData)
                if logFunc:
                    logFunc(f"Saving vídeo {fileName}")
            elif fileD:
                fileD.write(fragData)

        if fileD:
            nVideos += 1
            fileD.close()

        return nVideos

    def saveRecAtDirty (self, pIndx, path, logFunc):
        nVideos = 0
        fileD = None

        alreadySaved = []
        begDesc  = -1

        totDirtyFrags = len(self.dirtyFrags[pIndx])
        indx  = 0

        while len(alreadySaved) < totDirtyFrags:
            if self.dirtyFrags[pIndx][indx] not in alreadySaved:
                dIndx = self.dirtyFrags[pIndx][indx]

                date     = self.getBeginDate(pIndx, dIndx)
                begin    = self.getBeginTime(pIndx, dIndx)
                cam      = self.getCamera(pIndx, dIndx)
                fileName = f"FragDirty-p{pIndx}-{dIndx:06d}-{date.replace('-','')}-"
                fileName += f"{begin.replace(':','')}-"
                fileName += f"ch{cam:02d}.h264"
                fullName = path+"/"+fileName

                fileD = open(fullName, "wb")
                if logFunc:
                    logFunc(f"Saving vídeo {fileName}")

                fileD.write(self.readFrag(pIndx, dIndx))
                alreadySaved.append(dIndx)
                nextDesc = self.getNextDesc(pIndx, dIndx)
                if self.DEBUG:
                    print (f"pIndx {pIndx} dIndx {dIndx} nextDesc {nextDesc}"+
                           f"baseDesc {self.getBeginDesc(pIndx, dIndx)} "+
                           f"baseNext {self.getBeginDesc(pIndx, nextDesc)}")

                while (nextDesc != 0) and (self.getBeginDesc(pIndx, dIndx) ==
                                           self.getBeginDesc(pIndx, nextDesc)):
                    dIndx = nextDesc
                    fileD.write(self.readFrag(pIndx, dIndx))
                    alreadySaved.append(dIndx)
                    nextDesc = self.getNextDesc(pIndx, dIndx)

                    if self.DEBUG:
                        print (f"pIndx {pIndx} dIndx {dIndx} nextDesc {nextDesc}"+
                               f"baseDesc {self.getBeginDesc(pIndx, dIndx)} "+
                               f"baseNext {self.getBeginDesc(pIndx, nextDesc)}")

                fileD.close()
                nVideos += 1

            indx += 1


        return nVideos

    def saveRecVideos(self, pIndx, path, logFunc = None):
        nVideos = 0
        if self.imgLoaded:
            nVideos  = self.saveRecAtFree (pIndx, path, logFunc)
            nVideos += self.saveRecAtDirty(pIndx, path, logFunc)
        return nVideos


    def saveLogs(self, fullPath):
        self.disk.seek(self.logsOffset)
        logsHeader = self.disk.read(2 * self.BLK_SIZE)
        logsSize = int.from_bytes(logsHeader[:4], byteorder='little') - 2 * self.BLK_SIZE

        fileD = open(fullPath, "wb")
        fileD.write(self.disk.read(logsSize))
        fileD.close()

    def setConfig(self, fileName):
        castings = {"CARVE_SIGNAT" : lambda e: re.compile(("^"+e).encode()),
                    "DEBUG" : bool}

        fd = open (fileName, "r")
        for line in fd:
            line = line.strip()
            print (line)
            if (len(line) > 0) and (line[0] != "#"):
                eqIdx = line.find("=")
                if eqIdx > 0:
                    key   = line[:eqIdx].strip()
                    value = line[eqIdx+1:].strip()
                    self.config[key] = castings[key](value)
        fd.close()
        self.DEBUG = self.config['DEBUG']
        print (self.config)
