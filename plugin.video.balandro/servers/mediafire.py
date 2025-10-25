# -*- coding: utf-8 -*-

import base64

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data

    if "Invalid or Deleted File" in data or "Well, looks like we" in data:
        return "Archivo inexistente ó eliminado"
    elif "File Removed for Violation" in data:
        return "Archivo eliminado por infracción"
    elif "Upload still in progress" in data:
        return "Archivo aún No disponible"

    matches = scrapertools.find_multiple_matches(data, "DownloadButtonAd-startDownload gbtnSecondary.*?href='([^']+)'")
    if not matches: matches = scrapertools.find_multiple_matches(data, 'Download file.*?data-scrambled-url="([^"]+)"')

    if not matches:
         match = scrapertools.find_single_match(str(data), 'window.location.href =' + ".*?'(.*?)'")
         if match == '/login?l=1': match = ''

         if not match: match = scrapertools.find_single_match(str(data), 'Download file.*?href="(.*?)"')

         if match:
             if '.rar' in match or '.zip' in match:
                 return "El archivo está en formato comprimido"

             video_urls = [[match[-4:], match]]
             return video_urls

    if len(matches) > 0:
        if not 'javascript:void' in matches[0]:
            url = base64.b64decode(matches[0]).decode('utf-8')
            video_urls.append([url[-4:], url])

    if not video_urls:
        if '.rar' in page_url or '.zip' in page_url:
            return "El archivo está en formato comprimido"

    return video_urls
