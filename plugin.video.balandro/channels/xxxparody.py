# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://xxxparodyhd.net/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/release-year/free-' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

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

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', text_color = 'orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'most-viewed/' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'most-rating/' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'canales', url = host ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', url = host ))

    return itemlist


def canales(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '>Studios<(.*?)</ul>')

    matches = re.compile('<a href="(.*?)".*?>(.*?)</a>').findall(bloque)

    for url, title in matches:
        title = title.replace('&amp;', '&').replace('&#8217;', "'").strip()

        title = title.capitalize()

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'violet' ))

    return sorted(itemlist, key=lambda x: x.title)


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '>Categories<(.*?)</ul>')

    matches = re.compile('<a href="(.*?)".*?>(.*?)</a>').findall(bloque)

    for url, title in matches:
        title = title.capitalize()

        itemlist.append(item.clone (action='list_all', title = title, url = url, text_color = 'moccasin' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []


    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1969, -1):
        url = host + 'release-year/free-' + str(x) + '/'

        itemlist.append(item.clone( title=str(x), url=url, action='list_all', text_color = 'orange' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    patron = 'class="ml-item">.*?<a href="([^"]+)".*?oldtitle="([^"]+)".*?<img src="(.*?)"'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for url, title, thumb in matches:
        title = title.replace('&#8217;s', "'s").replace('&#8217;t', "'t").replace('&#8211;', '').replace('&amp;', '&').replace('&#038;', '').strip()

        itemlist.append(item.clone (action='findvideos', title=title, url=url, thumbnail=thumb,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div id="pagination".*?' + "<li class='active'>.*?href='(.*?)'.*?</nav>")
        if not next_page: next_page = scrapertools.find_single_match(data, "<div id='pagination'.*?<li class='active'>.*?href='(.*?)'.*?</nav>")

        if next_page:
            itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

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

    bloque = scrapertools.find_single_match(data, '<div id="playcontainer"(.*?)<div id="mv-info">')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)"')

    ses = 0

    for url in matches:
        ses += 1

        if '/frdl.' in url: continue
        elif '/drivevideo.' in url: continue
        elif '/snowdayonline.' in url: continue
        elif '/freepopnews.' in url: continue
        elif '/filepv.' in url: continue
        elif '/vinovo.' in url: continue

        elif '.seekplayer.' in url: continue
        elif '.streamkithmc.' in url: continue
        elif '.streamkitagg.' in url: continue
        elif '.cloudwarebrh.' in url: continue
        elif '.video-twimg.' in url: continue

        elif '/nitroflare.' in url: continue
        elif 'rapidgator.' in url: continue

        elif '/pooptv.' in url: continue
        elif '=pooptv.me' in url: continue

        ref = url

        servidor = servertools.get_server_from_url(url)

        url = servertools.normalize_url(servidor, url)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        force_input = ''
        if other == 'Lulustream': force_input = True

        if servidor == 'kinoger':
            if config.get_setting('developer_team'): other = url
        else: ref = ''

        if not servidor == 'directo':
            itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server=servidor, ref=ref,
                                  language = 'Vo', other = other.capitalize(), force_input=force_input ))

    # ~ Descargas No se tratan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if url:
        if item.server == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = item.server))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = "%ssearch/%s" % (host, texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


