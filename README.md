# dhfs_extractor
An small utility to extract videos, logs e slacks in DHFS4.1 file system

This program can identify and recover videos stored in a DHFS4.1 filesystem (common in chinese's DVR). 

Some features of dhfd_extractor

* Recognizes partitions and can extract all videos on them
* Extract slacks associated to each video
* Identify and save logs stored in file system
* Recover videos partially overwritten
* Recover videos after disk format (to be improved)

When running under Windows only raw (dd) images are suported. In Linux you can access evidence disks or images (dd). 
DHFS4.1 extractor is offered to you under GPL license by GALILEU Batista (galileu.batista@ifrn.edu.br)

You must retain author name in all circunstances in which the program is used. He has made the best to get a correct operation, but no warranty implicit or explicit is provided.
