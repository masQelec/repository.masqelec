# -*- coding: utf-8 -*-

from core import httptools, scrapertools, jsontools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return "El fichero no existe o ha sido borrado"

    id = scrapertools.find_single_match(page_url, '/e/(\w+)')
    if not id: id = scrapertools.find_single_match(page_url, '/v/(\w+)')

    post = {"id": id}

    data = httptools.downloadpage("https://streamlare.com/api/video/stream/get", post=post).data

    jdata = jsontools.load(data)

    try:
        media_url = jdata["result"]["file"]
    except:
        media_url = scrapertools.find_single_match(str(jdata), ".*?'file':.*?'(.*?)'")

    if media_url:
        media_url += "|User-Agent=%s" %(httptools.get_user_agent())
        video_urls.append(["m3u", media_url])

    return video_urls
