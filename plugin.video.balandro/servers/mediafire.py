# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data

    if "Invalid or Deleted File" in data or "Well, looks like we" in data:
        return "El archivo no existe o ha sido borrado"
    if "File Removed for Violation" in data:
        return "Archivo eliminado por infracción"

    matches = scrapertools.find_multiple_matches(data, "DownloadButtonAd-startDownload gbtnSecondary.*?href='([^']+)'")

    if len(matches) == 0: matches = scrapertools.find_multiple_matches(data, 'Download file.*?href="([^"]+)"')

    if len(matches) > 0:
        video_urls.append([matches[0][-4:], matches[0]])

    return video_urls
