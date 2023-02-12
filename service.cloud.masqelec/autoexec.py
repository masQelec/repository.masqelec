#!/usr/bin/python
import time
import subprocess
import urllib

def reload_rclone():
        urllib.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf",filename="rclone.conf")

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
