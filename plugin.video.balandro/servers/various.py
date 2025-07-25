# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3:
    import xbmcvfs
    translatePath = xbmcvfs.translatePath
else:
    import xbmc
    translatePath = xbmc.translatePath


import os, xbmc, time

from platformcode import config, logger, platformtools
from core import filetools, httptools, scrapertools


espera = config.get_setting('servers_waiting', default=6)


def import_libs(module):
    import xbmcaddon

    path = os.path.join(xbmcaddon.Addon(module).getAddonInfo("path"))
    addon_xml = filetools.read(filetools.join(path, "addon.xml"))

    if addon_xml:
        require_addons = scrapertools.find_multiple_matches(addon_xml, '(<import addon="[^"]+"[^\/]+\/>)')
        require_addons = list(filter(lambda x: not 'xbmc.python' in x and 'optional="true"' not in x, require_addons))

        for addon in require_addons:
            addon = scrapertools.find_single_match(addon, 'import addon="([^"]+)"')
            if xbmc.getCondVisibility('System.HasAddon("%s")' % (addon)):
                import_libs(addon)
            else:
                xbmc.executebuiltin('InstallAddon(%s)' % (addon))
                import_libs(addon)

        lib_path = scrapertools.find_multiple_matches(addon_xml, 'library="([^"]+)"')
        for lib in list(filter(lambda x: not '.py' in x, lib_path)):
            sys.path.append(os.path.join(path, lib))


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    ini_page_url = page_url

    if not xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'): return 'Falta ResolveUrl'

    txt_server = 'Unknow'

    if 'tubeload' in page_url: txt_server = 'Tubeload'

    elif 'mvidoo' in page_url:
          txt_server = 'Mvidoo'

          page_url = page_url.replace('/embed-', '/')

    elif 'rutube' in page_url: txt_server = 'Rutube'
    elif 'videowood' in page_url: txt_server = 'Videowood'
    elif 'yandex' in page_url: txt_server = 'Yandex'
    elif 'fastupload' in page_url: txt_server = 'Fastupload'

    elif 'dropload' in page_url:
          txt_server = 'Dropload'

          page_url = page_url.replace('/embed-', '/')

    elif 'krakenfiles' in page_url: txt_server = 'Krakenfiles'
    elif 'embedgram' in page_url: txt_server = 'Embedgram'
    elif 'embedrise' in page_url: txt_server = 'Embedrise'
    elif 'streamvid' in page_url: txt_server = 'Streamvid'
    elif 'vidello' in page_url: txt_server = 'Vidello'
    elif 'upload.do' in page_url: txt_server = 'Uploaddo'
    elif 'hxfile' in page_url: txt_server = 'Hxfile'
    elif 'drop' in page_url: txt_server = 'Drop'
    elif 'userload' in page_url: txt_server = 'Userload'
    elif 'uploadraja' in page_url: txt_server = 'Uuloadraja'
    elif 'rumble' in page_url: txt_server = 'Rumble'
    elif 'qiwi' in page_url: txt_server = 'Qiwi'
    elif 'streamsilk' in page_url: txt_server = 'Streamsilk'

    elif 'terabox' in page_url:
          txt_server = 'Terabox'

          page_url = page_url.replace('terabox.app/', 'terabox.com/')

    elif 'streamruby' in page_url or 'sruby' in page_url or 'rubystream' in page_url or 'stmruby' in page_url or 'rubystm' in page_url or 'rubyvid' in page_url:
          txt_server = 'Streamruby'

          page_url = page_url.replace('/rubystream.xyz/', '/streamruby.com/').replace('/sruby.xyz/', '/streamruby.com/')

          page_url = page_url.replace('/embed-', '/')

    elif 'goodstream' in page_url:
          txt_server = 'Goodstream'

          if '/embed-' in page_url:
              page_url = page_url.replace('/goodstream.uno/embed-', '/goodstream.uno/video/embed/')
              page_url = page_url.replace('/goodstream.one/embed-', '/goodstream.uno/video/embed/')
              page_url = page_url.replace('.html', '')
 
          if not '/video/embed/' in page_url:
              page_url = page_url.replace('/goodstream.uno/', '/goodstream.uno/video/embed/')
              page_url = page_url.replace('/goodstream.one/', '/goodstream.uno/video/embed/')
              page_url = page_url.replace('.html', '')

    elif 'filemoon' in page_url or 'fmoonembed' in page_url or 'embedmoon' in page_url or 'moonjscdn' in page_url or 'l1afav' in page_url:
          txt_server = 'Filemoon'

          page_url = page_url.replace('/filemoon.to/', '/filemoon.sx/').replace('/filemoon.in/', '/filemoon.sx/').replace('/filemoon.nl/', '/filemoon.sx/').replace('/filemoon.wf/', '/filemoon.sx/').replace('/filemoon.eu/', '/filemoon.sx/').replace('/filemoon.art/', '/filemoon.sx/').replace('/filemoon.link/', '/filemoon.sx/').replace('/filemoon.top/', '/filemoon.sx/').replace('/filemoon.lat/', '/filemoon.sx/').replace('/filemoon.org/', '/filemoon.sx/').replace('/filemoon.online/', '/filemoon.sx/')
          page_url = page_url.replace('/fmoonembed.pro/', '/filemoon.sx/').replace('/embedmoon.xyz/', '/filemoon.sx/').replace('/moonjscdn.info/', '/filemoon.sx/').replace('/l1afav.net/', '/filemoon.sx/')

    elif 'streamhub' in page_url:
          txt_server = 'Streamhub'

          page_url = page_url.replace('/streamhub.gg/', '/streamhub.to/').replace('/streamhub.ink/', '/streamhub.to/').replace('/streamhub.top/', '/streamhub.to/')

          page_url = page_url.replace('/e/e/', '/e/').replace('/d/d/', '/d/')

          page_url = page_url.replace('/embed-', '/')

    elif 'uploadever' in page_url:
          txt_server = 'Uploadever'

          page_url = page_url.replace('/uploadever.com/', '/uploadever.in/')

    elif 'moonmov' in page_url:
          txt_server = 'Moonplayer'

          page_url = page_url.replace('/moonmov.pro/', '/filemoon.sx/')

    elif 'moonplayer' in page_url:
          txt_server = 'Moonplayer'

          page_url = page_url.replace('/moonplayer.lat/', '/filemoon.sx/')

    elif 'yadi.' in page_url or 'yandex' in page_url:
          txt_server = 'Yandex'

          page_url = page_url.replace('/disk.yandex.ru/', '/yadi.sk/').replace('/disk.yandex.com/', '/yadi.sk/').replace('/disk.yandex.sk/', '/yadi.sk/').replace('/disk.yandex.disk/', '/yadi.sk/')

          page_url = page_url.replace('//yadi.ru', '/yadi.sk/').replace('//yadi.com', '/yadi.sk/').replace('//yadi.disk', '/yadi.sk/')

    elif 'streamwish' in page_url or 'strwish' in page_url or 'embedwish' in page_url or 'wishembed' in page_url or 'awish' in page_url or 'dwish' in page_url or 'mwish' in page_url or 'wishfast' in page_url or 'sfastwish' in page_url or 'doodporn' in page_url or 'flaswish' in page_url or 'obeywish' in page_url or 'cdnwish' in page_url or 'asnwish' in page_url or 'flastwish' in page_url or 'jodwish' in page_url or 'swhoi' in page_url or 'fsdcmo' in page_url or 'swdyu' in page_url or 'wishonly' in page_url or 'playerwish' in page_url or 'hlswish' in page_url or 'wish' in page_url or 'iplayerhls' in page_url or 'hlsflast' in page_url or 'ghbrisk' in page_url or 'cybervynx' in page_url or 'streamhg' in page_url or 'hlsflex' in page_url or 'dhcplay' in page_url or 'stbhg' in page_url or 'gradehgplus' in page_url:
          txt_server = 'Streamwish'

          page_url = page_url.replace('/streamwish.com/', '/streamwish.to/').replace('/streamwish.top/', '/streamwish.to/').replace('/streamwish.site/', '/streamwish.to/').replace('/strwish.xyz/', '/streamwish.to/').replace('/strwish.com/', '/streamwish.to/').replace('/embedwish.com/', '/streamwish.to/').replace('/wishembed.pro/', '/streamwish.to/')
          page_url = page_url.replace('/awish.pro/', '/streamwish.to/').replace('/dwish.pro/', '/streamwish.to/').replace('/mwish.pro/', '/streamwish.to/').replace('/wishfast.top/', '/streamwish.to/').replace('/sfastwish.com/', '/streamwish.to/').replace('/doodporn.xyz/', '/streamwish.to/')
          page_url = page_url.replace('/flaswish.com/', '/streamwish.to/').replace('/obeywish.com/', '/streamwish.to/').replace('/cdnwish.com/', '/streamwish.to/').replace('/asnwish.com/', '/streamwish.to/').replace('/flastwish.com/', '/streamwish.to/').replace('/jodwish.com/', '/streamwish.to/')
          page_url = page_url.replace('/swhoi.com/', '/streamwish.to/').replace('/fsdcmo.sbs/', '/streamwish.to/').replace('/swdyu.com/', '/streamwish.to/').replace('/wishonly.site/', '/streamwish.to/').replace('/playerwish.com/', '/streamwish.to/')
          page_url = page_url.replace('/hlswish.com/', '/streamwish.to/').replace('/swishsrv.com/', '/streamwish.to/').replace('/streamwish.fun/', '/streamwish.to/')

          page_url = page_url.replace('/iplayerhls.com/', '/streamwish.to/').replace('/hlsflast.com/', '/streamwish.to/').replace('/ghbrisk.com/', '/streamwish.to/')

          page_url = page_url.replace('/cybervynx.com/', '/streamwish.to/').replace('/streamhg.com/', '/streamwish.to/').replace('/hlsflex.com/', '/streamwish.to/').replace('/swiftplayers.com/', '/streamwish.to/')

          page_url = page_url.replace('/stbhg.click/', '/streamwish.to/').replace('/dhcplay.com/', '/streamwish.to/').replace('/gradehgplus/', '/streamwish.to/')

    elif 'desiupload' in page_url:
          txt_server = 'Desiupload'

          page_url = page_url.replace('/desiupload.to/', '/desiupload.co/').replace('/desiupload.in/', '/desiupload.co/')

    elif 'filelions' in page_url or 'azipcdn' in page_url or 'alions' in page_url or 'dlions' in page_url or 'mlions' in page_url or 'fviplions' in page_url or 'javlion' in page_url or 'fdewsdc' in page_url or 'peytonepre' in page_url or 'ryderjet' in page_url or 'smoothpre' in page_url or 'movearnpre' in page_url or 'seraphinap' in page_url or 'seraphinapl' in page_url:
          txt_server = 'Filelions'

          page_url = page_url.replace('/embed/', '/')

          page_url = page_url.replace('/filelions.com/', '/filelions.to/').replace('/filelions.live/', '/filelions.to/').replace('/filelions.xyz/', '/filelions.to/').replace('/filelions.online/', '/filelions.to/').replace('/filelions.site/', '/filelions.to/').replace('/filelions.co/', '/filelions.to/').replace('/filelions.top/', '/filelions.to/')
          page_url = page_url.replace('/azipcdn.com/', '/filelions.to/')
          page_url = page_url.replace('/alions.pro/', '/filelions.to/').replace('/dlions.pro/', '/filelions.to/').replace('/mlions.pro/', '/filelions.to/').replace('/fviplions.com/', '/filelions.to/')
          page_url = page_url.replace('/javlion.xyz/', '/filelions.to/').replace('/fdewsdc.sbs/', '/filelions.to/')
          page_url = page_url.replace('/peytonepre.com/', '/filelions.to/').replace('/ryderjet.com/', '/filelions.to/').replace('/smoothpre.com/', '/filelions.to/').replace('/movearnpre.com/', '/filelions.to/')
          page_url = page_url.replace('/seraphinap.com/', '/filelions.to/').replace('/seraphinapl.com/', '/filelions.to/')

    elif 'youdbox' in page_url or 'yodbox' in page_url or 'youdboox' in page_url: 
          txt_server = 'Youdbox'

          page_url = page_url.replace('/youdbox.com/', '/youdbox.site/').replace('/youdbox.net/', '/youdbox.site/').replace('/youdbox.org/', '/youdbox.site/')

          page_url = page_url.replace('/yodbox.com/', '/youdbox.site/').replace('/youdboox.com/', '/youdbox.site/')

          page_url = page_url.replace('/embed-', '/')

    elif 'vudeo' in page_url:
          txt_server = 'Vudeo'

          page_url = page_url.replace('/vudeo.net/', '/vudeo.ws/').replace('/vudeo.io/', '/vudeo..ws/').replace('/vudeo.co/', '/vudeo.ws/')

    elif 'hexupload' in page_url or 'hexload' in page_url:
          txt_server = 'Hexupload'

          page_url = page_url.replace('/hexupload.net/', '/hexload.com/')

          page_url = page_url.replace('/embed-', '/')

    elif 'vidguard' in page_url or 'vgfplay' in page_url or 'vgembed' in page_url or 'v6embed' in page_url or 'vembed' in page_url or 'vid-guard' in page_url or 'embedv' in page_url or 'bembed' in page_url or 'listeamed' in page_url or 'go-streamer.net' in page_url:
          txt_server = 'Vidguard'

          page_url = page_url.replace('/vidguard.to/', '/vgembed.com/').replace('/vgfplay.com/', '/vgembed.com/').replace('/vgfplay.xyz/', '/vgembed.com/').replace('/vgplayer.xyz/', '/vgembed.com/').replace('/v6embed.xyz/', '/vgembed.com/').replace('/vembed.net/', '/vgembed.com/').replace('/vembed.org/', '/vgembed.com/').replace('/vid-guard.com/', '/vgembed.com/').replace('/embedv.net/', '/vgembed.com/').replace('/bembed.net/', '/vgembed.com/')

    elif 'lulustream' in page_url or 'luluvdo' in page_url or 'streamhihi' in page_url or 'luluvdoo' in page_url or 'lulu' in page_url or 'ponmi' in page_url:
          txt_server = 'Lulustream'

          page_url = page_url.replace('/luluvdo.com/', '/lulustream.com/')
          page_url = page_url.replace('/streamhihi.com/', '/lulustream.com/').replace('/luluvdoo/', '/lulustream.com/')
          page_url = page_url.replace('/lulu.st/', '/lulustream.com/').replace('/ponmi.sbs/', '/lulustream.com/')

    elif 'turboviplay' in page_url or 'emturbovid' in page_url or 'tuborstb' in page_url:
          txt_server = 'Turboviplay'

          page_url = page_url.replace('/turboviplay.com/', '/emturbovid.com/').replace('/tuborstb.co/', '/emturbovid.com/')

    elif 'file-upload' in page_url:
          txt_server = 'Fileupload'

          page_url = page_url.replace('/www.file-upload.com/', '/www.file-upload.org/')

    elif 'vidspeed' in page_url or 'vidroba' in page_url:
          txt_server = 'Vidspeed'

          page_url = page_url.replace('/www.vidspeeds.com/', '/vidspeed.cc/').replace('/vidspeeds.com/', '/vidspeed.cc/')

          page_url = page_url.replace('/embed-', '/')

    elif 'vkspeed' in page_url or 'vkspeed7' in page_url:
          txt_server = 'Vkspeed'

          page_url = page_url.replace('/vkspeed7.com/', '/vkspeed.com/')

    elif 'twitch' in page_url:
          txt_server = 'Twitch'

          page_url = page_url.replace('/player.twitch.tv/', '/www.twitch.tv/')

    elif 'vidhide' in page_url or 'stblion' in page_url or 'dhtpre' in page_url or 'dramacool' in page_url:
          txt_server = 'Vidhidepro'

          page_url = page_url.replace('/embed/', '/v/').replace('/file/', '/s/').replace('/download/', '/v/')

          page_url = page_url.replace('/vidhide.com/v/', '/vidhidepro.com/s/').replace('/vidhidepro.com/v/', '/vidhidepro.com/s/').replace('/vidhidevip.com/v/', '/vidhidepro.com/s/').replace('/vidhide.com/f/', '/vidhidepro.com/s/').replace('/vidhidepro.com/f/', '/vidhidepro.com/s/').replace('/vidhidevip.com/f/', '/vidhidepro.com/s/')

          page_url = page_url.replace('/vidhidepre.com/v/', '/vidhidepro.com/s/').replace('/vidhidepre.com/f/', '/vidhidepro.com/s/')
          page_url = page_url.replace('/vidhideplus.com/v/', '/vidhidepro.com/s/').replace('/vidhideplus.com/f/', '/vidhidepro.com/s/')
          page_url = page_url.replace('/vidhide.fun/v/', '/vidhidepro.com/s/').replace('/vidhide.fun/f/', '/vidhidepro.com/s/')
          page_url = page_url.replace('/vidhidehub.com/v/', '/vidhidepro.com/s/').replace('/vidhidehub.com/f/', '/vidhidepro.com/s/')

          page_url = page_url.replace('/stblion.xyz/v/', '/vidhidepro.com/s/').replace('/stblion.xyz/f/', '/vidhidepro.com/s/')

          page_url = page_url.replace('/dhtpre.com/v/', '/vidhidepro.com/s/').replace('/dhtpre.com/f/', '/vidhidepro.com/s/')

          page_url = page_url.replace('/dramacool.men/v/', '/vidhidepro.com/s/').replace('/dramacool.men/f/', '/vidhidepro.com/s/')

    elif txt_server == 'Unknow': return 'Desconocido'

    # ~ VIDHIDEPRO
    if txt_server == 'Vidhidepro':
        if config.get_setting('servers_time', default=True):
            platformtools.dialog_notification('Accediendo a', '[COLOR cyan][B]' + txt_server + '[/B][/COLOR]')

        url = widhide(ini_page_url)

        if url:
            # ~ 27/4/2025  VIDHIDE pq ya No existe en ResolveUrl
            video_urls.append(['m3u8', url])
            return video_urls

    path = translatePath(os.path.join('special://home/addons/script.module.resolveurl/lib/resolveurl/plugins/', txt_server.lower() + '.py'))

    existe = filetools.exists(path)
    if not existe: return 'El Plugin No existe en Resolveurl'

    if config.get_setting('servers_time', default=True):
        platformtools.dialog_notification('Cargando ' + '[COLOR cyan][B]' + txt_server + '[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
        time.sleep(int(espera))

    try:
        import_libs('script.module.resolveurl')

        import resolveurl

        # ~ STREAMWISH
        if txt_server == 'Streamwish':
            if not "|Referer=" in ini_page_url: 
                ini_page_url = ini_page_url + "|Referer=" + ini_page_url
                page_url = ini_page_url

        # ~ FILELIONS
        if txt_server == 'Filelions':
            if not "|Referer=" in ini_page_url: 
                ini_page_url = ini_page_url + "|Referer=" + ini_page_url
                page_url = ini_page_url

        if "|Referer=" in page_url: page_url = page_url.replace("|Referer=", '$$')

        resuelto = resolveurl.resolve(page_url)

        if resuelto:
            if '.zip' in resuelto or '.rar' in resuelto: return "El archivo está en formato comprimido"
            elif '.m3u8' in resuelto: video_urls.append(['m3u8', resuelto])
            elif '.mp4' in resuelto: video_urls.append(['mp4', resuelto])
            else: video_urls.append(['', resuelto])
            return video_urls

        color_exec = config.get_setting('notification_exec_color', default='cyan')
        el_srv = ('Sin respuesta en [B][COLOR %s]') % color_exec
        el_srv += ('ResolveUrl[/B][/COLOR]')
        platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)

        page_url = ini_page_url

        return 'No se pudo Reproducir el Vídeo con ResolveUrl'

    except:
        import traceback
        logger.error(traceback.format_exc())

        if txt_server == 'Streamwish':
            if not "|Referer=" in ini_page_url: url = url + "|Referer=" + ini_page_url

            url = wish(ini_page_url)

            if url:
                # ~ 10/4/2025  WISH pq a veces falla ResolveUrl
                video_urls.append(['m3u8', url])
                return video_urls

        elif txt_server == 'Vidspeed':
             data = httptools.downloadpage(ini_page_url).data

             url = scrapertools.find_single_match(str(data), 'file:"(.*?)"')

             if url:
                 # ~ 13/10/2023  VIDSPEED --> Directo pq a veces falla ResolveUrl
                 video_urls = [[url[-4:], url]]
                 return video_urls

        elif txt_server == 'Hexupload':
             url = hexupload(ini_page_url)

             if url:
                 # ~ 23/5/2025  HEXUPLOAD pq a veces falla ResolveUrl
                 video_urls.append(['mp4', url])
                 return video_urls

        if 'resolveurl.resolver.ResolverError:' in traceback.format_exc():
            trace = traceback.format_exc()
            if 'File Removed' in trace or 'File Not Found or' in trace or 'The requested video was not found' in trace or 'File deleted' in trace or 'No video found' in trace or 'No playable video found' in trace or 'Video cannot be located' in trace or 'file does not exist' in trace or 'Video not found' in trace:
                return 'Archivo inexistente ó eliminado'

            elif 'No se ha encontrado ningún link al' in trace or 'Unable to locate link' in trace or 'Video Link Not Found' in trace:
                return 'Fichero sin link al vídeo ó restringido'

        elif 'HTTP Error 404: Not Found' in traceback.format_exc() or '404 Not Found' in traceback.format_exc():
            return 'Archivo inexistente'

        elif '<urlopen error' in traceback.format_exc():
            return 'No se puede establecer la conexión'

        return 'Sin Respuesta ' + txt_server


def wish(page_url):
    from lib import jsunpack

    m3u8 = ''

    headers = {}

    if "|Referer=" in page_url:
        referer = scrapertools.find_single_match(page_url, '|Referer=(.*?)$')
        headers = {'Referer': referer}

    try:
        page_url = httptools.downloadpage(page_url, headers=headers, follow_redirects=False).headers["location"]
    except:
        pass

    data = httptools.downloadpage(page_url).data

    if "Not Found" in data or "File was deleted" in data or "is no longer available" in data: return ''

    try:
        pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(pack)

        m3u8 = scrapertools.find_single_match(str(unpacked), 'links=.*?"hls2":"(.*?)"')
    except:
        pass

    return m3u8


def widhide(page_url):
    from lib import jsunpack

    m3u8 = ''

    headers = {}

    if "|Referer=" in page_url:
        referer = scrapertools.find_single_match(page_url, '|Referer=(.*?)$')
        headers = {'Referer': referer}

    resp = httptools.downloadpage(page_url, headers=headers)

    data = resp.data

    if not resp.sucess: return ''

    if "Not Found" in data or "File was deleted" in data or "is no longer available" in data: return ''

    enc_data = scrapertools.find_single_match(data, "text/javascript(?:'|\")>(eval.*?)</script>")

    try:
        dec_data = jsunpack.unpack(enc_data)

        m3u8 = scrapertools.find_single_match(dec_data, '\{(?:file|src|"hls2"):"([^"]+)"')
    except:
        pass

    return m3u8


def hexupload(page_url):
    id = page_url.replace('https://hexupload.net/', '')

    post = {'op': 'download3', 'id': id, 'ajax': '1', 'method_free': '1', 'dataType': 'json'}

    headers = {'Referer': page_url}

    resp = httptools.downloadpage('https://hexload.com/download', post=post, headers=headers)

    mp4 = scrapertools.find_single_match(resp.data, '"url":"(.*?)"')

    return mp4