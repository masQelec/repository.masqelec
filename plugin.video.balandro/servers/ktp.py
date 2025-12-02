# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


import re

from datetime import datetime

from platformcode import logger
from core import httptools, scrapertools

from lib.serverkt import decode


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    url = ''

    resp = httptools.downloadpage(page_url)

    if resp.code == 404:
        return 'Archivo inexistente ó eliminado'

    elif "Page not Found" in resp.data or "File was deleted" in resp.data or "not allowed to watch this video" in resp.data or "is no longer available" in resp.data:
        return 'Archivo inexistente ó eliminado'

    elif "cwtvembeds" in page_url or "Embed Player Error" in resp.data:
        return 'Archivo con Errores'

    elif "video is a private" in resp.data:
        return 'Archivo Privado restringido'

    data = resp.data

    host = "https://%s/" % scrapertools.get_domain_from_url(page_url)

    license_code = scrapertools.find_single_match(resp.data, 'license_code:\s*(?:\'|")([^\,]+)(?:\'|")')

    data = httptools.downloadpage(page_url,).data

    if "flashvars.video_url_text" in data:
        data = scrapertools.find_single_match(data, '(flashvars.video_url[^\}]+)')
        patron = "(?:flashvars.video_url|flashvars.video_alt_url)\s*=\s*'([^']+)'.*?"
        patron += "(?:flashvars.video_url_text|flashvars.video_alt_url_text)\s*=\s*'([^']+)'"

    elif "video_url_text" in data:
        patron = '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += '(?:video_url_text|video_alt_url_text|video_alt_url[0-9]*_text):\s*(?:\'|")([^\,]+)(?:\'|")'

    else:
        patron = 'video_url:\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += 'postfix:\s*(?:\'|")([^\,]+)(?:\'|")'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for url, qlty in matches:
        if "?login" not in url and "signup" not in url and "_preview" not in url and ".mp4" in url:
            if "function/" in url: url = decode(url, license_code)

            elif url.startswith("/get_file/"): url = urlparse.urljoin(page_url, url)

            if "FHD" in qlty: qlty = "1080p"
            elif "HD" in qlty and not "Full" in qlty: qlty = "720p"
            else:
                if "1080p" in qlty: qlty = "1080p"
                elif "720p" in qlty: qlty = "720p"
                elif "540p" in qlty: qlty = "540p"
                elif "480p" in qlty: qlty = "480p"
                elif "360p" in qlty: qlty = "360p"
                elif ".mp4" in qlty: qlty = "mp4"
                else: qlty = ""

            if "?br=" in url: url += "&rnd=" + str(int(datetime.now().timestamp() * 1000))

            url += "|Referer=%s" % host

            video_urls.append(['mp4 %s' % qlty, url])

    if not url:
        url = scrapertools.find_single_match(data, '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?')

        url += "|Referer=%s" % host

        video_urls.append(['mp4', url])

        return video_urls

    return video_urls

