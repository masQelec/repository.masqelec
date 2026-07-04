# -*- coding: utf-8 -*-

import xbmc, time

from core import httptools, scrapertools
from platformcode import config, logger, platformtools


espera = config.get_setting('servers_waiting', default=6)


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    if config.get_setting('servers_time', default=True):
        platformtools.dialog_notification('Cargando [COLOR cyan][B]Esprinahy[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)
        time.sleep(int(espera))

    data = httptools.downloadpage(page_url).data

    bloque = scrapertools.find_single_match(data, '<table(.*?)</table>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<td>(.*?)</td>')

    for media, qlty in matches:
        qlty = qlty.replace(',', '').strip()

        datal = httptools.downloadpage(media).data

        op = scrapertools.find_single_match(datal, '<input type="hidden" name="op" value="(.*?)"')
        id = scrapertools.find_single_match(datal, '<input type="hidden" name="id" value="(.*?)"')
        mode = scrapertools.find_single_match(datal, '<input type="hidden" name="mode" value="(.*?)"')
        hash = scrapertools.find_single_match(datal, '<input type="hidden" name="hash" value="(.*?)"')

        post ={'op': op, 'id': id, 'mode': mode, 'hash': hash}

        headers = {'Referer': media}

        timeout = config.get_setting('channels_repeat', default=30)

        xbmc.sleep(500)

        datap = httptools.downloadpage(media, post = post, headers = headers, timeout = timeout).data

        url = scrapertools.find_single_match(datap, '>File Download Link Generated<.*?href="(.*?)"')

        if url:
            video_urls.append(["%s %s" % ('mp4', qlty), url])

    return video_urls
