# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://fullseriehd.com/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '&years[]=' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'category/estrenos/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Novedades', action = 'list_all', url = host + 'category/estrenos/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Amazon', action = 'list_all', url = host + 'tag/amazon/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Fox', action = 'list_all', url = host + 'tag/fox/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host + 'tag/netflix/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Telenovela', action = 'list_all', url = host + 'tag/telenovela/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, 'id="categories(.*?)</span>')

    matches = re.compile('<a href="([^"]+)">([^<]+)').findall(bloque)

    for url, title in matches:
        if title == 'Estrenos': continue
        elif title == 'Proximamente': continue

        if item.search_type == 'movie':
            if title == 'Reality': continue
            elif title == 'Soap': continue
            elif title == 'Talk': continue
        else:
            if title == 'Película de TV': continue

        itemlist.append(item.clone( title = title, action = 'list_all', url = url ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie':
        post_type = 1
    else:
        post_type = 2

    for x in range(current_year, 1999, -1):
        year = str(x)
        url = '%s?s=trfilter&trfilter=1&tr_post_type=%s&years[]=%s' % (host, post_type, year)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)>Mas Vistas<')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')
        if not thumb:
            thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="Year">(.*?)</span>')
        if not year: year = '-'

        qlty = scrapertools.find_single_match(match, '<span class="Qlty">(.*?)</span>')

        plot = scrapertools.find_single_match(match, '<p>(.*?)</p>')

        if '/pelicula/' in url:
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, qualities = qlty, fmt_sufijo = sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))
        else:
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo = sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<div class="wp-pagenavi">.*?class="page-numbers current">.*?href="(.*?)"')

        if next_url:
            if '/page/' in next_url:
                itemlist.append(item.clone( title = '>> Página siguiente', url = next_url, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile('data-tab="(.*?)"', re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = tempo, page = 0 ))

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

    bloque = scrapertools.find_single_match(data, 'data-tab="' + str(item.contentSeason) + ".*?</span>(.*?)</div></div>")

    matches = re.compile('<span class="Num">(.*?)</span>.*?<a href="(.*?)".*?src="(.*?)"', re.DOTALL).findall(bloque)

    for epis, url, thumb in matches[item.page * perpage:]:
        title = 'Episodio ' + epis

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color = 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, 'id="Opt(.*?)">(.*?)</div>')

    ses = 0

    for opt, match in matches:
        ses += 1

        srv, lang, qlty = scrapertools.find_single_match(data, 'data-tplayernv="Opt' + opt + '"><span>(.*?)</span><span>(.*?)-(.*?)</span>')

        srv = srv.strip()
        lang = lang.strip()
        qlty = qlty.strip()

        if 'Latino' in lang:
            lang = 'Lat'
        elif 'Castellano' in lang:
            lang = 'Esp'
        elif 'Subtitulado' in lang:
            lang = 'Vose'
        else:
            lang = '?'

        if 'premium' in srv: srv = 'gvideo'

        other = srv.lower()

        if 'youtube' in other: continue
        elif 'waaw' in other: continue
        elif 'hqq' in other: continue
        elif 'netu' in other: continue

        url = scrapertools.find_single_match(match, 'data-.*?src="(.*?)"')
        if not url:
            match2 = match.replace('&quot;', "'")
            url = scrapertools.find_single_match(match2, "src='(.*?)'")

        if url:
            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                                  language = lang, quality = qlty, other = other.capitalize() ))

    # Descargar
    bloque = scrapertools.find_single_match(data, '<table>(.*?)</table>')

    matches = scrapertools.find_multiple_matches(bloque, '<span class="Num">(.*?)</td></tr>')

    for match in matches:
        ses += 1

        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        srv = scrapertools.find_single_match(match, '</noscript></noscript>(.*?)</span>').lower()

        if 'uptobox' in srv: pass
        elif 'mega' in srv: pass
        elif 'premium' in srv: pass
        else:
           continue

        lang = scrapertools.find_single_match(match, '</noscript></noscript></noscript></noscript>(.*?)</span>')
        if not lang:
            lang = scrapertools.find_single_match(match, '<td><span><imgalt="Imagen(.*?)"')

        if 'Latino' in lang:
            lang = 'Lat'
        elif 'Castellano' in lang:
            lang = 'Esp'
        elif 'Subtitulado' in lang:
            lang = 'Vose'
        else:
            lang = '?'

        qlty = scrapertools.find_single_match(match, '</noscript></noscript></noscript></noscript>.*?</span></td><td><span>(.*?)</span>')

        if 'premi' in srv: srv = 'gvideo'

        other = srv.replace('</noscript>', '').strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                              language = lang, quality = qlty, other = other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')
    item.url = item.url.replace('amp;#038;', '&').replace('#038;', '&').replace('amp;', '&')

    url = item.url

    if '/acortar24.xyz/' in item.url:
       url_b64 = scrapertools.find_single_match(item.url, 'l=(.*?)$')

       if url_b64:
           try:
              for x in range(7):
                  url_dec = base64.b64decode(url_b64).decode('utf-8')
                  url_b64 = url_dec
           except:
              pass

           url = url_b64

       if host in url:
           data = do_downloadpage(url, raise_weberror = False)

           url = scrapertools.find_single_match(data, '<h1 class=.*?<a href="(.*?)"')

           if not url:
               url = scrapertools.find_single_match(data.lower(), '<iframe.*?src="(.*?)"')
               if not url:
                   url = scrapertools.find_single_match(data, '<iframe id="myframe" data-src="(.*?)"')
                   if not url:
                       url = scrapertools.find_single_match(data, 'var video_url="(.*?)"')
                       if not url:
                           url = scrapertools.find_single_match(data, 'sources:.*?"src":.*?"(.*?)"')

    else:
       data = do_downloadpage(item.url, raise_weberror = False)

       url = scrapertools.find_single_match(data, '<h1 class=.*?<a href="(.*?)"')

       if not url:
           url = scrapertools.find_single_match(data.lower(), '<iframe.*?src="(.*?)"')
           if not url:
               url = scrapertools.find_single_match(data, '<iframe id="myframe" data-src="(.*?)"')
               if not url:
                   url = scrapertools.find_single_match(data, 'var video_url="(.*?)"')
                   if not url:
                       url = scrapertools.find_single_match(data, 'sources:.*?"src":.*?"(.*?)"')

    if url:
        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'
        elif '//www.facebook.com/' in url:
            return 'Archivo NO encontrado'
        elif url == 'about:blank':
            return 'El archivo ya no está disponible'

        if '/gdri.php' in url:
            url = scrapertools.find_single_match(url, 'v=([A-z0-9-_=]+)')
            url = 'https://drive.google.com/file/d/%s/preview' % url

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone(server = servidor, url = url))

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

