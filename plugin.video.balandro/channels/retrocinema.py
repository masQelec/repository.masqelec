# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://online.historiadelcine.es/'


perpage = 25


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/?s=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('RetroCinema', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone ( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone ( title = 'Últimas', action = 'list_all', url = host, text_color = 'cyan', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<ul id="menu-main"(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    for url, title in matches:
        if 'Más<' in title: continue

        itemlist.append(item.clone( action='list_all', title=title, url=url, text_color = 'deepskyblue' ))

    return sorted(itemlist, key = lambda it: it.title)


def list_all(item): 
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    if '>Últimas películas clásicas añadidas<' in data:
        data = scrapertools.find_single_match(data, '>Últimas películas clásicas añadidas<(.*?)<div class="copyright-bar">')
    else:
        data = scrapertools.find_single_match(data, '</h2>(.*?)<div class="copyright-bar">')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    num_matches = len(matches)

    for article in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(article, ' href="(.*?)"')

        title = scrapertools.find_single_match(article, 'title="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#8211;', '').strip()

        thumb = scrapertools.find_single_match(article, ' src="(.*?)"')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace(('(' + year + ')'), '').strip()
        else: year = '-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page = item.page + 1, action='list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if 'Película completa en español' in data: lang = 'Esp'
    else: lang = '?'

    matches = scrapertools.find_multiple_matches(data, '<iframe.*?data-src="(.*?)".*?</iframe>')

    if not matches:
        matches = scrapertools.find_multiple_matches(data, 'youtube_url(.*?)&quot;,&quot;')

    ses = 0

    for url in matches:
        ses += 1

        url = url.replace('\\/', '/').replace('&quot;:&quot;','').strip()

        if url.startswith("//"): url = 'https:' + url

        servidor = servertools.get_server_from_url(url)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''
        if servidor == 'directo':
            if not config.get_setting('developer_mode', default=False): continue
            other = url.replace('https://', '').strip()

        url = servertools.normalize_url(servidor, url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    post = {'Referer': host, 'Content-Disposition': 'form-data', 'action': 'zeus_ajax_search', 'nonce': '8dd2cfb37b', 'search': item.tex, 'type': 'post'}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post)

    matches = re.compile('<li>(.*?)</li>', re.DOTALL).findall(data)

    num_matches = len(matches)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="(.*?)"')

        title = scrapertools.find_single_match(article, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="(.*?)"')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace(('(' + year + ')'), '').strip()
        else: year = '-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s='
        item.tex = texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
