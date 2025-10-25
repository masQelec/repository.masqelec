# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ Las series no se tratan pq solo hay 17

host = 'https://www.tubeonline.net/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'pelicula/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    if config.get_setting('mnu_adultos', default=True):
        itemlist.append(item.clone( title = 'Adultos', action = 'list_all', url = host + 'categoria/adultos-18/', group = '+18', search_type = 'movie', text_color = 'orange' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'idioma/castellano/', lang='Esp', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'idioma/latino/', lang='Lat', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Subtituladas', action = 'list_all', url = host + 'idioma/subtitulado/', lang='Vos', search_type = 'movie', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if not config.get_setting('mnu_adultos', default=True):
            if title == 'Peliculas Porno +18': continue

        if title == 'News': continue

        group = ''

        if title == 'Peliculas Porno +18': group = '+18'

        title = title.replace('&amp;', '&')

        title = title.capitalize()

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, group = group, text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        url = host + 'fecha-estreno/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if item.group == '+18':
        if not config.get_setting('ses_pin'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

            config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<h1>(.*?)>Pelis y Series Online Gratis')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        if '/serie/' in url: continue

        title = title.replace('&#8217;s', "'s").replace('&#8211;', '')

        title = title.replace('Ver ', '').replace(' online', '')

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        langs = []
        if '/idioma/castellano/' in match: langs.append('Esp')
        if '/idioma/latino/' in match: langs.append('Lat')
        if '/idioma/subtitulado/' in match: langs.append('Vose')

        contentExtra = ''
        if item.group == '+18': contentExtra = 'adults'

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, languages=', '.join(langs),
                                    contentType = 'movie', contentTitle = title, contentExtra = contentExtra, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<span class="current">.*?href="(.*?)".*?>Pelis y Series Online')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if item.group == '+18':
        if not config.get_setting('ses_pin'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

            config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    idiomas = scrapertools.find_multiple_matches(data, '<ul id="container(.*?)</ul>')

    ses = 0

    for idioma in idiomas:
        matches = scrapertools.find_multiple_matches(idioma, '<li data-url="(.*?)"')

        for d_url in matches:
            ses += 1

            if '11"' in idioma: lang = 'Lat'
            elif '22"' in idioma: lang = 'Esp'
            elif '33"' in idioma: lang = 'Vose'
            else: lang = '?'

            itemlist.append(Item( channel = item.channel, action = 'play', server = '', url = item.url, d_url = d_url, language = lang ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    headers = {'Referer': item.url}

    post = {'nombre': item.d_url}

    data = do_downloadpage(host + 'wp-content/themes/dooplayorig123/inc/encriptar.php', post = post, headers = headers)

    url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)".*?</iframe>')

    if url:
        if '/powvideo.' in url:
            return 'Powvideo [COLOR tan]No soportado[/COLOR]'
        elif '/streamplay.' in url:
            return 'Streamplay [COLOR tan]No soportado[/COLOR]'

        if '/ups2up.' in url: return itemlist
        elif '/goo.' in url: return itemlist
        elif '/strmbolt.' in url: return itemlist

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Resultados encontrados(.*?)>Pelis y Series Online Gratis')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        if '/serie/' in url: continue

        title = title.replace('&#8217;s', "'s").replace('&#8211;', '')

        title = title.replace('Ver ', '').replace(' online', '')

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>')

        if not year: year = '-'
        else:
           title = title.replace('(' + year + ')', '').strip()

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<span class="current">.*?' + "href='(.*?)'.*?>Pelis y Series Online")

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_search', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + '?s=' + texto.replace(" ", "+")
       return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

