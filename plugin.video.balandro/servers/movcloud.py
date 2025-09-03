# -*- coding: utf-8 -*-

import os

from core import httptools, filetools, scrapertools, jsontools
from platformcode import config, logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    path_server = os.path.join(config.get_runtime_path(), 'servers', 'zplayer.json')
    data = filetools.read(path_server)
    dict_server = jsontools.load(data)

    try:
       notes = dict_server['notes']
    except: 
       notes = ''

    if "out of service" in notes.lower(): return 'Fuera de Servicio'

    vid = scrapertools.find_single_match(page_url, "embed/([A-z0-9_-]+)")

    if vid:
        data = httptools.downloadpage('https://api.movcloud.net/stream/' + vid).data

        if '"message":"NOT_FOUND"' in str(data):
            return 'Archivo inexistente ó eliminado'

        url = scrapertools.find_single_match(data, '"file":"([^"]+)')
        if url: video_urls.append(["mp4", url])

    return video_urls
