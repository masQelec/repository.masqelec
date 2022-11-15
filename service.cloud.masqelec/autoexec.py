import subprocess
import urllib.request

def launch():
	urllib.request.urlretrieve("https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf", filename="/storage/.config/rclone/rclone.conf")

	subprocess.call(["systemctl", "daemon-reload"])
	subprocess.call(["systemctl", "restart", "rclone_tvshows_1"])
	subprocess.call(["systemctl", "restart", "rclone_tvshows_2"])
	subprocess.call(["systemctl", "restart", "rclone_videos_1"])
	subprocess.call(["systemctl", "restart", "rclone_videos_2"])

launch()
