import subprocess
import xbmcgui
import xbmc
import xbmcaddon
import urllib
import tarfile
import shutil
import time
import os
import distutils.dir_util


def launch():
    
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
    __icon__ = __addon__.getAddonInfo('icon')
 

    urllib.urlretrieve("https://raw.githubusercontent.com/masQelec/epg.masqelec/master/satellite/epg.tar.gz", filename="/storage/epg.tar.gz")
    
    try:        
        subprocess.call(["systemctl", "daemon-reload"]) # make sure it's executable
        subprocess.call(["systemctl", "stop", "service.tvheadend43"]) # make sure it's executable
         
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/bouquet', ignore_errors=True)
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/channel', ignore_errors=True)
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/epggrab', ignore_errors=True)
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/input', ignore_errors=True)
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/profile', ignore_errors=True)
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/service_mapper', ignore_errors=True)
        shutil.rmtree('/storage/.kodi/userdata/addon_data/service.tvheadend43/xmltv', ignore_errors=True)
        
        os.mkdir('/storage/tmp')
           
        subprocess.call(["tar", "-xzvf", "/storage/epg.tar.gz", "--directory", "/storage/tmp"])

	time.sleep(1)
	
	distutils.dir_util.copy_tree('/storage/tmp', '/storage')
	
        subprocess.call(["systemctl", "restart", "service.tvheadend43"]) # make sure it's executable
        
        time.sleep(1)
        
        shutil.rmtree('/storage/tmp', ignore_errors=True)
        os.remove("/storage/epg.tar.gz")

    except:
        xbmcgui.Dialog().ok("Failed to launch", "Failed to launch script %s" % cmd)

launch()
