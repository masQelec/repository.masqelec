# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://hentaila.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

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

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', search_video = 'adult', text_color='orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'catalogo' ))

    itemlist.append(item.clone( title = 'Últimos', action = 'list_all', url = host + 'catalogo?order=latest_released', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'catalogo?order=popular' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'catalogo?order=score' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'catalogo?status=emision' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'catalogo?status=finalizado' ))

    itemlist.append(item.clone( title = 'Sin censura', action = 'list_all', url = host + 'catalogo?uncensored=', text_color = 'tan' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    matches = []

    data = httptools.downloadpage(host + 'catalogo').data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    bloque = scrapertools.find_single_match(str(data), 'genresIdsMap:(.*?)filters:')

    cats = scrapertools.find_multiple_matches(bloque, 'id:.*?name:"(.*?)",.*?slug:"(.*?)"')

    if cats:
        for name, slug in cats:
            matches.append(('?genre={}'.format(slug), name))

        for url, title in matches:
            url = '{}catalogo{}'.format(host, url)

            itemlist.append(item.clone( action = 'list_all', url = url, title = title, text_color='moccasin' ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3 class=".*?">(.*?)</h3>')
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        url = host[:-1] + url

        itemlist.append(item.clone( action = 'episodios', url = url, title = title, thumbnail = thumb,
                                   contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        if '</span><!--]--><!--]--><!--[!--><!--[!--><a class=' in data:
            datap = str(data).replace('</span><!--]--><!--]--><!--[!--><!--[!--><a class=', 'next_url=').strip()

            next_page = scrapertools.find_single_match(str(datap), 'next_url=.*?href="(.*?)"')

            if next_page:
                next_page = next_page.replace('&amp;', '&').strip()

                if '?page=' in next_page or '&page=' in next_page:
                     next_page = host[:-1] + next_page

                     itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    bloque = scrapertools.find_single_match(data, '>Episodios<(.*?)</section>')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(str(bloque))

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        url = host[:-1] + url

        title = scrapertools.find_single_match(match, '<span class="sr-only">(.*?)</span>')

        title = title.replace('Ver ', '').strip()

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        titulo = title.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults' ))

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
    data = re.sub(r'\n|\r|\t|\s{2}', "", data)

    lang = 'Vose'

    bloque = scrapertools.find_single_match(data, 'var videos =(.*?)</script>')

    matches = re.compile('server:.*?"(.*?)".*?url:.*?"(.*?)"', re.DOTALL).findall(str(data))

    ses = 0

    for srv, url in matches:
        ses += 1

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        if not servidor == 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url,
                                  language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'catalogo?search=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
