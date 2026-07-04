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


import os, xbmc, re, time

from platformcode import config, logger, platformtools
from core import filetools, httptools, scrapertools


host = 'https://doodstream.com'

player = 'https://playmogo.com'

espera = config.get_setting('servers_waiting', default=6)

color_exec = config.get_setting('notification_exec_color', default='cyan')
el_srv = ('Sin respuesta en [B][COLOR %s]') % color_exec
el_srv += ('ResolveUrl[/B][/COLOR]')

color_alert = config.get_setting('notification_alert_color', default='red')


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

    page_url = page_url.replace('/d/', '/e/')

    data = httptools.downloadpage(page_url, headers={"Referer": host}).data

    if 'Video not found' in data:
        return "Archivo inexistente ó eliminado"

    js_code = scrapertools.find_single_match(data, ("(function\s?makePlay.*?})"))

    if js_code:
        js_code = re.sub("\s+\+\s+Date.now\(\)", '', js_code)

        existe = False
        hay_error = False

        try:
            try:
                import js2py
                existe = True
            except:
                import traceback
                logger.error(traceback.format_exc())

                trace = traceback.format_exc()
                if 'Your python version made changes to the bytecode' in trace:
                    trace = 'RuntimeError: Your python version made changes to the bytecode'

                if config.get_setting('developer_team'):
                    platformtools.dialog_ok(config.__addon_name, '[COLOR red][B]Error en[/B][/COLOR] [COLOR gold][B]Script Module Js2py[/B][/COLOR]', trace)

                hay_error = True
        except:
            pass

        if not hay_error:
            if not existe:
                platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Falta script.module.js2py[/COLOR][/B]' % color_alert)

            if existe:
                js = js2py.eval_js(js_code)

                makeplay = js() + str(int(time.time()*1000))

                if makeplay:
                    if config.get_setting('servers_time', default=True):
                        platformtools.dialog_notification('Cargando [COLOR cyan][B]Dood[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
                        time.sleep(int(espera))

                    url = scrapertools.find_single_match(data, "\$.get\('(/pass[^']+)'")

                    if url:
                        data2 = httptools.downloadpage(player + '/' + url, headers={'Referer': page_url}).data

                        new_url = re.sub(r'\s+', '', data2)

                        if new_url:
                            url = new_url + makeplay + '|Referer=' + page_url.replace(host, player)

                            video_urls.append(['mp4', url])
                            return video_urls

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            path = translatePath(os.path.join('special://home/addons/script.module.resolveurl/lib/resolveurl/plugins/', 'doodstream.py'))

            existe = filetools.exists(path)
            if not existe:
                return 'El Plugin No existe en Resolveurl'

            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Doodstream[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
                time.sleep(int(espera))

            try:
                import_libs('script.module.resolveurl')

                if xbmc.getCondVisibility('System.HasAddon("script.module.cloudrequest")'):
                    import_libs('script.module.cloudrequest')

                import resolveurl
                page_url = ini_page_url
                resuelto = resolveurl.resolve(page_url)

                if resuelto:
                    video_urls.append(['mp4', resuelto + '|Referer=%s' % page_url])
                    return video_urls

                color_exec = config.get_setting('notification_exec_color', default='cyan')
                el_srv = ('Sin respuesta en [B][COLOR %s]') % color_exec
                el_srv += ('ResolveUrl[/B][/COLOR]')
                platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)

                page_url = ini_page_url

                return 'ResolveUrl No se pudo Reproducir el Vídeo'

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

                   elif 'BYPARR not available' in trace:
                       return 'No está Habilitado el Acceso a ByParr'

               elif "No module named 'cloudscraper'" in traceback.format_exc():
                   return 'Falta script.module.cloudrequest'

               elif 'HTTP Error 404: Not Found' in traceback.format_exc() or '404 Not Found' in traceback.format_exc():
                   return 'Archivo inexistente'

               elif 'HTTP Error 403: Forbidden' in traceback.format_exc() or '403 Forbidden' in traceback.format_exc():
                   return 'Archivo bloqueado'

               elif '<urlopen error' in traceback.format_exc():
                   return 'No se puede establecer la conexión'

               return 'Sin Respuesta ResolveUrl'

        else:
           return 'Falta ResolveUrl'

    return video_urls
