# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

if PY3:
    import xbmcvfs
    translatePath = xbmcvfs.translatePath
else:
    import xbmc
    translatePath = xbmc.translatePath


import re, os, xbmc, time

from platformcode import config, logger, platformtools
from core import filetools, httptools, scrapertools


espera = config.get_setting('servers_waiting', default=6)

color_exec = config.get_setting('notification_exec_color', default='cyan')
el_srv = ('Sin respuesta en [B][COLOR %s]') % color_exec
el_srv += ('ResolveUrl[/B][/COLOR]')


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
    logger.info("url=" + page_url)
    video_urls = []

    ini_page_url = page_url

    if 'okru.link/v2' in page_url:
        v = scrapertools.find_single_match(page_url, "t=([\w\.]+)")

        headers = {"Content-Type" : "application/x-www-form-urlencoded", "Origin" : page_url}
        post = {"video" : v}

        data = httptools.downloadpage("https://apizz.okru.link/decoding", post = post, headers = headers).data

        if '<p>Por causas ajenas a' in data or '>Por causas ajenas a' in data:
            return 'Servidor Bloqueado por su Operadora'

        elif str(data) == '{"status":"decoding"}':
            return 'Archivo Bloqueado por su Operadora'

        video = scrapertools.find_single_match(data,'"url":"(.*?)"')

        if video:
            video = video.replace('\\/', '/')

            video_urls.append(['mp4', video])
            return video_urls

    elif 'okru.link/embed' in page_url:
         v = scrapertools.find_single_match(page_url, "t=(\w+)")

         data = httptools.downloadpage("https://okru.link/details.php?v=" + v).data

         if '<p>Por causas ajenas a' in data or '>Por causas ajenas a' in data:
             return 'Servidor Bloqueado por su Operadora'

         elif str(data) == '{"status":"decoding"}':
             return 'Archivo Bloqueado por su Operadora'

         video = scrapertools.find_single_match(data,'"file":"(.*?)"')

         if video:
             video = video.replace('\\/', '/')

             video_urls.append(['mp4', video])
             return video_urls

    elif 'okru.link' in page_url:
         v = scrapertools.find_single_match(page_url, "t=(\w+)")

         data = httptools.downloadpage("https://okru.link/details.php?v=" + v).data

         if '<p>Por causas ajenas a' in data or '>Por causas ajenas a' in data:
             return 'Servidor Bloqueado por su Operadora'

         elif str(data) == '{"status":"decoding"}':
             return 'Archivo Bloqueado por su Operadora'

         video = scrapertools.find_single_match(str(data), '"file":"(.*?)"')

         if video:
             video = video.replace('\\/', '/')

             video_urls.append(['mp4', video])
             return video_urls

    elif '/embed.html' in page_url or '/embed_vf.html' in page_url:
       if '/embed.html' in page_url: new_page_url = page_url.replace('/embed.html?t=', '/details.php?v=')
       else: new_page_url = page_url.replace('/v2/embed_vf.html?t=', '/details.php?v=')

       post = scrapertools.find_single_match(new_page_url, "v=(.*?)$")

       if post:
           data = httptools.downloadpage(new_page_url, post = {'v': post}).data

           video = scrapertools.find_single_match(data, '"file":"(.*?)"')

           if video:
               video = video.replace('\\/', '/')

               video_urls.append(['mp4', video])
               return video_urls

    data = httptools.downloadpage(page_url).data

    if "copyrightsRestricted" in data or "COPYRIGHTS_RESTRICTED" in data or "copyrights_rstricted" in data or "limited_access" in data or "LIMITED_ACCESS" in data:
        return 'Archivo eliminado Violación Copyright'
    elif 'author of this video has not been found or is blocked' in data:
        return 'Autor del vídeo inexistente ó bloqueado'
    elif 'Access to this video is restricted' in data:
        return 'El acceso al vídeo está Restringido'
    elif 'src="/captcha.asd.js?v=' in data:
        return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'
    elif "notFound" in data:
        return 'Archivo inexistente ó eliminado'
    elif "The video is blocked" in data:
        return 'Archivo bloqueado'

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            path = translatePath(os.path.join('special://home/addons/script.module.resolveurl/lib/resolveurl/plugins/', 'ok.py'))

            existe = filetools.exists(path)
            if not existe:
                return 'El Plugin No existe en Resolveurl'

            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Ok[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
                time.sleep(int(espera))

            try:
                import_libs('script.module.resolveurl')

                if xbmc.getCondVisibility('System.HasAddon("script.module.cloudrequest")'):
                    import_libs('script.module.cloudrequest')

                import resolveurl
                page_url = ini_page_url
                resuelto = resolveurl.resolve(page_url)

                if resuelto:
                    if '.m3u8' in resuelto: video_urls.append(['m3u8', resuelto])
                    elif '.m3u' in resuelto: video_urls.append(['m3u', resuelto])
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

                if 'resolveurl.resolver.ResolverError:' in traceback.format_exc():
                    trace = traceback.format_exc()
                    if 'File Removed' in trace or 'File Not Found or' in trace or 'The requested video was not found' in trace or 'File deleted' in trace or 'No video found' in trace or 'No playable video found' in trace or 'Video cannot be located' in trace or 'file does not exist' in trace or 'Video not found' in trace:
                        return 'Archivo inexistente ó eliminado'

                    elif 'No se ha encontrado ningún link al' in trace or 'Unable to locate link' in trace or 'Video Link Not Found' in trace:
                        return 'Fichero sin link al vídeo ó restringido'

                    elif 'Cloudflare challenge' in trace:
                        return 'Cloudflare Challenge Check'

                elif "No module named 'cloudscraper'" in traceback.format_exc():
                    return 'Falta script.module.cloudrequest'

                elif 'HTTP Error 404: Not Found' in traceback.format_exc() or '404 Not Found' in traceback.format_exc():
                    return 'Archivo inexistente'

                elif '<urlopen error' in traceback.format_exc():
                    return 'No se puede establecer la conexión'

                return 'Sin Respuesta ResolveUrl'

        else:
            return 'Falta ResolveUrl'

    return video_urls
