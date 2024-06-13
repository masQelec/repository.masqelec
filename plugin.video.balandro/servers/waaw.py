# -*- coding: utf-8 -*-

import xbmc, time

from core import httptools, scrapertools
from platformcode import config, logger, platformtools


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

    if '/watch_video.php?v=/watch_video.php?v=/player/embed_player.php?vid=' in page_url: page_url = page_url.replace('/watch_video.php?v=/watch_video.php?v=/player/embed_player.php?vid=', '/watch_video.php?v=')
    elif '/watch_video.php?v=/player/embed_player.php?vid=' in page_url: page_url = page_url.replace('/watch_video.php?v=/player/embed_player.php?vid=', '/watch_video.php?v=')
    elif '/watch_video.php?v=/watch_video.php?v=' in page_url: page_url = page_url.replace('/watch_video.php?v=/watch_video.php?v=', '/watch_video.php?v=')

    page_url = page_url.replace('&amp;', '&').replace('&autoplay=no/', '').replace('&autoplay=no', '').replace('&autoplay=yes/', '').replace('&autoplay=yes', '')

    ini_page_url = page_url

    if not xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        return '[COLOR cyan][B]script.module.resolveurl [COLOR red][B]No Instalado[/COLOR]'

    if config.get_setting('servers_time', default=True):
        platformtools.dialog_notification('Cargando [COLOR cyan][B]Waaw[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
        time.sleep(int(espera))

    try:
        import_libs('script.module.resolveurl')

        import resolveurl
        page_url = ini_page_url

        page_url = page_url.replace('watch_video.php?v=', 'f/')
        resuelto = resolveurl.resolve(page_url)

        if resuelto:
            video_urls.append(['mp4', resuelto])
            return video_urls

        platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)

    except:
        import traceback
        logger.error(traceback.format_exc())

        if 'resolveurl.resolver.ResolverError:' in traceback.format_exc():
            trace = traceback.format_exc()
            if 'File Not Found or' in trace or 'The requested video was not found' in trace or 'File deleted' in trace or 'No video found' in trace or 'No playable video found' in trace or 'Video cannot be located' in trace or 'file does not exist' in trace or 'Video not found' in trace:
                return 'Archivo inexistente ó eliminado'
            elif 'No se ha encontrado ningún link al' in trace or 'Unable to locate link' in trace or 'Video Link Not Found' in trace:
                return 'Fichero sin link al vídeo'

            elif 'Wrong captcha. Please try again.' in trace:
                return 'Captcha erróneo. [COLOR cyan][B]Inténtelo de nuevo[/COLOR]'

        elif "KeyError: 'obf_link'" in traceback.format_exc():
            return 'KeyError [COLOR red][B]obf_link[/COLOR]'

        elif "AttributeError: 'int'" in traceback.format_exc():
            return 'AttributeError [COLOR red][B]get_int[/COLOR]'

        elif '<urlopen error' in traceback.format_exc():
            return 'No se puede establecer la conexión'

        platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)

        return video_urls

