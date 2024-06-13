# encoding: utf-8

version = "DHFS4.1 Extractor 0.5"
copyright = \
'''
This program can identify and recover videos stored\n\
in a DHFS4.1 filesystem (common in chinese's DVR). \n\n\
When running under Windows, use 'Open Image' to get data\n\
source. In Linux you can access evidence disks or images\n\
using their names in file system. \n\n\
DHFS4.1 extractor is offered to you under GPL license\n\
by GALILEU Batista (galileu.batista@ifrn.edu.br)\n\
You must retain author name in all circunstances in which\n\
the program is used. He has made the best to get \n\
a correct operation, but no warranty implicit or explicit\n\
is provided.
'''

from dhfs41 import *
import wx
import os
import time

class DVRExtractor (wx.Frame):
    def __init__(self, *args, **kwargs):
        super(DVRExtractor, self).__init__(*args, **kwargs)
        self.SetSize(840,530)
        self.dhfs = DHFS41(DEBUG=DEBUG)
        self.createGUI()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def createGUI(self):
        self.CreateStatusBar()

        splitter = wx.SplitterWindow(self, style=wx.SP_NOSASH)
        self.painel = wx.Panel(splitter)
        self.painel1 = wx.Panel(splitter)
        splitter.SplitVertically(self.painel1, self.painel)
        splitter.SetSashGravity(0.27)

        # ToolBar
        self.ToolBar = wx.ToolBar(self, wx.ID_ANY, style=wx.TB_TEXT)
        self.ToolBar.AddTool(toolId=101, label="Open Image",
                bitmap=wx.Bitmap(self.resource_path("icons/abrir.png")))
        if os.name != 'nt':
            self.ToolBar.AddTool(toolId=102, label="Open Disk",
                bitmap=wx.Bitmap(self.resource_path("icons/abrir.png")))
        self.ToolBar.AddTool(toolId=103, label="Info",
                bitmap=wx.Bitmap(self.resource_path("icons/info.png")))
        self.ToolBar.AddTool(toolId=104, label="Extract",
                bitmap=wx.Bitmap(self.resource_path("icons/extract.png")))
        self.ToolBar.AddTool(toolId=105, label="MetaData",
                bitmap=wx.Bitmap(self.resource_path("icons/metadata.png")))
        self.ToolBar.AddTool(toolId=106, label="Slack",
                bitmap=wx.Bitmap(self.resource_path("icons/slack.png")))
        self.ToolBar.AddTool(toolId=107, label="Recover",
                bitmap=wx.Bitmap(self.resource_path("icons/recover.png")))
        self.ToolBar.AddTool(toolId=108, label="Logs",
                bitmap=wx.Bitmap(self.resource_path("icons/logs.png")))
        self.ToolBar.AddTool(toolId=109, label="Config",
                bitmap=wx.Bitmap(self.resource_path("icons/config.png")))
        self.ToolBar.AddTool(toolId=110, label="About",
                bitmap=wx.Bitmap(self.resource_path("icons/info.png")))
        self.ToolBar.AddTool(toolId=111, label="Exit",
                bitmap=wx.Bitmap(self.resource_path("icons/exit.png")))
        self.ToolBar.Bind(wx.EVT_TOOL, self.toolBarEvent)
        self.ToolBar.Realize()

        self.SetTitle(version)
        self.Centre()

        self.lbVideos = wx.ListCtrl(self.painel, -1, pos=(0, 0),
                                    size=(585, 400),
                                    style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.lbVidHeaders = ["PART", "ID", "DATA", "BEGIN", "END", "CAMERA", "SIZE"]
        self.lbVideos.SetBackgroundColour(wx.WHITE)
        for i in range(len(self.lbVidHeaders)):
            self.lbVideos.InsertColumn(i+1, self.lbVidHeaders[i],
                                            wx.LIST_FORMAT_CENTER,
                                            width=wx.LIST_AUTOSIZE)

        wx.StaticText(self.painel1, label="Date", pos=(40, 10))
        wx.StaticText(self.painel1, label="Camera", pos=(125, 10))

        # ListBoxes para selecionar datas e câmeras
        self.lbDates = wx.ListBox(self.painel1, pos=(10, 30), size=(100, 370),
                                    style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.filterVideosInfo, self.lbDates)

        self.lbCams = wx.ListBox(self.painel1, pos=(120, 30), size=(70, 370),
                                    style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.filterVideosInfo, self.lbCams)


        self.Show(True)
        time.sleep(1)
        self.showAbout()

        #fileName = r"Y:\IPL2024.0011881-DPF_MOS_RN\M0353_24\IPL2024.0011881-TA1233949_24-I01-M353_24.dd"
        #fileName = r"Y:\IPL2024.0011881-DPF_MOS_RN\M0354_24\IPL2024.0011881-TA1233949_24-I02-M354_24.dd"
        #self.SetTitle(version + " - " + fileName)

        #if self.dhfs.loadImage(fileName):
        #    self.showVideosInfo()

    def toolBarEvent(self, e):
        if e.GetId() == 101:
            self.loadImage()
        elif e.GetId() == 102:
            self.loadDisk()
        elif e.GetId() == 103:
            self.showMetadata()
        elif e.GetId() == 104:
            self.saveVideos()
        elif e.GetId() == 105:
            self.exportVideosMetaData()
        elif e.GetId() == 106:
            self.saveSlacks()
        elif e.GetId() == 107:
            self.saveRecovered()
        elif e.GetId() == 108:
            self.saveLogs()
        elif e.GetId() == 109:
            self.config()
        elif e.GetId() == 110:
            self.showAbout()
        elif e.GetId() == 111:
            self.Close()

    def clearGUI(self):
        self.lbDates.Clear()
        self.lbCams.Clear()
        self.lbVideos.DeleteAllItems()
        self.SetStatusText("")

    def loadDisk(self):
        self.loadImage()

    def loadImage(self):
        self.clearGUI()

        self.dlg = wx.FileDialog(self, "Escolha um arquivo", os.getcwd(), "")
        if self.dlg.ShowModal() == wx.ID_OK:
            fileName = self.dlg.GetPath()

            self.SetStatusText("Loading Image...")
            if self.dhfs.loadImage(fileName):
                self.showVideosInfo()
            else:
                self.SetStatusText("")
                wx.MessageBox("This is not a DHFS4.1 filesystem!!!", version,
                                style=wx.OK | wx.ICON_INFORMATION)

    def showAbout(self):
        wx.MessageBox(copyright, "About", style=wx.OK)

    def showMetadata(self):
        message = self.dhfs.getImageMetaData()
        if message:
            wx.MessageBox(message, "DHFS4.1 Metadata", style=wx.OK)
        else:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)

    def showVideosInfo(self):
        allVideoDates  = []
        allCameras     = []
        for pIndx in range(self.dhfs.getNumPartitions()):
            for dIndx in self.dhfs.getMainDescs(pIndx):
                videoDate = self.dhfs.getBeginDate(pIndx, dIndx)
                if not videoDate in allVideoDates:
                    allVideoDates.append(videoDate)

                camera = f"{self.dhfs.getCamera(pIndx, dIndx):02d}"
                if not camera in allCameras:
                    allCameras.append(camera)

        allVideoDates.sort()
        allVideoDates.insert(0, "All")
        allCameras.sort()
        allCameras.insert(0, "All")

        self.lbDates.InsertItems(allVideoDates, 0)
        self.lbDates.SetSelection(0)

        self.lbCams.InsertItems(allCameras, 0)
        self.lbCams.SetSelection(0)

        self.filterVideosInfo(None)

    def filterVideosInfo(self, evt):
        self.lbVideos.DeleteAllItems()

        scanned = 0
        id = 0
        numVid = sum(len(videos) for videos in self.dhfs.fragsInVideos)
        for pIndx in range(self.dhfs.getNumPartitions()):
            for dIndx in self.dhfs.getMainDescs(pIndx):
                date  = self.dhfs.getBeginDate(pIndx, dIndx)
                begin = self.dhfs.getBeginTime(pIndx, dIndx)
                end   = self.dhfs.getEndTime(pIndx, dIndx)
                cam   = f"{self.dhfs.getCamera(pIndx, dIndx):02d}"
                size  = f"{self.dhfs.getVideoSize(pIndx, dIndx)/1024**2:.2f} MB"

                selectedDate = self.lbDates.GetStringSelection()
                selectedCam = self.lbCams.GetStringSelection()

                if (((selectedDate == "All") or (selectedDate == date)) and
                    ((selectedCam == "All") or (selectedCam == cam))):
                    self.lbVideos.InsertItem(id, str(pIndx))
                    self.lbVideos.SetItem(id, 1, str(dIndx))
                    self.lbVideos.SetItem(id, 2, date)
                    self.lbVideos.SetItem(id, 3, begin)
                    self.lbVideos.SetItem(id, 4, end)
                    self.lbVideos.SetItem(id, 5, cam)
                    self.lbVideos.SetItem(id, 6, size)
                    id += 1

                scanned += 1
                if scanned % 50 == 0:
                    self.SetStatusText("Listing Videos... {0:.2f}%".format((scanned/numVid) * 100))

        self.SetStatusText("Done!!!!!!!!!")

    def getSavePath(self):
        self.dlg = wx.DirDialog(self, "Choose a dir to save...", os.getcwd(),
                        wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        return self.dlg.GetPath() if self.dlg.ShowModal() == wx.ID_OK else None

    def saveVideos(self):
        if not self.dhfs.imgLoaded:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        dirToSave = self.getSavePath()
        if dirToSave:
            nVideos = 0
            for lbVideoIdx in range(self.lbVideos.GetItemCount()):
                if self.lbVideos.IsSelected(lbVideoIdx):
                    pIndx = int(self.lbVideos.GetItemText(lbVideoIdx, 0))
                    vIndx = int(self.lbVideos.GetItemText(lbVideoIdx, 1))
                    self.dhfs.saveVideoAt(pIndx, vIndx, dirToSave, self.SetStatusText)
                    nVideos += 1
            self.SetStatusText(f"Done!!!")

            if nVideos == 0:
                wx.MessageBox("Choose one or more videos!!!", version,
                                    style=wx.OK | wx.ICON_INFORMATION)

    def exportVideosMetaData(self):
        if not self.dhfs.imgLoaded:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        fileDialog = wx.FileDialog(self, "Save Videos Metadata file",
                        wildcard="csv (*.csv)|*.csv",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return

        fdOut = open (fileDialog.GetPath(), "w")
        fdOut.write(";".join(self.lbVidHeaders)+"\n")
        nVideos = 0
        for lbVideoIdx in range(self.lbVideos.GetItemCount()):
            if self.lbVideos.IsSelected(lbVideoIdx):
                metaData = ";".join([self.lbVideos.GetItemText(lbVideoIdx, i)
                                        for i in range(7)])
                fdOut.write(metaData+"\n")
                nVideos += 1
        fdOut.close()

        if nVideos == 0:
            wx.MessageBox("Choose one or more videos!!!", version,
                            style=wx.OK | wx.ICON_INFORMATION)

    def saveSlacks(self):
        if not self.dhfs.imgLoaded:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        dirToSave = self.getSavePath()
        if dirToSave:
            nSlack = 0
            for lbVideoIdx in range(self.lbVideos.GetItemCount()):
                if self.lbVideos.IsSelected(lbVideoIdx):
                    pIndx = int(self.lbVideos.GetItemText(lbVideoIdx, 0))
                    vIndx = int(self.lbVideos.GetItemText(lbVideoIdx, 1))
                    self.dhfs.saveSlackAt(nSlack, pIndx, vIndx, dirToSave, self.SetStatusText)
                    nSlack += 1
            self.SetStatusText(f"Done!!!")

            if nSlack == 0:
                wx.MessageBox("Choose one or more slacks!!!", version,
                                    style=wx.OK | wx.ICON_INFORMATION)

    def saveRecovered(self):
        if not self.dhfs.imgLoaded:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        dirToSave = self.getSavePath()
        if dirToSave:
            nVideos = 0
            for pIndx in range(self.dhfs.getNumPartitions()):
                nVideos += self.dhfs.saveRecVideos(pIndx, dirToSave, self.SetStatusText)
            self.SetStatusText(f"Done!!!")
            wx.MessageBox(f"{nVideos} Video(s) sucessfully saved.", style=wx.OK)

    def saveLogs(self):
        if not self.dhfs.imgLoaded:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        fileDialog = wx.FileDialog(self, "Save Log file",
                        wildcard="log (*.log)|*.log",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if fileDialog.ShowModal() == wx.ID_CANCEL: return

        fileToSave = fileDialog.GetPath()
        self.dhfs.saveLogs (fileToSave)

    def config(self):
        wx.MessageBox("You will be inquired to open one config file.\n\n"+
                      "This file should have the format:\n"+
                      "key1 = VALUE1\n"+
                      "key2 = VALUE2\n"+
                      "key3 = VALUE3\n\n"+
                      "At the moment only two keys are supported:\n"+
                      "CARVE_SIGNAT=regex python to use in video carving\n"+
                      "DEBUG=True or False",
                      "Info", style=wx.OK)

        self.dlg = wx.FileDialog(self, "Escolha um arquivo", os.getcwd(), "")
        if self.dlg.ShowModal() == wx.ID_OK:
            fileName = self.dlg.GetPath()
            try:
                self.dhfs.setConfig(fileName)
            except Exception as e:
                wx.MessageBox("Error in processing config file:\n"+str(e),
                            "Info", style=wx.OK)

DEBUG = True
if __name__ == '__main__':
    app = wx.App()
    main = DVRExtractor(None)
    app.MainLoop()
