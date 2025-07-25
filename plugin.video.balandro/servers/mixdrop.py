# -*- coding: utf-8 -*-

import sys

import xbmc, time

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
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    if not 'http' in page_url: return video_urls

    ini_page_url = page_url

    if '/mixdrop.co/' in page_url: page_url = page_url.replace('/mixdrop.co/', '/mixdrop.ag/')
    elif '/mixdrop.my/' in page_url: page_url = page_url.replace('/mixdrop.my/', '/mixdrop.ag/')

    headers = {'Referer': page_url.replace('/e/', '/f/')}

    data = httptools.downloadpage(page_url, headers=headers).data

    if '>WE ARE SORRY</h2>' in data or '<title>404 Not Found</title>' in data:
        return 'Archivo inexistente ó eliminado'

    url = scrapertools.find_single_match(data, 'window\.location\s*=\s*"([^"]+)')
    if url:
        if not '+e+' in url:
            if not 'http' in url:
                if url.startswith('/e/'): url = 'https://mixdrop.ag' + url
                data = httptools.downloadpage(url).data
 
    packed = scrapertools.find_multiple_matches(data, r'(eval.*?)</script>')

    for pack in packed:
        try: data = jsunpack.unpack(pack)
        except: data = ''

    urls = scrapertools.find_multiple_matches(data, 'MDCore\.\w+\s*=\s*"([^"]+)"')

    for url in urls:
        if '/' not in url: continue
        elif url.endswith('.jpg'): continue

        elif not url.endswith('.mp4'): continue

        if url.startswith('//'):
            url = 'https' + url
            video_urls.append(["mp4", url])
            break

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Mixdrop[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
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
