# -*- coding: utf-8 -*-

import xbmc, time, base64

from core import httptools, scrapertools
from platformcode import config, logger, platformtools

from core.jsontools import json


espera = config.get_setting('servers_waiting', default=6)

color_exec = config.get_setting('notification_exec_color', default='cyan')
el_srv = ('Sin respuesta en [B][COLOR %s]') % color_exec
el_srv += ('ResolveUrl[/B][/COLOR]')


def import_libs(module):
    import os, sys, xbmcaddon
    from core import filetools

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

    data = httptools.downloadpage(page_url).data

    if "Not found" in data or "File not found" in data or "File is no longer available" in data or "Error 404" in data or '404 - No encontrado' in data:
        return "Archivo inexistente ó eliminado"

    elif '<title>Modo mantenimiento</title>' in data:
        return "Servidor en Mantenimiento"

    if "permanentToken" in data:
        match = scrapertools.find_single_match(data, "(?i)window\.location\.href\s*=\s*'([^']+)'")
        data = httptools.downloadpage(match).data

        if '<title>Modo mantenimiento</title>' in data:
            return "Servidor en Mantenimiento"

    video_srcs = scrapertools.find_multiple_matches(data, "(?:mp4|hls)': '([^']+)'")

    if not video_srcs:
        bloque = scrapertools.find_single_match(data, "sources.*?\}")

        video_srcs = scrapertools.find_multiple_matches(bloque, ': "([^"]+)')

        if not video_srcs:
            if not video_srcs: video_srcs = scrapertools.find_multiple_matches(bloque, ":.*?'(.*?)'")

    if video_srcs:
        for url in video_srcs:
            if url.startswith("aHR0"):
                url = base64.b64decode(url).decode("utf-8")

            if 'http' in url:
                video_urls.append(['mp4', url])

    if not video_urls:
        try:
            vid = scrapertools.find_single_match(data, "(?i)let\s[0-9a-f]+\s=\s'(.*?)'")
            dec_vid = base64.b64decode(vid).decode("utf-8")
            data_json = json.loads(dec_vid[::-1])

            video_urls.append(['mp4', data_json['file']])
        except Exception:
            pass

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Voe[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
                time.sleep(int(espera))

            try:
                import_libs('script.module.resolveurl')

                import resolveurl
                page_url = ini_page_url

                resuelto = resolveurl.resolve(page_url)

                if resuelto:
                    video_urls.append(['mp4', resuelto])
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

                elif 'HTTP Error 404: Not Found' in traceback.format_exc() or '404 Not Found' in traceback.format_exc():
                    return 'Archivo inexistente'

                elif '<urlopen error' in traceback.format_exc():
                    return 'No se puede establecer la conexión'

                return 'Sin Respuesta ResolveUrl'

        else:
           return 'Falta ResolveUrl'

    return video_urls

