# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://pandrama.buzz/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', search_type = 'tvshow', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Episodios Recientes', action = 'list_all', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)Próximamente')
    if not bloque: bloque = scrapertools.find_single_match(data, 'Search Results for:(.*?)</form>')

    matches = re.compile('<div class="recent-item(.*?)</p></div>').findall(bloque)
    if not matches: matches = re.compile('<article(.*?)</article>').findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3 class="post-box-title">.*?rel="bookmark">(.*?)</a>')
        if not title: title = scrapertools.find_single_match(match, '<h2 class="post-box-title">.*?">(.*?)</a>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        title = title.replace('&#8230;', '&').replace('&#038;', '&').replace('&#8217;', "'")

        epis = scrapertools.find_single_match(title, 'Capitulo (.*?)$')
        if not epis: epis = scrapertools.find_single_match(title, 'Cap (.*?)$')

        if not epis: epis = 1

        SerieName = title

        if 'Capitulo ' in SerieName: SerieName = SerieName.split("Capitulo ")[0]
        elif 'Cap ' in SerieName: SerieName = SerieName.split("Cap ")[0]

        SerieName = SerieName.strip()

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType = 'episode', contentSerieName = SerieName, episode = epis, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<span class="current">.*?<a href="(.*?)"')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title="Siguientes ...", action="list_all", url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<IFRAME SRC=(".*?)"')
    if not matches: matches = scrapertools.find_multiple_matches(data, '<iframe src=(".*?)"')

    ses = 0

    for url in matches:
        ses += 1

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)

        if not servidor == 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = 'Vose', other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        item.text = texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
