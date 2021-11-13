# -*- coding: utf-8 -*-

from core import httptools, scrapertools, jsontools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    page_url = page_url.replace('/fembeder.com/', '/www.fembed.com/').replace('/divload.com/', '/www.fembed.com/').replace('/ilovefembed.best/', '/www.fembed.com/').replace('/myurlshort.live/', '/www.fembed.com/')
    page_url = page_url.replace('/jplayer.club/', '/www.fembed.com/').replace('/fembedisthebest.rest/', '/www.fembed.com/').replace('/pelispng.online/', '/www.fembed.com/').replace('/hlshd.xyz/', '/www.fembed.com/')
    page_url = page_url.replace('/embedsito.com/', '/www.fembed.com/').replace('/mrdhan.com/', '/www.fembed.com/').replace('/dutrag.com/', '/www.fembed.com/').replace('/fplayer.info/', '/www.fembed.com/')

    if 'fembed.com' in page_url:
        page_url = page_url.replace('/fembed.com/', '/www.fembed.com/')
    elif 'fembed.live' in page_url:
        page_url = page_url.replace('/www.fembed.live/', '/dutrag.com/').replace('/fembed.live/', '/dutrag.com/')
    elif 'feurl.com' in page_url:
        page_url = page_url.replace('/www.feurl.com/', '/dutrag.com/').replace('/feurl.com/', '/dutrag.com/')
    elif 'femax20.com' in page_url:
        page_url = page_url.replace('/www.femax20.com/', '/dutrag.com/').replace('/femax20.com/', '/dutrag.com/')
    elif 'fcdn.stream' in page_url:
        page_url = page_url.replace('/www.fcdn.stream/', '/dutrag.com/').replace('/fcdn.stream/', '/dutrag.com/')
    elif 'fembad.org' in page_url:
        page_url = page_url.replace('/www.fembad.org/', '/dutrag.com/').replace('/fembad.org/', '/dutrag.com/')

    dom = scrapertools.find_single_match(page_url, "(https://[^/]+)")

    vid = scrapertools.find_single_match(page_url, "/(?:v|f)/([A-z0-9_-]+)")
    if not vid or not dom: return video_urls

    post = {'r':'', 'd': dom.replace('https://', '')}

    data = httptools.downloadpage(dom + '/api/source/' + vid, post=post).data

    try:
        data = jsontools.load(data)

        if 'data' not in data or 'success' not in data: return 'Vídeo no encontrado'
        if not data['success']: return 'Vídeo no encontrado o eliminado'

        for videos in data['data']:
            if 'file' in videos:
                url = videos['file'] if videos['file'].startswith('http') else dom + videos['file']

                if '/redirector?' in url:
                    resp = httptools.downloadpage(url, follow_redirects=False)
                    if 'location' in resp.headers:
                        url = resp.headers['location']

                lbl = videos['label'] if 'label' in videos and videos['label'] else 'mp4'
                video_urls.append([lbl, url])
    except:
        pass

    return video_urls
