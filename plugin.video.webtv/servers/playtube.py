# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from lib import jsunpack
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url)
    # ~ logger.debug(data)

    if data.code == 404 or "File is no longer available" in data.data:
        return 'El archivo no existe o ha sido borrado'

    pack = scrapertools.find_single_match(data.data, 'p,a,c,k,e,d.*?</script>')
    unpacked = jsunpack.unpack(pack)
    url = scrapertools.find_single_match(unpacked, 'file:"([^"]+)') + "|referer=%s" %(page_url)

    if url != '':
        video_urls.append(["%s" % url[-3:], url])

    return video_urls