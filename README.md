# dhfs_extractor
A small utility to extract videos, logs, and slacks in the DHFS4.1 file system.

This program can identify and recover videos stored in a DHFS4.1 file system (commonly found in Chinese DVRs).

Some features of dhfs_extractor:

* Recognizes partitions and can extract all videos on them.
* Extracts slacks associated with each video.
* Identifies and saves logs stored in the file system.
* Recovers partially overwritten videos.
* Recovers videos after disk format (to be improved).

When running under Windows, only raw (dd) images are supported. In Linux, you can access evidence disks or images (dd).
DHFS4.1 extractor is offered to you under the MIT license by GALILEU Batista (galileu.batista@ifrn.edu.br).

You must retain the author's name in all circumstances in which the program is used. He has done his best to ensure correct operation, but no implicit or explicit warranty is provided.
