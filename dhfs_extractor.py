# encoding: utf-8

version = "DHFS4.1 Extractor 0.6"
copyright = \
'''
This program identifies and recovers videos from DHFS4.1 filesystems, which are common in Chinese DVRs.

Under Windows, use 'Open Image' to select a data source. Under Linux, you can also access disk devices directly.

DHFS4.1 Extractor is provided under the MIT license by Galileu Batista (galileu.batista@ifrn.edu.br).

The author has made every effort to ensure correct operation, but no warranty, implicit or explicit, is provided.
'''

from dhfs41 import *
import sys
import wx
import wx.lib.mixins.listctrl as listmix
import os
import time

class dhfs_extractor(wx.Frame, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetSize(840, 530)
        self.dhfs = DHFS41(DEBUG=DEBUG)
        self.create_gui()
        self.itemDataMap = {}                # ID -> tuple of column values
        listmix.ColumnSorterMixin.__init__(self, len(self.video_list_headers))

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def GetListCtrl(self):
        return self.video_list

    def GetSortImages(self):
        # optional: provide down/up bitmaps for header arrows
        art = wx.ArtProvider
        return (art.GetBitmap(wx.ART_GO_DOWN), art.GetBitmap(wx.ART_GO_UP))

    def create_gui(self):
        art = wx.ArtProvider
        self.CreateStatusBar(3)
        self.SetStatusWidths([-2, -1, -2])
        self.SetStatusText("", 0)
        self.SetStatusText("", 1)
        self.SetStatusText("", 2)

        # ToolBar
        toolbar_font = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize() - 1,
                               wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.toolbar = wx.ToolBar(self, wx.ID_ANY, style=wx.TB_TEXT)
        self.toolbar.SetFont(toolbar_font)
        def center_label(label):
            # Center each line for multi-line labels
            return "\n".join([line.center(8) for line in label.split("\n")])

        self.toolbar.AddTool(toolId=101, label=center_label("Open\nImage"), shortHelp="Open a disk image file",
                             bitmap=art.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
        if os.name != 'nt':
            self.toolbar.AddTool(toolId=102, label=center_label("Open\nDisk"), shortHelp="Open a physical disk",
                                 bitmap=art.GetBitmap(wx.ART_HARDDISK, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=103, label=center_label("Disk\nInfo"), shortHelp="Display information about the loaded disk",
                             bitmap=art.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=104, label=center_label("Save\nSelected"), shortHelp="Save the selected videos",
                             bitmap=art.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=105, label=center_label("Export\nMetadata"), shortHelp="Export video metadata to a CSV file",
                             bitmap=art.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=106, label=center_label("Save\nSlack"), shortHelp="Save the slack space of the selected videos",
                             bitmap=wx.Bitmap(self.resource_path("icons/slack.png")))
        self.toolbar.AddTool(toolId=107, label=center_label("Recover\nVideos"), shortHelp="Recover deleted or corrupted videos",
                             bitmap=wx.Bitmap(self.resource_path("icons/recover.png")))
        self.toolbar.AddTool(toolId=108, label=center_label("Save\nLogs"), shortHelp="Save the filesystem logs",
                             bitmap=art.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=109, label=center_label("Settings"), shortHelp="Configure the application",
                             bitmap=art.GetBitmap(wx.ART_EDIT, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=110, label=center_label("About"), shortHelp="About this application",
                             bitmap=art.GetBitmap(wx.ART_HELP, wx.ART_TOOLBAR))
        self.toolbar.AddTool(toolId=111, label=center_label("Exit"), shortHelp="Exit the application",
                             bitmap=art.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_toolbar_event)
        self.toolbar.Realize()
        self.SetToolBar(self.toolbar)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        splitter = wx.SplitterWindow(self, style=wx.SP_NOSASH)
        main_sizer.Add(splitter, 1, wx.EXPAND)

        self.right_panel = wx.Panel(splitter)
        self.left_panel = wx.Panel(splitter)
        splitter.SplitVertically(self.left_panel, self.right_panel, sashPosition=220)

        # Left panel sizer
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        date_label = wx.StaticText(self.left_panel, label="Date")
        self.date_list = wx.ListBox(self.left_panel, style=wx.LB_SINGLE)
        left_sizer.Add(date_label, 0, wx.ALL, 5)
        left_sizer.Add(self.date_list, 1, wx.EXPAND | wx.ALL, 5)
        
        camera_label = wx.StaticText(self.left_panel, label="Camera")
        self.camera_list = wx.ListBox(self.left_panel, style=wx.LB_SINGLE)
        left_sizer.Add(camera_label, 0, wx.ALL, 5)
        left_sizer.Add(self.camera_list, 1, wx.EXPAND | wx.ALL, 5)
        self.left_panel.SetSizer(left_sizer)

        # Right panel sizer
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.video_list = wx.ListCtrl(self.right_panel, -1, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.video_list.SetBackgroundColour(wx.WHITE)
        self.video_list_headers = ["Partition", "ID", "Date", "Start Time", "End Time", "Camera", "Size"]
        for i in range(len(self.video_list_headers)):
            self.video_list.InsertColumn(i + 1, self.video_list_headers[i],
                                         wx.LIST_FORMAT_LEFT if i != 6 else wx.LIST_FORMAT_RIGHT,
                                         width=wx.LIST_AUTOSIZE)
            
        right_sizer.Add(self.video_list, 1, wx.EXPAND | wx.ALL, 5)

        self.selection_info = wx.StaticText(self.right_panel, label="")
        
        right_sizer.Add(self.selection_info, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
        self.right_panel.SetSizer(right_sizer)

        self.SetSizer(main_sizer)
        self.SetTitle(version)
        self.Centre()

        self.Bind(wx.EVT_LISTBOX, self.filter_videos, self.date_list)
        self.Bind(wx.EVT_LISTBOX, self.filter_videos, self.camera_list)
        
        self.video_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.update_selection_info)
        self.video_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.update_selection_info)

        self.Show(True)

    def on_toolbar_event(self, e):
        ID_OPEN_IMAGE = 101
        ID_OPEN_DISK = 102
        ID_INFO = 103
        ID_EXTRACT = 104
        ID_METADATA = 105
        ID_SLACK = 106
        ID_RECOVER = 107
        ID_LOGS = 108
        ID_CONFIG = 109
        ID_ABOUT = 110
        ID_EXIT = 111

        if   e.GetId() == ID_OPEN_IMAGE: self.on_load_image()
        elif e.GetId() == ID_OPEN_DISK:  self.load_disk()
        elif e.GetId() == ID_INFO:       self.show_metadata()
        elif e.GetId() == ID_EXTRACT:    self.save_videos()
        elif e.GetId() == ID_METADATA:   self.export_videos_metadata()
        elif e.GetId() == ID_SLACK:      self.save_slacks()
        elif e.GetId() == ID_RECOVER:    self.save_recovered()
        elif e.GetId() == ID_LOGS:       self.save_logs()
        elif e.GetId() == ID_CONFIG:     self.config()
        elif e.GetId() == ID_ABOUT:      self.show_about()
        elif e.GetId() == ID_EXIT:       self.Close()

    def update_selection_info(self, event=None):
        selected_count = 0
        total_size = 0.0
        for i in range(self.video_list.GetItemCount()):
            if self.video_list.IsSelected(i):
                selected_count += 1
                size_str = self.video_list.GetItemText(i, 6)
                if "MB" in size_str:
                    total_size += float(size_str.replace("MB", "").strip()) / 1024
                elif "GB" in size_str:
                    total_size += float(size_str.replace("GB", "").strip())

        if selected_count == 0:
            self.selection_info.SetLabel("")
        elif selected_count == 1:
            self.selection_info.SetLabel(f"({total_size:.1f} GB)")
        else:
            self.selection_info.SetLabel(f"{selected_count} selected clips ({total_size:.1f} GB)")

    def clear_ui(self):
        self.date_list.Clear()
        self.camera_list.Clear()
        self.video_list.DeleteAllItems()
        self.selection_info.SetLabel("")
        self.SetStatusText("", 0)
        self.SetStatusText("", 1)
        self.SetStatusText("", 2)

    def load_disk(self):
        self.on_load_image()

    def on_load_image(self):
        self.clear_ui()

        dialog = wx.FileDialog(self, "Choose a file", os.getcwd(), "")
        if dialog.ShowModal() == wx.ID_OK:
            file_path = dialog.GetPath()

            self.SetStatusText("Loading image...")
            if self.dhfs.load_image(file_path):
                self.show_videos_info()
            else:
                self.SetStatusText("")
                wx.MessageBox("This does not appear to be a DHFS 4.1 filesystem.", "Invalid Filesystem",
                                style=wx.OK | wx.ICON_ERROR)

    def show_about(self):
        wx.MessageBox(copyright, "About", style=wx.OK)

    def show_metadata(self):
        message = self.dhfs.get_image_metadata()
        if message:
            wx.MessageBox(message, "Disk Information", style=wx.OK)
        else:
            wx.MessageBox("No image or disk loaded.", "Warning", style=wx.OK | wx.ICON_WARNING)

    def show_videos_info(self):
        all_video_dates  = []
        all_cameras      = []
        for p_idx in range(self.dhfs.get_num_partitions()):
            for d_idx in self.dhfs.get_main_descs(p_idx):
                video_date = self.dhfs.get_begin_date(p_idx, d_idx)
                if video_date not in all_video_dates:
                    all_video_dates.append(video_date)

                camera = f"{self.dhfs.get_camera(p_idx, d_idx):02d}"
                if camera not in all_cameras:
                    all_cameras.append(camera)

        all_video_dates.sort()
        all_video_dates.insert(0, "All")
        all_cameras.sort()
        all_cameras.insert(0, "All")

        self.date_list.InsertItems(all_video_dates, 0)
        self.date_list.SetSelection(0)

        self.camera_list.InsertItems(all_cameras, 0)
        self.camera_list.SetSelection(0)

        self.filter_videos(None)

    def filter_videos(self, evt):
        self.video_list.DeleteAllItems()

        videos_scanned = 0
        video_idx = 0
        total_videos = sum(len(videos) for videos in self.dhfs.frags_in_videos)
        for part_idx in range(self.dhfs.get_num_partitions()):
            for desc_idx in self.dhfs.get_main_descs(part_idx):
                date = self.dhfs.get_begin_date(part_idx, desc_idx)
                begin = self.dhfs.get_begin_time(part_idx, desc_idx)
                end = self.dhfs.get_end_time(part_idx, desc_idx)
                cam = f"{self.dhfs.get_camera(part_idx, desc_idx):02d}"
                size = f"{self.dhfs.get_video_size(part_idx, desc_idx) / 1024 ** 2:.2f} MB"

                selected_date = self.date_list.GetStringSelection()
                selected_cam = self.camera_list.GetStringSelection()

                if (((selected_date == "All") or (selected_date == date)) and
                        ((selected_cam == "All") or (selected_cam == cam))):
                    self.video_list.InsertItem(video_idx, str(part_idx))
                    self.video_list.SetItem(video_idx, 1, str(desc_idx))
                    self.video_list.SetItem(video_idx, 2, date)
                    self.video_list.SetItem(video_idx, 3, begin)
                    self.video_list.SetItem(video_idx, 4, end)
                    self.video_list.SetItem(video_idx, 5, cam)
                    self.video_list.SetItem(video_idx, 6, size)
                        # After inserting and SetItem(…) for columns 1–6:
                    self.video_list.SetItemData(video_idx, video_idx)
                    self.itemDataMap[video_idx] = (
                        part_idx,
                        desc_idx,
                        date,
                        begin,
                        end,
                        int(cam),         # convert camera string to int for numeric sort
                        float(size.split()[0])
                    )

                    video_idx += 1

                videos_scanned += 1
                if videos_scanned % 50 == 0:
                    self.SetStatusText(f"Listing Videos... {(videos_scanned / total_videos) * 100:.2f}%")

        self.SetStatusText("Done!")
        self.SetStatusText(f"{video_idx} items", 1)
        self.selection_info.SetLabel("")

    def get_save_path(self):
        self.dlg = wx.DirDialog(self, "Choose a directory to save the files...", os.getcwd(),
                        wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        return self.dlg.GetPath() if self.dlg.ShowModal() == wx.ID_OK else None

    def save_videos(self):
        if not self.dhfs.img_loaded:
            wx.MessageBox("No image/disk loaded!", "Warning", style=wx.OK)
            return

        dir_save = self.get_save_path()
        if dir_save:
            total_videos = 0
            for lb_video_idx in range(self.video_list.GetItemCount()):
                if self.video_list.IsSelected(lb_video_idx):
                    part_idx = int(self.video_list.GetItemText(lb_video_idx, 0))
                    vid_idx = int(self.video_list.GetItemText(lb_video_idx, 1))
                    self.dhfs.save_video_at(part_idx, vid_idx, dir_save, self.SetStatusText)
                    total_videos += 1
            self.SetStatusText(f"Done. {total_videos} video(s) saved.")

    def export_videos_metadata(self):
        if not self.dhfs.img_loaded:
            wx.MessageBox("No image/disk loaded!", "Warning", style=wx.OK)
            return

        file_dialog = wx.FileDialog(self, "Save Video Metadata",
                                     wildcard="csv (*.csv)|*.csv",
                                     style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if file_dialog.ShowModal() == wx.ID_CANCEL: return

        with open(file_dialog.GetPath(), "w") as fd_out:
            fd_out.write(";".join(self.video_list_headers) + "\n")
            total_videos = 0
            for lb_video_idx in range(self.video_list.GetItemCount()):
                if self.video_list.IsSelected(lb_video_idx):
                    metadata = ";".join([self.video_list.GetItemText(lb_video_idx, i)
                                            for i in range(7)])
                    fd_out.write(metadata + "\n")
                    total_videos += 1

        if total_videos == 0:
            wx.MessageBox("Please select one or more videos to export.", "No Videos Selected",
                            style=wx.OK | wx.ICON_INFORMATION)

    def save_slacks(self):
        if not self.dhfs.img_loaded:
            wx.MessageBox("No image/disk loaded!", "Warning", style=wx.OK)
            return

        dir_save = self.get_save_path()
        if dir_save:
            total_slacks = 0
            for lb_video_idx in range(self.video_list.GetItemCount()):
                if self.video_list.IsSelected(lb_video_idx):
                    part_idx = int(self.video_list.GetItemText(lb_video_idx, 0))
                    video_idx = int(self.video_list.GetItemText(lb_video_idx, 1))
                    self.dhfs.save_slack_at(total_slacks, part_idx, video_idx, dir_save, self.SetStatusText)
                    total_slacks += 1
            self.SetStatusText(f"Done. {total_slacks} slack file(s) saved.")

    def save_recovered(self):
        if not self.dhfs.img_loaded:
            wx.MessageBox("No image/disk loaded!", "Warning", style=wx.OK)
            return

        dir_save = self.get_save_path()
        if dir_save:
            total_videos = 0
            for part_idx in range(self.dhfs.get_num_partitions()):
                total_videos += self.dhfs.save_recovered_videos(part_idx, dir_save, self.SetStatusText)
            self.SetStatusText(f"Done. {total_videos} video(s) recovered.")
            wx.MessageBox(f"{total_videos} Video(s) sucessfully saved.", style=wx.OK)

    def save_logs(self):
        if not self.dhfs.img_loaded:
            wx.MessageBox("No image/disk loaded!", "Warning", style=wx.OK)
            return

        file_dialog = wx.FileDialog(self, "Save Log file",
                        wildcard="log (*.log)|*.log",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if file_dialog.ShowModal() == wx.ID_CANCEL: return

        file_save = file_dialog.GetPath()
        self.dhfs.save_logs (file_save)

    def config(self):
        wx.MessageBox("This will open a configuration file.\n\n" +
                      "The file should be in the following format:\n"+
                      "key1 = VALUE1\n"+
                      "key2 = VALUE2\n"+
                      "key3 = VALUE3\n\n"+
                      "Currently, the following keys are supported:\n"+
                      "CARVE_SIGNAT: A Python regex for video carving.\n"+
                      "DEBUG: True or False.",
                      "Configuration", style=wx.OK)

        self.dlg = wx.FileDialog(self, "Choose a File", os.getcwd(), "")
        if self.dlg.ShowModal() == wx.ID_OK:
            file_name = self.dlg.GetPath()
            try:
                self.dhfs.set_config(file_name)
            except Exception as e:
                wx.MessageBox("Error processing config file:\n" + str(e), "Info", style=wx.OK)

DEBUG = True

def main():
    app = wx.App()
    main_frame = dhfs_extractor(None)
    app.MainLoop()

if __name__ == '__main__':
    main()
