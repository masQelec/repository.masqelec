# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.pelistv.top/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://www.pelispedia.ws/', 'https://ww7.pelispedia.ws/', 'https://www.gnula4.cc/']


domain = config.get_setting('dominio', 'pelispediaws', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'pelispediaws')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'pelispediaws')
    else: host = domain


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    if '/release/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'pelispediaws', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_pelispediaws', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='pelispediaws', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_pelispediaws', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'ver-pelicula/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'ver-pelicula/')

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    for url, title in matches:
        title = title.replace('&amp;', '&')

        itemlist.append(item.clone( action='list_all', title=title, url=url, text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1938, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action='list_all', page = 1, text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, 'Añadido recientemente(.*?)<div class="copy">')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        title = scrapertools.find_single_match(article, ' alt="(.*?)"').strip()

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, '<img src="([^"]+)"')

        lngs = []
        langs = scrapertools.find_multiple_matches(article, '<img title="(.*?)"')
        if not langs: langs = scrapertools.find_multiple_matches(article, '/flags/(.*?).png')

        for lang in langs:
            lng = ''

            if lang == 'Español' or lang == 'es': lng = 'Esp'
            if lang == 'Latino' or lang == 'mx': lng = 'Lat'
            if lang == 'Subtitulado': lng = 'Vose'
            if lang == 'Ingles' or lang == 'en': lng = 'Voi'

            if lng:
               if not lng in str(lngs):
                   if lng == 'Voi': lng = 'Vo'
                   lngs.append(lng)

        year = scrapertools.find_single_match(article, '</h3>.*?<span>.*?,(.*?)</span>').strip()
        if not year: year = scrapertools.find_single_match(article, '<span class="year">(.*?)</span>')

        year = year.strip()

        if not year: year = '-'
        else:
           if '(' + year + ')' in title: title = title.replace('(' + year + ')', '').strip()

        title = title.replace('&#8211;', '').replace('&#8217;', '')

        titulo = title

        if "|" in titulo: titulo = titulo.split("|")[0]

        plot = scrapertools.find_single_match(article, '<div class="texto">(.*?)</div>')
        if not plot: plot = scrapertools.find_single_match(article, '<div class="contenido"><p>(.*?)</p>')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, languages = ', '.join(lngs),
                                    contentType = 'movie', contentTitle = titulo, infoLabels = {'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_url = scrapertools.find_single_match(data, '<div class="pagination">.*?<span class="current">.*?' + "<a href='(.*?)'")

            if next_url:
               if '/page/' in next_url:
                   itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, "<tr id='link-'.*?<a href='(.*?)'.*?<strong class='quality'>(.*?)</strong>.*?/flags/(.*?).png")

    ses = 0

    for url, qlty, lang in matches:
        ses += 1

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue

        elif '.mystream.' in url: continue
        elif '/ul.' in url: continue

        if lang == 'es': lang = 'Esp'
        elif lang == 'la': lang = 'Lat'
        elif lang == 'mx': lang = 'Lat'
        elif lang == 'en': lang = 'Vo'
        elif lang == 'jp': lang = 'Vose'
        else: lang = '?'

        servidor = servertools.get_server_from_url(url, disabled_servers=True)

        if servidor is None: continue

        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        url = servertools.normalize_url(servidor, url)

        itemlist.append(Item(channel = item.channel, action = 'play', title = '', server = servidor, url = url, language = lang, quality = qlty ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
