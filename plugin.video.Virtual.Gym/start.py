# -*- coding: utf-8 -*-

"""

			𝐕𝐈𝐑𝐓𝐔𝐀𝐋 𝐆𝐘𝐍 
		𝐁𝐘 𝐍𝐄𝐓𝐀𝐈 𝐓𝐄𝐀𝐌 𝟐𝟎𝟐𝟎
		
"""
import urllib , urllib2 , sys , re , os , unicodedata
import xbmc , xbmcgui , xbmcplugin , xbmcaddon
import cookielib , webbrowser
import traceback , datetime , HTMLParser , httplib
import resolveurl
import cookielib , base64
import requests
import plugintools
import codecs

addon = xbmcaddon.Addon('plugin.video.Virtual.Gym')
addon_version = addon.getAddonInfo('version')		
plugin_handle = int(sys.argv[1])
mysettings = xbmcaddon.Addon(id = 'plugin.video.Virtual.Gym')
profile = mysettings.getAddonInfo('profile')
home = mysettings.getAddonInfo('path')
fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
MenuColor = addon.getSetting('MenuColor')
Fontcolor = addon.getSetting('Fontcolor')

## AQUI VAN TUS IMAGENES
patry = 'https://yt3.ggpht.com/a/AATXAJzbx1rQAKFcQpKPKqkoF94xv42HiN7cvcTUrA=s900-c-k-c0xffffffff-no-rj-mo'
inactivas = 'https://yt3.ggpht.com/a/AATXAJwycLZKRIaU_3GU8JB6neioNdYbb5z-g9dirw=s288-c-k-c0xffffffff-no-rj-mo'
## AQUI VAN TUS ENLACES -> Pastebin a la lista de categorias ...

ejercicios1 = "https://pastebin.com/raw/pq5Z6NKN"
ejercicios2 = "https://pastebin.com/raw/vZ7vnD41"

## THESE ARE YOUR REGEX'S

m3u_regex = 'img="(.+?)",(.+)\s*(.+)\s*'

## THIS IS JUST A FILLER FOR THE URL ON MAION CATEGORIES
u_tube = 'http://www.youtube.com'

def removeAccents(s):
## THIS REMOVES ACCENTS FROM TEXT SO THAT PYTHON CAN READ IT
	return ''.join((c for c in unicodedata.normalize('NFD', s.decode('utf-8')) if unicodedata.category(c) != 'Mn'))
					
def read_file(file):
## THIS FUNCTION READS THE SOURCE FILES
    try:
        f = open(file, 'r')
        content = f.read()
        f.close()
        return content
    except:
        pass

def make_request(url):
## THIS FUNCTION GETS THE FILES FROM URL AND READS THEM TO CACHE/MEM
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0')
		response = urllib2.urlopen(req)	  
		link = response.read()
		response.close()  
		return link
	except urllib2.URLError, e:
		print 'We failed to open "%s".' % url
		if hasattr(e, 'code'):
			print 'We failed with error code - %s.' % e.code	
		if hasattr(e, 'reason'):
			print 'We failed to reach a server.'
			print 'Reason: ', e.reason
			

			
def main():

	add_dir('[COLOR %s]Patry Jordan[/COLOR]' % Fontcolor, u_tube, 2, patry, fanart)
	add_dir('[COLOR %s]Inactiva, Tu gimnasio en casa[/COLOR]' % Fontcolor, u_tube, 3, inactivas, fanart)

			
def Calentamiento():

	content2 = make_request(ejercicios1)
	match = re.compile(m3u_regex).findall(content2)
	for iconimage, name, url in match:
		try:
				
			add_dir2(name, url, 20, iconimage, fanart)
			
		except:
			pass
def inactiva():

	content = make_request(ejercicios2)
	match = re.compile(m3u_regex).findall(content)
	for iconimage, name, url in match:
		try:
				
			add_dir2(name, url, 20, iconimage, fanart)
			
		except:
			pass

def m3u_play(name,url):	

	content = make_request(url)
	match = re.compile(m3u_regex).findall(content)
	for iconimage, name, url in match:
		try:	

			name = name.encode('utf-8')		
			url = url.replace('"', ' ').replace('&amp;', '&').strip()
			Fontcolor = addon.getSetting('Fontcolor')
			name = '[COLOR %s]' % Fontcolor + name + '[/COLOR]'
			add_link(name, url, 1, iconimage, fanart)
			
		except:
			pass
			
def PLAY(name,url):	
	
	import urlresolver
	from urlresolver import common
    
	hmf = urlresolver.HostedMediaFile(url)

	if not hmf:
		xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR], Enlace no soportado para: [COLOR orange]" +name+ "[/COLOR] ,7500)")
		return False


	try:
		stream_url = hmf.resolve()
		if not stream_url or not isinstance(stream_url, basestring):
			try: msg = stream_url.msg
			except: msg = url
			raise Exception(msg)
	except Exception as e:
		try: msg = str(e)
		except: msg = url
		xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR], [COLOR red]Enlace no encontrado:[/COLOR] [COLOR orange]" +name+ "[/COLOR] ,7500)")            
		return False
   

	xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR],[COLOR lime] reproduciendo: [/COLOR][COLOR orange]" +name+ "[/COLOR] ,7500)")	
	listitem = xbmcgui.ListItem(path=stream_url)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)


def play(name,url):	
	
	import resolveurl
	resolved = resolveurl.resolve(url)
		
	if not resolved:
		xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR], Enlace no soportado para: [COLOR orange]" +name+ "[/COLOR] ,5000)")
		return False

	try:
		dp = xbmcgui.DialogProgress()
		dp.create('Realstream:','Iniciando ...')
		dp.update(30,'RESOLVEURL:','Conectando al servidor ...')
		xbmc.sleep(1000)
		stream_url = resolved.resolve(url)
		if not stream_url or not isinstance(stream_url, basestring):
			try: msg = stream_url.msg
			except: msg = url
			raise Exception(msg)
					
	except Exception as e:
		try: msg = str(e)
		except: msg = url
		dp.update(45,'RESOLVEURL:','Reiniciando ... ')
		xbmc.sleep(1000)
		xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR], Episodio no disponible.  ,3000)")            
		dp.close()
						
	dp.update(60,'RESOLVEURL:','Comprobando que existe el enlace.')
	xbmc.sleep(500)
	dp.update(75,'RESOLVEURL:','Resolviendo enlace ...')
	xbmc.sleep(500)
	dp.update(95,'RESOLVEURL:','Encontrado ...')
	xbmc.sleep(500)
	dp.update(100,'RESOLVEURL:','Disfrute de este capitulo!')
	dp.close()
	notificar = addon.getSetting('notificar')
	listitem = xbmcgui.ListItem(path=stream_url)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
	

def PLAYVIDEO(name,url):

		if '[Youtube]' in name:
		
			url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url
			media_url = url
			item = xbmcgui.ListItem(trailer, path = media_url)
			xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
	
			
		else:
		
			import resolveurl
		
			hmf = resolveurl.HostedMediaFile(url)

			if not hmf:
				xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR], Enlace no soportado para: [COLOR orange]" +name+ "[/COLOR] ,7500)")
				return False


			try:
				stream_url = hmf.resolve()
				if not stream_url or not isinstance(stream_url, basestring):
					try: msg = stream_url.msg
					except: msg = url
					raise Exception(msg)
			except Exception as e:
				try: msg = str(e)
				except: msg = url
				xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR], [COLOR red]Enlace no encontrado:[/COLOR] [COLOR orange]" +name+ "[/COLOR] ,7500)")            
				return False
   
			notificar = addon.getSetting('notificar')
			if notificar == 'true':
				xbmc.executebuiltin("XBMC.Notification([COLOR yellow]Virtual Gym[/COLOR],[COLOR lime] reproduciendo: [/COLOR][COLOR orange]" +name+ "[/COLOR] ,7500)")	
			listitem = xbmcgui.ListItem(path=stream_url)
			xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)

		
		return

def get_params():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring)>= 2:
		params = sys.argv[2]
		cleanedparams = params.replace('?', '')
		if (params[len(params)-1] == '/'):
			params = params[0:len(params)-2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0]] = splitparams[1]
	return param

def add_dir(name, url, mode, iconimage, fanart):
## Añadre los directorios del menu. Con sus respetivos iconos y fanart y los enlaces a las acciones a enprender por el addon.
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&iconimage=" + urllib.quote_plus(iconimage)
	ok = True
	liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": name } )
	liz.setProperty('fanart_image', fanart)	
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)
	return ok
	
def add_dir2(name, url, mode, iconimage, fanart):
## Añadre los directorios del menu. Con sus respetivos iconos y fanart y los enlaces a las acciones a enprender por el addon.
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&iconimage=" + urllib.quote_plus(iconimage)
	ok = True
	liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": name} )
	liz.setProperty('fanart_image', fanart)	
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)
	return ok

def add_link(name, url, mode, iconimage, fanart):
## ADDS THE LINKS
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&iconimage=" + urllib.quote_plus(iconimage)	
	liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": name } )
	liz.setProperty('fanart_image', fanart)
	liz.setProperty('IsPlayable', 'true') 
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz) 

def add_link_info(name, iconimage, fanart):
## ADDS THE TEXT ONLY LINKS WITH NO CLICK ACTION
	u = sys.argv[0] + "&name=" + urllib.quote_plus(name) + "&iconimage=" + urllib.quote_plus(iconimage)	
	liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": name } )
	liz.setProperty('fanart_image', fanart)
	liz.setProperty('IsPlayable', 'false') 
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz) 
	
def add_link_dummy(iconimage, fanart):
## ADDS THE BLANK SPACER IN MENU WITH NO CLICK ACTION
	u = sys.argv[0] + "&iconimage=" + urllib.quote_plus(iconimage)	
	liz = xbmcgui.ListItem(iconImage = "DefaultVideo.png", thumbnailImage = iconimage)
	liz.setProperty('fanart_image', fanart)
	liz.setProperty('IsPlayable', 'false') 
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz)  

def iniciar():

	if addon == 'plugin.video.Virtual.Gym':
	
		main()
		
	else:
	
	
		xbmc.executebuiltin("XBMC.Notification(Virtual Gym, [COLOR red]Virtual Gym no puede inciarse !![/COLOR] [COLOR orange] Resinstale de nuevo desde repositorio Netai.[/COLOR] ,7500)")   
		
		
		return

params = get_params()
url = None
name = None
mode = None
iconimage = None
description = None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass
try:
	iconimage = urllib.unquote_plus(params["iconimage"])
except:
	pass  
try:
	description = urllib.unquote_plus(params["description"])
except:
	pass

print "Mode: " + str(mode)
print "URL: " + str(url)
print "Name: " + str(name)
print "iconimage: " + str(iconimage)		



if mode == None or url == None or len(url) < 1:

	try:

		xbmc.executebuiltin("XBMC.Notification([COLOR white]Virtual Gym[/COLOR], [COLOR green]Cargando contenido ...[/COLOR] ,5000)")
	
	except:
		pass
	
	main()
	
elif mode == 1:
	 PLAY(name,url)

elif mode == 2:
	Calentamiento()
	
elif mode == 3:
	inactiva()
	
elif mode == 20:
	
	m3u_play(name,url)
	

xbmcplugin.endOfDirectory(plugin_handle)