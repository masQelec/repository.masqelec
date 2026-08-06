# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://xmoviesforyou.com/'


def do_downloadpage(url, post=None, headers=None):
    timeout = None
    if host in url: timeout = config.get_setting('channels_repeat', default=30)

    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if not data:
        if url.startswith(host):
            if not '/search?q=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('XmoviesForYou', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', search_video = 'adult', text_color = 'orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'most-viewed'))

    itemlist.append(item.clone( title = 'Por estudio', action = 'estudios', url = host + 'studios?page=1' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + 'categories/' ))
    itemlist.append(item.clone( title = 'Por estrella', action = 'pornstars', url = host + 'pornstars?page=1' ))

    return itemlist


def estudios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>All Studios<(.*?)</main>')

    matches = re.compile('<a(.*?)</a>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3.*?">(.*?)</h3>')

        if not url or not title: continue

        url = host[:-1] + url

        itemlist.append(item.clone (action='list_all', title=title, url=url, text_color='orange' ))

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="flex justify-center mt-12 gap-2">(.*?)</main>')

        next_page = scrapertools.find_single_match(bloque, '<a href="(.*?)"')

        if next_page:
            next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='estudios', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Categories</h1>(.*?)</main>')

    matches = re.compile('<a(.*?)</a>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3.*?">(.*?)</h3>')

        if not url or not title: continue

        url = host[:-1] + url

        itemlist.append(item.clone (action='list_all', title=title, url=url, text_color = 'moccasin' ))

    return sorted(itemlist, key=lambda x: x.title)


def pornstars(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>All Pornstars<(.*?)</main>')

    matches = re.compile('<a(.*?)</a>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        url = host[:-1] + url

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail=thumb, text_color='orange' ))

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="flex justify-center mt-12 gap-2">(.*?)</main>')

        next_page = scrapertools.find_single_match(bloque, '<a href="(.*?)"')

        if next_page:
            next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='pornstars', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    if '</h1>' in data:
        bloque = scrapertools.find_single_match(data, '</h1>(.*?)$')
    else:
        bloque = data

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?src="(.*?)".*?alt="(.*?)"')

    for url, thumb, title in matches:
        if not title: continue

        url = host[:-1] + url

        itemlist.append(item.clone (action='findvideos', title=title, url=url, thumbnail=thumb,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="flex justify-center mt-12 gap-2">(.*?)</section>')
        if not bloque: bloque = scrapertools.find_single_match(data, '<div class="flex justify-center mt-12 gap-2">(.*?)</main>')

        if not '>Prev</a>' in bloque:
            next_page = scrapertools.find_single_match(bloque, '<a href="(.*?)"')
        else:
            next_page = scrapertools.find_single_match(bloque, '>Prev</a>.*?<a href="(.*?)"')

        if next_page:
            next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '<div class="flex flex-wrap gap-4 mb-8">(.*?)</div>')

    matches = re.compile('<a href="([^"]+)"', re.DOTALL).findall(bloque)

    ses = 0

    for url in matches:
        ses += 1

        # ~ Netu
        if not "0load" in url:
            servidor = servertools.get_server_from_url(url)

            url = servertools.normalize_url(servidor, url)

            if '/bigwarp.' in url or '/bgwp.' in url: servidor = 'zures'

            other = ''

            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'zures': other = servertools.corregir_zures(url)

            itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server=servidor,
                                  language = 'Vo', other = other.capitalize()) )

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'search?q=%s' % (texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
