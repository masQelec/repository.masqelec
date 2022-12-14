# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

from lib import decrypters


host = 'https://cinetorrent.eu/'


def do_downloadpage(url, post=None, raise_weberror=True):
    if '/years/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data,'>Genero<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque,'<a href="(.*?)".*?>(.*?)</a>')

    for url, tit in matches:
        if not url or not tit: continue

        tit = tit.replace('&amp;', '&').capitalize()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    if itemlist:
        itemlist.append(item.clone( action = 'list_all', title = 'Documental', url = host + 'category/documental/' ))
        itemlist.append(item.clone( action = 'list_all', title = 'Histoia', url = host + 'category/historia/' ))
        itemlist.append(item.clone( action = 'list_all', title = 'Western', url = host + 'category/western/' ))

    return sorted(itemlist, key=lambda it: it.title)


def calidades(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='En 4K 2160p', url = host + 'quality/4k-2160p/', action='list_all' ))
    itemlist.append(item.clone( title='En 1080 Dual', url = host + 'quality/1080p-dual/', action='list_all' ))
    itemlist.append(item.clone( title='En 1080', url = host + 'quality/1080p/', action='list_all' ))
    itemlist.append(item.clone( title='En BluRay Scr', url = host + 'quality/br-scr/', action='list_all' ))
    itemlist.append(item.clone( title='En Ts Sreener', url = host + 'quality/ts-scr/', action='list_all' ))
    itemlist.append(item.clone( title='En Cam', url = host + 'quality/cam/', action='list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1969, -1):
        url = host + 'years/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div class="col-6 col-sm-4 col-lg-3 col-xl-2">(.*?)</div></div>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="card__title">.*?">(.*?)</a>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')
        qlty = scrapertools.find_single_match(match, '<li>(.*?)</li>').strip()

        tipo = 'tvshow' if '/series/' in url else 'movie'

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page_link = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)')

        if next_page_link:
            itemlist.append(item.clone( title='Siguientes ...', action='list_all', url=next_page_link, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('data-target="#collapse-.*?<span>(.*?)</span>', re.DOTALL).findall(data)

    for title in matches:
        numtempo = title.replace('Temporada ', '').strip()

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.title = title
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = numtempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<span>' + str(item.title) + '</span>(.*?)</tbody>')

    matches = re.compile('data-season="(.*?)".*?data-serie="(.*?)".*?href="(.*?)"', re.DOTALL).findall(bloque)

    for season, episode, url in matches[item.page * perpage:]:
        if item.contentSeason:
            if not str(item.contentSeason) == season: continue

        titulo = '%sx%s %s' % (season, episode, item.contentSerieName)

        itemlist.append(item.clone( action='findvideos', title = titulo, url = url,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = episode ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > (item.page + 1) * perpage:
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not item.url: return itemlist

    if '/short-link.one/' in item.url:
        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = item.url, server = 'directo', other = 'shortlink' ))

        return itemlist

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<tbody>(.*?)</tbody>')

    matches = re.compile('<tr>(.*?)</tr>', re.DOTALL).findall(bloque)

    ses = 0

    for match in matches:
        ses += 1

        url = scrapertools.find_single_match(match, ' href="([^"]+)')

        if url:
            qlty = scrapertools.find_single_match(match, '<td>(.*?)</td>')
            if '<b>Notice</b>' in qlty: qlty = ''

            lang = scrapertools.find_single_match(match, '</td>.*?<td>(.*?)</td>')
            if lang == 'Castellano': lang = 'Esp'
            elif lang == 'Latino': lang = 'Lat'
            elif lang == 'Subtitulado': lang = 'Vose'
            elif lang == 'Version Original': lang = 'VO'

            peso = scrapertools.find_single_match(match, '<td class="hide-on-mobile">.*?<td>(.*?)</td>')

            servidor = 'torrent'
            srv = ''

            if url.endswith(".torrent"): pass
            elif url.startswith('magnet:'): srv = 'magnet'
            else:
                servidor = 'directo'
                if '/short-link.one/' in url: srv = 'shortlink'
                elif '/acortalink.me/' in url: srv = 'acortalink'
                elif '/mega.' in url: srv = 'mega'
                else:
                    srv = servertools.get_server_from_url(url)
                    srv = servertools.corregir_servidor(srv)

            other = peso + ' ' + srv

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, quality = qlty,
                                  other = other ))

    if not itemlist:
       url = ''

       servidor = 'torrent'
       other = ''

       if item.url.endswith(".torrent"): url = item.url
       elif item.url.startswith('magnet:'):
          url = item.url
          other = 'magnet'
       else:
           servidor = 'directo'
           if '/acortalink.me/' in item.url:
              url = item.url
              other = 'acortalink'
           elif '/mega.' in item.url:
              url = item.url
              other = 'mega'
           else:
              other = servertools.get_server_from_url(item.url)
              other = servertools.corregir_servidor(other)

       if url:
           itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.server == 'torrent':
        itemlist.append(item.clone( url = item.url, server = 'torrent' ))
        return itemlist

    else:
        if 'magnet' in item.other:
            itemlist.append(item.clone( url = item.url, server = 'torrent' ))
            return itemlist

        if 'mega' in item.other:
            try:
                url_id = item_url.split('#')[1]
                file_id = url_id.split('!')[1]
            except:
                file_id = ''

            if file_id:
                get = ''
                post = {'a': 'g', 'g': 1, 'p': file_id}

                if '/#F!' in page_url:
                    get = '&n=' + file_id
                    post = {'a': 'f', 'c': 1, 'r': 0}
 
                import random
                nro = random.randint(0, 0xFFFFFFFF)

                from core import jsontools
                api = 'https://g.api.mega.co.nz/cs?id=%d%s' % (nro, get)
                resp = httptools.downloadpage(api, post=jsontools.dump([post]), headers={'Referer': 'https://mega.nz/'})

        servidor = servertools.get_server_from_url(item.url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, item.url)

        if servidor and servidor != 'directo':
            itemlist.append(item.clone( url = url, server = servidor ))
            return itemlist

        if servidor == 'directo':
            host_torrent = host[:-1]
            url_base64 = decrypters.decode_url_base64(url, host_torrent)

            if url_base64.startswith('magnet:'):
                itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

            elif url_base64.endswith(".torrent"):
                itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'buscar/?buscar=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
