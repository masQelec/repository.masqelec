# -*- coding: utf-8 -*-

import binascii

from core import httptools, jsontools, scrapertools
from platformcode import logger

import pyaes


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    resp = httptools.downloadpage(page_url)

    if resp.code == 404:
        return 'Archivo inexistente ó eliminado'

    data = resp.data

    try:
        edata = binascii.unhexlify(data[:-1])
        key = b'\x6b\x69\x65\x6d\x74\x69\x65\x6e\x6d\x75\x61\x39\x31\x31\x63\x61'
        iv = b'\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x6f\x69\x75\x79\x74\x72'

        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        ddata = decrypter.feed(edata)
        ddata += decrypter.feed()

        ddata = ddata.decode('utf-8')
        ddata = jsontools.load(ddata)

        url = scrapertools.find_multiple_matches(ddata, "source'([^']+)'")

        if url:
            url += "|User-Agent={0}&Referer={1}/&Origin={1}".format(httptools.get_user_agent(), page_url)

            video_urls.append(['m3u8', url])
    except:
        pass

    return video_urls
