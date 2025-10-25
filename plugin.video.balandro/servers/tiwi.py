# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True


import re

from core import httptools, scrapertools
from platformcode import logger

from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    headers = {}

    if "|Referer=" in page_url:
        page_url, referer = page_url.split("|")
        referer = referer.replace('Referer=', '')
        headers = {'Referer': referer}

    if '/okhd.' in page_url:
        headers = {'Referer': 'https://mp4.nu/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site'} 

    resp = httptools.downloadpage(page_url, headers=headers)

    if resp.code == 404 or "not found" in resp.data:
        return 'Archivo inexistente ó eliminado'

    data = resp.data

    if '/okhd.' in page_url:
        try:
            enc_data = scrapertools.find_multiple_matches(data, "text/javascript(?:'|\")>(eval.*?)</script>")
            dec_data = jsunpack.unpack(enc_data[-1])
        except:
            dec_data = data

        sources = 'sources\:\s*\[\{(?:file|src):"([^"]+)"'

        try:
            matches = re.compile(sources, re.DOTALL).findall(dec_data)
            for url in matches:
                video_urls.append(['m3u8', url])
        except:
            pass

        return video_urls

    try:
        pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(pack)

        m3u8_source = scrapertools.find_single_match(unpacked, '\{(?:file|"hls\d+"|src):"([^"]+)"')

        if "master.m3u8" in m3u8_source:
            if not 'http' in m3u8_source: m3u8_source = 'https:/' + m3u8_source

            datos = httptools.downloadpage(m3u8_source).data

            if PY3:
                if isinstance(datos, bytes):
                    datos = "".join(chr(x) for x in bytes(datos))

            if datos:
                matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)

                for quality, url in matches_m3u8:
                    m3u8_source = m3u8.split("/master.m3u8")[0]
                    url = m3u8_source + url

                    if 'urlsetindex-' in url: url = url.replace('urlsetindex-', 'urlset/index-')

                    elif 'index-v1-a1.m3u8' in url:
                        if not '/index-v1-a1.m3u8' in url: url = url.replace('index-v1-a1.m3u8', '/index-v1-a1.m3u8')

                    video_urls.append([quality, 'M3u', url])

            if not video_urls:
                m3u8_source = scrapertools.find_single_match(unpacked, '"hls2":"(.*?)"')

                if m3u8_source:
                    video_urls.append(['m3u', m3u8_source])
        else:
            m3u8_source = scrapertools.find_single_match(unpacked, '"hls2":"(.*?)"')

            if m3u8_source:
                video_urls.append(['m3u', m3u8_source])

    except Exception:
        pass

    return video_urls
