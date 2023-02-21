# -*- coding: utf-8 -*-

import xbmc, time

from platformcode import config, logger, platformtools
from core import httptools, scrapertools


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

    data = httptools.downloadpage(page_url).data

    msg_error = scrapertools.find_single_match(data, "<li class='no-side-margin'>([^<]+)</li>")

    if "no longer available!" in msg_error:
        return "El fichero no existe o ha sido borrado"
    elif msg_error:
        return msg_error

    url = scrapertools.find_single_match(data, "href='([^']+)'>download now</a>")

    if url:
        platformtools.dialog_notification('Cargando MegaUp', 'Espera de %s segundos requerida' % espera)
        time.sleep(int(espera))

        headers = { 'Referer': page_url }
        url = httptools.downloadpage(url, headers=headers, follow_redirects=False, only_headers=True).headers.get('location', '')

        if url:
            video_urls.append(['mp4', url])

        else:
            if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
                try:
                    import_libs('script.module.resolveurl')

                    import resolveurl
                    page_url = ini_page_url
                    resuelto = resolveurl.resolve(page_url)

                    if resuelto:
                        video_urls.append(['mp4', resuelto + '|Referer=%s' % page_url])
                        return video_urls

                    platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)
                except:
                    import traceback
                    logger.error(traceback.format_exc())
                    platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)

            else:
                return 'Acceso Denegado' # ~ Cloudflare recaptcha

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            try:
                import_libs('script.module.resolveurl')

                import resolveurl
                page_url = ini_page_url
                resuelto = resolveurl.resolve(page_url)

                if resuelto:
                    video_urls.append(['mp4', resuelto + '|Referer=%s' % page_url])
                    return video_urls

                platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)

            except:
               import traceback
               logger.error(traceback.format_exc())
               platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)
        else:
           return 'Acceso Denegado (2do.)' # ~ Cloudflare recaptcha

    return video_urls
