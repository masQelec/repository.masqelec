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


import os, xbmc, time

from platformcode import config, logger, platformtools
from core import filetools, httptools, scrapertools

from lib import jsunpack


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
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    ini_page_url = page_url

    page_url = page_url.replace('supervideo.cc/emb.html?','supervideo.cc/e/')

    video_urls = get_video_url_embed(page_url, url_referer)
    if not type(video_urls) == list: return video_urls

    if len(video_urls) == 0:
        video_urls = get_video_url_download(page_url, url_referer)

    if not video_urls:
        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            path = translatePath(os.path.join('special://home/addons/script.module.resolveurl/lib/resolveurl/plugins/', 'vidmoly.py'))

            existe = filetools.exists(path)
            if not existe:
                return 'El Plugin No existe en Resolveurl'

            if config.get_setting('servers_time', default=True):
                platformtools.dialog_notification('Cargando [COLOR cyan][B]Supervideo[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
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


def get_video_url_embed(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    if 'supervideo.cc/e/' not in page_url:
        page_url = page_url.replace('supervideo.cc/','supervideo.cc/e/')

    data = httptools.downloadpage(page_url).data

    if '<title>404 Not Found</title>' in data:
        return 'Archivo inexistente ó eliminado'

    elif "File is no longer available as it expired or has been deleted" in data or "File Not Found" in data:
        return 'Archivo inexistente ó eliminado'

    packed = scrapertools.find_multiple_matches(data, "(?s)eval(.*?)\s*</script>")

    for pack in packed:
        try:
            data = jsunpack.unpack(pack)
        except:
            data = ''

        if 'sources:[' in data: break

    bloque = scrapertools.find_single_match(data, 'sources:\s*\[(.*?)\]')

    matches = scrapertools.find_multiple_matches(bloque, '\{(.*?)\}')

    for vid in matches:
        url = scrapertools.find_single_match(vid, 'file:"([^"]+)')
        if not url: continue

        lbl = scrapertools.find_single_match(vid, 'label:"([^"]+)')
        if not lbl: lbl = url[-4:]
        video_urls.append([lbl, url+'|Referer=https://supervideo.cc/'])

    try:
        video_urls = sorted(video_urls, key=lambda x: 0 if x[0] == 'm3u8' else int(x[0].replace('p','')) )
    except:
        pass

    return video_urls


def get_video_url_download(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    if 'supervideo.cc/e/' in page_url:
        page_url = page_url.replace('supervideo.cc/e/','supervideo.cc/')

    data = httptools.downloadpage(page_url).data

    if '<title>404 Not Found</title>' in data:
        return 'Archivo inexistente ó eliminado'
 
    elif "File is no longer available as it expired or has been deleted" in data or "File Not Found" in data:
        return 'Archivo inexistente ó eliminado'

    if 'download_video(' not in data:
        post = {
            'op': scrapertools.find_single_match(data, '<input type="hidden" name="op" value="([^"]+)'),
            'usr_login': scrapertools.find_single_match(data, '<input type="hidden" name="usr_login" value="([^"]+)'),
            'id': scrapertools.find_single_match(data, '<input type="hidden" name="id" value="([^"]+)'),
            'fname': scrapertools.find_single_match(data, '<input type="hidden" name="fname" value="([^"]+)'),
            'referer': scrapertools.find_single_match(data, '<input type="hidden" name="referer" value="([^"]+)'),
            'hash': scrapertools.find_single_match(data, '<input type="hidden" name="hash" value="([^"]+)'),
        }

        if post['id'] and post['hash']:
            data = httptools.downloadpage(page_url, post=post).data

    matches = scrapertools.find_multiple_matches(data, "download_video\('([^']+)','([^']+)','([^']+)'\)\">([^<]+)</a></td><td>([^<]+)")

    if not matches:
        matches = scrapertools.find_multiple_matches(data, "download_video\('([^']+)','([^']+)','([^']+)'\)\">.*? class=\"downloadbox__quality\">([^<]+)</b><span class=\"downloadbox__size\">([^<]+)")

    for a, b, c, titulo, desc in matches:
        if b == 'l' and len(video_urls) > 1: continue # descartar low si ya hay original y normal

        data = httptools.downloadpage('https://supervideo.cc/dl?op=download_orig&id=%s&mode=%s&hash=%s' % (a, b, c)).data

        url = scrapertools.find_single_match(data, ' href="([^"]+)">Direct Download Link</a>')
        if not url: url = scrapertools.find_single_match(data, 'btn_direct-download" href="([^"]+)')

        if not url:
            post = {'op': 'download_orig', 'id': a, 'mode': b, 'hash': c}
            data = httptools.downloadpage('https://supervideo.cc/dl', post=post).data

            url = scrapertools.find_single_match(data, '<a href="([^"]+)">Direct Download Link</a>')
            if not url: url = scrapertools.find_single_match(data, 'btn_direct-download" href="([^"]+)')

        if url:
            video_urls.append(["%s - %s" % (titulo.replace(' quality', '').strip(), desc.strip()), url])

    video_urls.reverse()

    return video_urls
