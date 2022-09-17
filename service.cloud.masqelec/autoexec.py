import subprocess
import urllib

def launch():
	urllib.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf", filename="/storage/.config/rclone/rclone.conf")
	
	try:
		xbmc.log("Launching script", xbmc.LOGDEBUG)
		subprocess.call(["systemctl", "daemon-reload"])      
		subprocess.call(["systemctl", "restart", "rclone_iptv"])
		subprocess.call(["systemctl", "restart", "rclone_recordings"])
		subprocess.call(["systemctl", "restart", "rclone_tvshows_1"])
		subprocess.call(["systemctl", "restart", "rclone_tvshows_2"])
		subprocess.call(["systemctl", "restart", "rclone_videos_1"])
		subprocess.call(["systemctl", "restart", "rclone_videos_2"])
        
	except:
		xbmc.log("Failed to launch", xbmc.LOGDEBUG)

launch()
