# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3:
    from urllib.parse import urlencode
else:
    from urllib import urlencode


from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    page_url = page_url.replace('http://', 'https://').replace('://www.', '://')

    data = httptools.downloadpage(page_url).data

    if "File Not Found" in data or "File was deleted" in data or "File is no longer available as it expired or has been deleted" in data:
        return 'Archivo inexistente ó eliminado'
    elif "Video is processing now." in data:
        return 'Vídeo en Proceso, Intentelo más tarde'

    unpacked = ''

    if 'sources: [' in data:
        video_urls = extract_sources(data)
    else:
        try:
            packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")

            if packed:
                unpacked = jsunpack.unpack(packed)

        except:
            unpacked = scrapertools.find_single_match(data,"window.hola_player.*")

        if unpacked:
            if '/lamovie.' in page_url:
                url = scrapertools.find_single_match(unpacked, '<source src="([^"]+)"')

                if url:
                    host = 'https://lamovie.link/'

                    headers = httptools.default_headers.copy()
                    headers = "|{0}&Referer={1}/&Origin={1}".format(urlencode(headers), host)

                    video_urls.append(['m3u8', url + headers])
            else:
               video_urls = extract_sources(unpacked)

    if not video_urls:
        videos = scrapertools.find_multiple_matches(unpacked or data, r'(?:file|src|sources):\s*(?:\[)?"([^"]+)"(?:,label:\s*"([^"]+))?')

        for video, label in videos:
            if ".jpg" not in video:
                label = video.split('.')[-1]

            video_urls.append([label, video])

    return video_urls


def extract_sources(data):
    video_urls = []

    bloque = scrapertools.find_single_match(data, 'sources: \[(.*?\})\]')

    matches = scrapertools.find_multiple_matches(bloque, '\{(.*?)\}')

    for vid in matches:
        url = scrapertools.find_single_match(vid, 'src:\s*"([^"]+)')
        if not url: url = scrapertools.find_single_match(vid, 'file:\s*"([^"]+)')
        if not url: continue

        if url.startswith('//'): url = 'https:' + url

        if url.endswith('.m3u8'):
            aux = httptools.downloadpage(url).data

            if len(aux) == 0: return video_urls

            matches2 = scrapertools.find_multiple_matches(aux, 'RESOLUTION=\d+x(\d+).*?(http.*?\.m3u8)')
            if matches2:
                for res2, url2 in sorted(matches2, key=lambda x: int(x[0])):
                    if '/iframes' in url2: continue
                    if '/index-v1-a1.m3u8' not in url2: continue

                    url2 = url2.replace('/hls/', '/').replace('/index-v1-a1.m3u8', '/v.mp4')
                    video_urls.append(['mp4 ' + res2 + 'p', url2])

            if len(video_urls) == 0: video_urls.append(['m3u8', url])

        else:
            lbl = scrapertools.find_single_match(vid, 'label:\s*"([^"]+)')
            if not lbl: lbl = scrapertools.find_single_match(vid, 'type:\s*"([^"]+)')
            if not lbl: lbl = url[-4:]
            video_urls.append([lbl, url])

    return video_urls
