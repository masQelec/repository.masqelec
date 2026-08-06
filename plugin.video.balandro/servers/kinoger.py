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


import os, xbmc, time, binascii

from platformcode import config, logger, platformtools
from core import filetools, httptools, jsontools, scrapertools


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

    if url_referer: ini_page_url = url_referer

    resp = httptools.downloadpage(page_url)

    if resp.code == 404:
        return 'Archivo inexistente ó eliminado'

    data = resp.data

    try:
       import_libs('script.module.pyaes')

       import pyaes

       id_url = scrapertools.find_single_match(page_url, '/#(.*?)$')

       if '|Referer=' in id_url: id_url = id_url.split("|Referer=")[0]

       if id_url:
           new_url = page_url.split("/#")[0]

           new_url = new_url + '/api/v1/video?id=' + id_url

           data = httptools.downloadpage(new_url).data

       edata = binascii.unhexlify(data[:-1])

       key = b'\x6b\x69\x65\x6d\x74\x69\x65\x6e\x6d\x75\x61\x39\x31\x31\x63\x61'
       iv = b'\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x6f\x69\x75\x79\x74\x72'

       decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))

       ddata = decrypter.feed(edata)
       ddata += decrypter.feed()

       ddata = ddata.decode('utf-8')
       ddata = jsontools.load(ddata)

       url = scrapertools.find_single_match(str(ddata), "'source': '(.*?)'")

       if url:
           url += "|User-Agent={0}&Referer={1}/&Origin={1}".format(httptools.get_user_agent(), page_url)

           video_urls.append(['m3u8', url])
    except:
        pass

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            path = translatePath(os.path.join('special://home/addons/script.module.resolveurl/lib/resolveurl/plugins/', 'kinoger.py'))

            existe = filetools.exists(path)
            if not existe:
                return 'El Plugin No existe en Resolveurl'

            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Kinoger[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
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

                    elif 'No se ha encontrado ningún link al' in trace or 'Unable to locate link' in trace or 'Video Link Not Found' in trace or 'No playable video found' in trace:
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
