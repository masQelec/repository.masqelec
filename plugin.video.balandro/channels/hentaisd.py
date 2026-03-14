# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://hentaisd.tv/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'hentai/?page=1' ))

    itemlist.append(item.clone( title = 'Sin censura', action = 'list_all', url = host + 'hentai/sin-censura/?page=1', text_color = 'tan' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'hentai?status=en_emision&page=1' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'hentai?status=finalizado&page=1' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'hentai/').data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Géneros(.*?)>Año')

    matches = re.compile('value="(.*?)".*?<span class="ml-3 text-white text-sm">(.*?)</span>', re.DOTALL).findall(bloque)

    for gen, title in matches:
        title = title.replace('&ntilde;', 'ñ')

        title = title.replace('&amp;oacute;', 'o').replace('&amp;iacute;', 'i').replace('&amp;ntilde;', 'ñ')

        title = title.capitalize()

        url = host[:-1] + '/hentai?genre_ids[0]=' + gen + '&page=1'

        itemlist.append(item.clone( action = 'list_all', url = url, title = title, text_color='moccasin' ))

    return sorted(itemlist, key=lambda i: i.title)


def anios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'hentai/').data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<select wire:model.live="year"(.*?)</select>')

    matches = re.compile('<option value="(.*?)".*?>(.*?)</option>', re.DOTALL).findall(bloque)

    for anio, title in matches:
        if not anio: continue

        elif title == 'Todos': continue

        url = host[:-1] + '/hentai?year=' + anio + '&page=1'

        itemlist.append(item.clone( action = 'list_all', url = url, title = title, text_color='orange' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="mt-4 pt-4 border-t border-white/10">(.*?)<div class="flex justify-center">')

    if not bloque: bloque = scrapertools.find_single_match(data, '<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 mb-8">(.*?)<div class="flex justify-center">')

    matches = re.compile('<a href="(.*?)".*?<script src=".*?src="(.*?)".*?alt="(.*?)"', re.DOTALL).findall(bloque)

    for url, thumb, title in matches:
        title = title.strip()

        url = host[:-1] + url

        itemlist.append(item.clone( action = 'episodios', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, 'click="nextPage(.*?)"')

        if next_page:
            ant_page = ''
            num_page = ''

            if '?page=' in item.url:
                ant_page = scrapertools.find_single_match(item.url, '(.*?)page=')
                ant_page = ant_page.replace('?', '').strip()

                num_page =scrapertools.find_single_match(item.url, 'page=(.*?)$')

            elif'&page=' in item.url:
                ant_page = scrapertools.find_single_match(item.url, '(.*?)&page=')

                num_page = scrapertools.find_single_match(item.url, '&page=(.*?)$')

            if ant_page:
                next_page = ''

                try:
                   nro_page = int(num_page)
                   nro_page = (nro_page + 1)

                   num_page = str(nro_page)
                except:
                   pass

                if '?page=' in item.url:
                    next_page = ant_page + '?page=' + str(num_page)

                elif'&page=' in item.url:
                    next_page = ant_page + '&page=' + str(num_page)

                if next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('"episodeNumber":.*?"name":.*?"(.*?)".*?"url":.*?"(.*?)"', re.DOTALL).findall(data)

    for title, url in matches:
        title = title.strip()

        epis = scrapertools.find_single_match(title, 'Episodio (.*?)$')
        if ' / ' in epis: epis = epis.split(" / ")[0]

        if not epis: epis = 1

        titulo = title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        titulo = titulo.replace('Tráiler', '[COLOR goldenrod]Epis.[/COLOR]').replace('tráiler', '[COLOR goldenrod]Epis.[/COLOR]')

        title = titulo + ' ' + item.title

        SerieName = item.contentTitle.strip()

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title,
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason = 1, contentEpisodeNumber=epis,
                                    contentExtra='adults' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    # ~ Online
    matches1 = re.compile('<iframe.*?src="(.*?)"', re.DOTALL).findall(data)

    # ~ Descargas
    bloque = scrapertools.find_single_match(data, '<table(.*?)</table>')

    matches2 = re.compile('<a href="(.*?)"', re.DOTALL).findall(bloque)

    matches = matches1 + matches2

    for url in matches:
        ses += 1

        if '/usersdrive.' in url: continue

        if url:
            if url.startswith('//'): url = 'https:' + url

            servidor = servertools.get_server_from_url(url)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            if not servidor == 'directo':
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = 'Vo', other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = host + 'hentai?search=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
