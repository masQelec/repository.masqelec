# -*- coding: utf-8 -*-

from platformcode import logger
from core import httptools, scrapertools
from lib import balandroresolver

def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)

    video_urls = []

    page_url = page_url.replace('/uptobox/', '/uptobox.com/')

    vid = scrapertools.find_single_match(page_url, "(?:uptobox.com/|uptostream.com/)(?:iframe/|)([A-z0-9]+)")
    if not vid: return video_urls

    try:
       video_urls = balandroresolver.resolve_uptobox().getLink(vid, video_urls)
    except Exception as e:
       if '150 minutos' in e:
           return "Debes esperar 150 minutos para poder reproducir"
       elif 'Unfortunately, the file you want is not available' in e or 'Unfortunately, the video you want to see is not available' in e or 'This stream doesn' in e or 'Page not found' in e or 'Archivo no encontrado' in e:
           return "El archivo no existe o ha sido borrado"
       elif "'str' object has no attribute 'get'":
           return video_urls

       return "Acceso temporalmente restringido"

    except:
       import traceback
       logger.error(traceback.format_exc(1))

    return video_urls

