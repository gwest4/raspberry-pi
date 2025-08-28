import os

path = "/"
(f_bsize, f_frsize, f_blocks, f_bfree, f_bavail, f_files, f_ffree, f_favail, f_flag, f_namemax) = os.statvfs(path)

# free blocks available * fragment size
bytes_avail = (f_bavail * f_frsize)
kilobytes_avail = bytes_avail / 1024
print("{} kilobytes available at {}".format(kilobytes_avail, path))