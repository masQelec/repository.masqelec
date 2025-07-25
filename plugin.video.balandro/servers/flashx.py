# -*- coding: utf-8 -*-

import xbmc, time, base64

from core import httptools, scrapertools
from platformcode import config, logger, platformtools

from lib import jsunpack


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
    logger.info("url=" + page_url)
    video_urls = []

    ini_page_url = page_url

    video_id = scrapertools.find_single_match(page_url, '/([A-z0-9]+)\.html')

    url = 'https://www.flashx.tv/playvideo-%s.html?playvid' % video_id

    data = httptools.downloadpage(url, headers={'Referer': 'https://www.flashx.tv/embed-%s.html' % video_id}).data

    if 'Too many views' in data:
        return 'Archivo no encontrado'
    elif 'NOT FOUND' in data or 'file was deleted or the link is expired' in data:
        return 'Archivo inexistente ó eliminado'

    if 'normal.mp4' not in data:
        file_id = scrapertools.find_single_match(data, "'file_id', '([^']+)'")

        if file_id:
            file_id = base64.b64encode(file_id)

            httptools.downloadpage('https://www.flashx.to/counter.cgi?c2=%s&fx=%s' % (video_id, file_id))
            httptools.downloadpage('https://www.flashx.tv/flashx.php?ss=yes&f=fail&fxfx=6')
            data = httptools.downloadpage(url).data

    # ~ packeds = scrapertools.find_multiple_matches(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    # ~ for packed in packeds:
        # ~ unpacked = jsunpack.unpack(packed)
        # ~ logger.info(unpacked)

    matches = scrapertools.find_multiple_matches(data, "{src: '([^']+)'.*?,label: '([^']+)',res: ([\d]+)")

    for url, lbl, res in matches:
        video_urls.append(['%s %sp' % (lbl, res), url])

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Flashx[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
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
