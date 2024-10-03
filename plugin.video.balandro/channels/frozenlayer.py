# -*- coding: utf-8 -*-

import re

from platformcode import logger, config, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.frozen-layer.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data

def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False: return

    titulo = 'dorama, anime, ova, manga ...'
    text_color = 'hotpink'

    if item.extra == 'anime':
        titulo = 'anime, ova, manga ...'
        text_color = 'springgreen'
    elif item.extra == 'dorama':
        titulo = 'dorama ...'
        text_color = 'firebrick'

    itemlist.append(item.clone( title = '[B][COLOR yellow]Buscar [/B][/COLOR]' + titulo, action = 'search', search_type = 'tvshow', text_color = text_color ))

    itemlist.append(item.clone( title = 'Catálogo general', action = 'list_all', url = host + '/descargas/detallada/bittorrent', search_type = 'tvshow' ))

    if item.extra == 'all' or item.extra == 'torrents' or item.extra == 'dorama' or item.extra == 'groups':
        itemlist.append(item.clone( title = '[B]Doramas:[/B]', folder=False, text_color='moccasin' ))
        itemlist.append(item.clone( title = ' - Episodios', action = 'list_all', url = host + '/descargas/detallada/bittorrent/dorama', search_type = 'tvshow' ))

    if not config.get_setting('descartar_anime', default=False):
        if item.extra == 'all' or item.extra == 'torrents' or item.extra == 'anime' or item.extra == 'groups':
            itemlist.append(item.clone( title = '[B]Animes:[/B]', folder=False, text_color='moccasin' ))

            itemlist.append(item.clone( title = ' - Catálogo', action = 'list_lst', url = host + '/buscar/anime/tv?&categoria=tv&detallada=true', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = ' - [COLOR cyan]Estrenos[/COLOR]', action = 'list_lst', url = host + '/animes/lista?sort=anio&direction=desc&detallada=true', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = ' - Más valorados', action = 'list_lst', url = host + '/animes/lista?sort=rating&direction=desc&detallada=true', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = ' - [COLOR deepskyblue]Películas[/COLOR]', action = 'list_lst', url = host + '/buscar/anime/pelicula?&categoria=pelicula&detallada=true', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = ' - Episodios', action = 'list_all', url = host + '/descargas/detallada/bittorrent/anime', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = ' - Por categoría', action = 'categorias', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = ' - Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = '[B]Ovas:[/B]', folder=False, text_color='moccasin' ))
            itemlist.append(item.clone( title = ' - Catálogo', action = 'list_lst', url = host + '/buscar/anime/ova?&categoria=ova&detallada=true', search_type = 'tvshow' ))
            itemlist.append(item.clone( title = ' - Episodios', action = 'list_all', url = host + '/descargas/detallada/bittorrent/anime-OVA', search_type = 'tvshow' ))

            itemlist.append(item.clone( title = '[B]Mangas:[/B]', folder=False, text_color='moccasin' ))
            itemlist.append(item.clone( title = ' - Episodios', action = 'list_all', url = host + '/descargas/detallada/bittorrent/manga', search_type = 'tvshow' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + '/animes')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<h2>Categorias(.*?)</div>')

    matches = re.compile('<a href="(.*?)".*?">(.*?)</a>').findall(bloque)

    for url, title in matches:
        if config.get_setting('descartar_xxx', default=False):
            if title == 'Adulto': continue
            elif title == 'Erótico': continue
            elif title == 'Incesto': continue

        url = host + url + '?&detallada=true'

        itemlist.append(item.clone( title = title.capitalize(), action = 'list_lst', url = url, text_color = 'springgreen' ))

    return sorted(itemlist, key=lambda x: x.title)


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0':
        url = host + '/animes/lista/letra/' + letra + '?&detallada=true'

        itemlist.append(item.clone( title = letra, action = 'list_lst', url = url, text_color = 'springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, "<h1 class='descarga_titulo'>(.*?)</div></div>")

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<a href=".*?">(.*?)</a>').strip()

        if title.startswith("["):
           if '] -' in title: title = scrapertools.find_single_match(title, ' -(.*?)$').strip()

        thumb = scrapertools.find_single_match(match, "<div class='twocol'>.*?" + '<a href="(.*?)"')

        title_ser = title.strip()

        if ' Season Episodio' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) Season Episodio')
        elif ' Episodio' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) Episodio')
        elif ' Capitulo' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) Capitulo')
        elif ' Cap' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) Cap')
        elif ' Tomo' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) Tomo')
        elif ' OVA' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) OVA')
        elif ' COMPLETA' in title_ser: title_ser = scrapertools.find_single_match(title, '(.*?) COMPLETA')

        title_ser = title_ser.strip()

        if 'Película' in title_ser: title_ser = title_ser.split("Película")[0]
        if 'Episodio' in title_ser: title_ser = title_ser.split("Episodio")[0]
        if 'Season' in title_ser: title_ser = title_ser.split("Season")[0]
        if 'Pack' in title_ser: title_ser = title_ser.split("Pack")[0]

        SerieName = title_ser.strip()

        url_tor = scrapertools.find_single_match(match, "<div id='descargar_torrent'>.*?href='(.*?)'")

        title = title.replace('Episodio', '[COLOR goldenrod]Episodio[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Capitulo[/COLOR]').replace(' Cap', '[COLOR goldenrod] Cap[/COLOR]')

        if '(Pelicula)' in title_ser or '(pelicula)' in title_ser:
            PeliName = title_ser.replace('(Pelicula)', '').replace('(pelicula)', '').strip()
            title = title.replace('(Pelicula)', '[COLOR deepskyblue]Película[/COLOR]').replace('(pelicula)', '[COLOR deepskyblue]Película[/COLOR]')

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, contentType = 'movie', contentTitle = PeliName, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, url_tor = url_tor,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if "<span class='next'>" in data:
            next_page = scrapertools.find_single_match(data, "<span class='next'>" + '.*?href="(.*?)"')

            if next_page:
                if 'page=' in next_page:
                    next_page = host + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def list_lst(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, "id='descarga_anime_row'>(.*?)</span></div>")

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if url:
            if url == '/buscar/descargas/tv': continue
            elif url == '/buscar/descargas/pelicula': continue

            url = url + '/descargas'

            title = scrapertools.find_single_match(match, 'src=".*?<a href=".*?">(.*?)</a>').strip()

            thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

            title_ser = title.strip()

            if 'Película' in title_ser: title_ser = title_ser.split("Película")[0]
            if 'Episodio' in title_ser: title_ser = title_ser.split("Episodio")[0]
            if 'Season' in title_ser: title_ser = title_ser.split("Season")[0]
            if 'Pack' in title_ser: title_ser = title_ser.split("Pack")[0]
            if '(TV)' in title_ser: title_ser = title_ser.split("(TV)")[0]
            if 'TV' in title_ser: title_ser = title_ser.split("TV")[0]

            SerieName = title_ser.strip()

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, contentType = 'tvshow', contentSerieName = SerieName, infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if "<span class='next'>" in data:
            next_page = scrapertools.find_single_match(data, "<span class='next'>" + '.*?href="(.*?)"')

            if next_page:
                if 'page=' in next_page:
                    next_page = host + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_lst', url = next_page, text_color='coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, "<td class='tit'>(.*?)<td class='detalles'>")

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'class="detalles_link">(.*?)</a>').strip()

        try:
            episode = scrapertools.find_single_match(title, "Episodio.*?(\d+)")
        except:
            episode = 0

        title = title.replace('Pelicula', '[COLOR deepskyblue]Pelicula[/COLOR]').replace('Película', '[COLOR deepskyblue]Película[/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = title, contentType = 'episode', contentSeason = 1, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if "<span class='next'>" in data:
            next_page = scrapertools.find_single_match(data, "<span class='next'>" + '.*?href="(.*?)"')

            if next_page:
                if 'page=' in next_page:
                    next_page = host + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'episodios', url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, 'Seeds:.*?"stats.*?">(\d+)<.*?Peers:.*?"stats.*?">(\d+)<.*?descargar_torrent.*?href=\'(.*?)\'')

    if not matches:
        if item.url_tor:
            if item.url_tor.endswith('.torrent'): servidor = 'torrent'
            elif item.url_tor.startswith('magnet:?'): servidor = 'torrent'
            else: servidor = ''

            if servidor:
                url = item.url_tor

                itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = 'Vose' ))

                return itemlist

    ses = 0

    for seeds, peers, url in matches:
        ses += 1

        if url.endswith('.torrent'): servidor = 'torrent'
        elif url.startswith('magnet:?'): servidor = 'torrent'
        else:
           servidor = servertools.get_server_from_url(url)
           servidor = servertools.corregir_servidor(servidor)

           url = servertools.normalize_url(servidor, url)

           if servidor == 'directo': continue

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = 'Vose' ))


    match = scrapertools.find_single_match(data, 'Magnet Link:.*?<a href="(.*?)"')

    if match:
        if match.endswith('.torrent'): servidor = 'torrent'
        elif match.startswith('magnet:?'): servidor = 'torrent'
        else: servidor = ''

        match = match.replace('&amp;', '&')

        if not servidor == 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = match, server = servidor, language = 'Vose' ))

    if not itemlist:
        matches = scrapertools.find_multiple_matches(data, 'FlashVars.*?text=https.*?https(.*?)">')
        if not matches:
            matches = scrapertools.find_multiple_matches(data, 'tr class="enlaces">.*?">(.*?)</td>')

            if not matches:
               if 'FlashVars="text=' in data or 'tr class="enlaces">' in data: ses += 1

        if matches:
           for match in matches:
               ses += 1

               if not 'http' in match: url = 'https' + match
               else: url = match

               if url.endswith('.torrent'): servidor = 'torrent'
               elif url.startswith('magnet:?'): servidor = 'torrent'
               else:
                  servidor = servertools.get_server_from_url(url)
                  servidor = servertools.corregir_servidor(servidor)

                  url = servertools.normalize_url(servidor, url)

                  if servidor == 'directo': continue

               itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = 'Vose' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '/buscar/' + texto.replace(" ", "+") + '?&detallada=true'
        return list_lst(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
