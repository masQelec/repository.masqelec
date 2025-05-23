# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ las series no se tratan 29/8/24

host = 'https://bloghorror.com/'


def do_downloadpage(url, post=None, headers=None):
    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

    if '<h1>aaWAF is checking your access</h1>' in data:
        if not '/?s=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('BlogHorror', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

        timeout = config.get_setting('channels_repeat', default=30)

        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if '<h1>aaWAF is checking your access</h1>' in data:
            if not '/?s=' in url:
                platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection [COLOR yellowgreen]aaWAF[/B][/COLOR]')
            return ''

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/terror-3/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Asiáticas', action = 'list_all', url = host + 'category/asiatico1/', search_type = 'movie', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = {
        'accion': 'Acción',
        'animacion': 'Animación',
        'peliculas-de-terror-de-asesinos': 'Asesinos',
        'aventura': 'Aventura',
        'belico': 'Bélico',
        'ciencia-ficcion': 'Ciencia ficción',
        'comedia': 'Comedia',
        'deportes': 'Deportes',
        'documental': 'Documental',
        'drama': 'Drama',
        'romance': 'Romance',
        'suspenso': 'Suspense',
        'thriller': 'Thriller'
        }

    for opc in sorted(opciones):
        itemlist.append(item.clone( title = opciones[opc], url = host + 'category/' + opc + '/', action ='list_all', text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1959, -1):
        url = host + '?s=' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action='list_all', anio = str(x), text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)<div class="covernews-pagination">')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3 class="article-title article-title-1">.*?data-wpel-link="internal">(.*?)</a>').strip()

        if not url or not title: continue

        if 'peliculas' in title.lower() or 'películas' in title.lower(): continue
        elif 'cortos' in title.lower(): continue
        elif 'mejores' in title.lower(): continue

        if "serie" in url: continue

        thumb = scrapertools.find_single_match(match, 'data-background="(.*?)"')

        title = title.replace('&#038;', '&').replace('&#8211;', '').replace('&#8217;s', "'s")

        year = '-'

        if ' (' in title:
            year = title.split(' (')[1]
            year = year.replace(')', '').strip()
        elif ' [' in title:
            year = title.split(' [')[1]
            year = year.replace(']', '').strip()

        if not year == '-':
            if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
            elif ' [' in title: title = title.replace(' [' + year + ']', '').strip()

        if item.anio: year = item.anio

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                            contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="covernews-pagination">' in data:
            next_page = scrapertools.find_single_match(data, 'class="page-numbers current">.*?href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    lang = scrapertools.find_single_match(data, 'Audio</span>(.*?)<br')
    if not lang: lang = scrapertools.find_single_match(data, '>Audio:</span>(.*?)<br')
    if not lang: lang = scrapertools.find_single_match(data, '>Audio:</strong>(.*?)<br')
    if not lang: lang = scrapertools.find_single_match(data, 'Audio(.*?)<br')

    lang = lang.replace(':', '').strip()

    idioma = ''

    if lang == 'Ingles': lang = 'Ing'
    elif lang == 'Español': lang = 'Esp'
    elif lang == 'Latino': lang = 'Lat'
    else:
        idioma = lang
        lang = 'Vo'

    if 'FICHA TECNICA' in data:
        bloque = scrapertools.find_single_match(data, 'FICHA TECNICA(.*?)</div>')
        if not bloque or bloque == '</span>': bloque = scrapertools.find_single_match(data, 'FICHA TECNICA(.*?)</a></div>')
    else:
        bloque = scrapertools.find_single_match(data, 'DESCARGA DIRECTA(.*?)</div>')
        if not bloque or bloque == '</span>': bloque = scrapertools.find_single_match(data, 'DESCARGA DIRECTA(.*?)</a></div>')

    matches = re.compile('<br(.*?)<br.*?<a href="(.*?)"', re.DOTALL).findall(bloque)

    if not matches: matches = re.compile('Calidad</span>(.*?)<span.*?<a href="(.*?)"', re.DOTALL).findall(bloque)
    if not matches: matches = re.compile('>Calidad:(.*?)</span>.*?<a href="(.*?)"', re.DOTALL).findall(bloque)
    if not matches: matches = re.compile('Calidad</span>(.*?)</span>.*?<a href="(.*?)"', re.DOTALL).findall(bloque)

    if not matches: matches = re.compile('<em>(.*?)</em>.*?<a href="(.*?)"', re.DOTALL).findall(bloque)

    ses = 0

    for qlty, url in matches:
        if 'www.subdivx' in url: continue

        ses += 1

        if '</div>' in idioma: idioma = scrapertools.find_single_match(idioma, '(.*?)</div>').strip()

        qlty = qlty.replace(':', '').replace('/>', '').strip()
        qlty = qlty.replace('<em>', '').replace('</em>', '').replace('<i>', '').replace('</i>', '').strip()
        qlty = qlty.replace('</a>', '').replace('BlogHorror', '').strip()

        if 'Calidad' in qlty:
            qlty = scrapertools.find_single_match(qlty, 'Calidad.*?</span>(.*?)<span').strip()

            if '+' in qlty: qlty = scrapertools.find_single_match(qlty, '(.*?) +').strip()

        if '<span' in qlty: qlty = scrapertools.find_single_match(qlty, '(.*?)<span').strip()
        elif '<a href' in qlty: qlty = ''

        url = url.replace('&amp;', '&')

        other = idioma

        other = other.replace('de toda la vida', '').strip()

        if url.endswith('.torrent'): servidor = 'torrent'
        elif url.startswith('magnet:?'):
            servidor = 'torrent'
            if not idioma: other = 'Magnet'
        elif '/tinyurl.' in url:
            servidor = 'directo'
            other = 'mega'
        else:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

        lng = ''

        if idioma:
            if not other == 'Magnet' and not other == 'mega':
                lng = idioma.replace('<em>', '').strip()
                other = ''

        if servidor == 'directo':
            if other == 'mega':
                itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor,
                                      language = lang, quality = qlty, other = other, age = lng ))

        if not servidor == 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url,
                                  server = servidor, language = lang, quality = qlty, other = other, age = lng ))

    # ~ Otros
    matches = re.compile('<a href="(.*?)".*?data-wpel-link="external">(.*?)<', re.DOTALL).findall(bloque)

    for url, tipo in matches:
        ses += 1

        if '1fichier' in url: continue

        if tipo.lower() == 'subtitulos': continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        link_other = ''
        if servidor == 'various': link_other = servertools.corregir_other(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = link_other ))

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
