#!/usr/bin/python
import time
import subprocess
import urllib.request

def reload_rclone():
    try:
        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf",
                                   filename="/storage/.config/rclone/rclone.conf")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_tvshows_1.service",
                                   filename="/storage/.config/system.d/rclone_tvshows_1.service")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_tvshows_2.service",
                                   filename="/storage/.config/system.d/rclone_tvshows_2.service")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_videos_1.service",
                                   filename="/storage/.config/system.d/rclone_videos_1.service")

        urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone_videos_2.service",
                                   filename="/storage/.config/system.d/rclone_videos_2.service")

        subprocess.call(["systemctl", "daemon-reload"])
        subprocess.call(["systemctl", "restart", "rclone_tvshows_1"])
        subprocess.call(["systemctl", "restart", "rclone_tvshows_2"])
        subprocess.call(["systemctl", "restart", "rclone_videos_1"])
        subprocess.call(["systemctl", "restart", "rclone_videos_2"])

    except:
        time.sleep(5)
        reload_rclone()

reload_rclone()

# Execute every 12 hours
while True:
    time.sleep(23600)
    reload_rclone()



