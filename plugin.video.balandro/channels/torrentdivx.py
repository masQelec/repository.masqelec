# -*- coding: utf-8 -*-

import re

from platformcode import logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://www.torrentdivx.net/'


def item_configurar_proxies(item):
    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    url = url.replace('/www.torrentdivx.com/', '/www.torrentdivx.net/')

    # ~ data = httptools.downloadpage(url, post=post, headers=headers).data
    data = httptools.downloadpage_proxy('torrentdivx', url, post=post, headers=headers).data

    if '<title>You are being redirected...</title>' in data:
        try:
            from lib import balandroresolver
            ck_name, ck_value = balandroresolver.get_sucuri_cookie(data)
            if ck_name and ck_value:
                httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])
                # ~ data = httptools.downloadpage(url, post=post, headers=headers).data
                data = httptools.downloadpage_proxy('torrentdivx', url, post=post, headers=headers).data
        except:
            pass

    return data


def mainlist(item):
    return mainlist_pelis(item)

    # ~  las series con recaptcha

    # ~ logger.info()
    # ~ itemlist = []

    # ~ itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    # ~ itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' )) # de momento se quitan por hidenn captacha

    # ~ itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    # ~ itemlist.append(item_configurar_proxies(item))
    # ~ return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'tag/estreno/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    itemlist.append(item_configurar_proxies(item))
    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Catálogo', action='list_all', url= host + 'tvshows/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    itemlist.append(item_configurar_proxies(item))
    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Castellano', action='list_all', url=host + 'tag/castellano/' ))
    itemlist.append(item.clone( title='Latino', action='list_all', url=host + 'tag/latino/' ))
    itemlist.append(item.clone( title='Subtitulado', action='list_all', url=host + 'tag/subtitulado/' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='En HdRip', action='list_all', url=host + 'tag/hdrip/', search_type = 'movie' ))
    itemlist.append(item.clone( title='En 720p', action='list_all', url=host + 'tag/720p/', search_type = 'movie' ))
    itemlist.append(item.clone( title='En 1080p', action='list_all', url=host + 'tag/1080p/', search_type = 'movie' ))
    itemlist.append(item.clone( title='En 4K', action='list_all', url=host + 'tag/4k/', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, 'Generos</a>\s*<ul class="sub-menu">(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)"[^>]*>([^<]+)')
    for url, title in matches:
        title = title[0].upper() + title[1:]
        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    itemlist.append(item.clone ( action = 'list_all', title = 'Bélica', url = host + 'genre/belica/' ))

    return sorted(itemlist, key=lambda it: it.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1938, -1):
        itemlist.append(item.clone( title=str(x), url= host + 'release/' + str(x) + '/', action='list_all' ))

    return itemlist


def list_all(item): 
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Añadido recientemente<(.*?)>Top IMDB<')
    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)')
        title = scrapertools.find_single_match(article, ' alt="([^"]+)')
        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        if not thumb: thumb = scrapertools.find_single_match(article, '<img data-src="(.*?)"')

        year = scrapertools.find_single_match(article, '<span>(\d{4})</span>')
        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'

        plot = scrapertools.find_single_match(article, '<div class="texto">(.*?)</div>')

        tipo = 'tvshow' if '/tvshows/' in url else 'movie'

        if tipo == 'movie':
            qlty = scrapertools.find_single_match(article, '<span class="quality">([^<]+)')

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, '<span class="current">.*?<a href="([^"]+)"')
    if next_page:
       itemlist.append(item.clone (url = next_page, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile("domain=utorrent.com.*?Temporada (\d+)", re.DOTALL).findall(data)

    for numtempo in matches:
        title = 'Temporada ' + numtempo

        itemlist.append(item.clone( action = 'findvideos', title = title, contentType = 'season', contentSeason = numtempo, contentEpisodeNumber = numtempo))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def puntuar_calidad(txt):
    txt = txt.replace(' ', '').replace('-', '').lower()

    orden = ['cam',
          'ts',
          'webdl',
          'webrip',
          'bdscr',
          'hdtv',
          'hc720p',
          'bdrip',
          'dvdrip',
          'hdrip',
          '720p',
          'hd720p',
          '1080p',
          'hd1080p',
          'hd2160p',
          '2160p',
          '4k']

    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Castellano':'Esp', 'Latino':'Lat', 'V.O. Subtitulado':'Vose', 'Version Original':'VO',
                'Version Original +Sub': 'VOS', 'Latino - Varios': 'Varios'}

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div class="box_links">(.*?)</table>')

    matches = scrapertools.find_multiple_matches(bloque, '<tr(.*?)</tr>')
    for enlace in matches:
        if '<th' in enlace or 'torrent' not in enlace: continue
        if "id='link-fake'" in enlace: continue

        url = scrapertools.find_single_match(enlace, " href='([^']+)")
        if not url: continue

        tds = scrapertools.find_multiple_matches(enlace, '<td>(.*?)</td>')
        qlty = scrapertools.find_single_match(tds[1], "<strong class='quality'>([^<]+)")
        lang = tds[2]
        othr = tds[3] if tds[3] != '----' else ''

        itemlist.append(Item( channel = item.channel, action = 'play', server = 'torrent', title = '', url = url,
                              language = IDIOMAS.get(lang,lang), quality = qlty, quality_num = puntuar_calidad(qlty), other = othr ))

    if len(itemlist) == 0:
        matches = scrapertools.find_multiple_matches(data, ' href="(magnet[^"]+)')
        for url in matches:
            itemlist.append(Item( channel = item.channel, action = 'play', server = 'torrent', title = '', url = url ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith(host) and '/links/' in item.url:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<a id="link" rel="nofollow" href="([^"]+)')

        if ('/www.pastexts.com/') in url or '/tmearn.com/' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        if url.endswith('.torrent'):
            import os
            from platformcode import config

            data = do_downloadpage(url)
            file_local = os.path.join(config.get_data_path(), "temp.torrent")
            with open(file_local, 'wb') as f: f.write(data); f.close()

            itemlist.append(item.clone( url = file_local, server = 'torrent' ))
            return itemlist

        if url:
            itemlist.append(item.clone(url = url))

    else:
        itemlist.append(item.clone())

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1>Resultados(.*?)>Top IMDB<')
    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, ' alt="([^"]+)"')
        if not url or not title: continue

        year = scrapertools.find_single_match(article, '<span class="year">(\d+)</span>')
        if not year: year = scrapertools.find_single_match(article, '<span>(\d{4})</span>')
        if not year: year = scrapertools.find_single_match(title, '\((\d{4})\)')
        plot = scrapertools.htmlclean(scrapertools.find_single_match(article, '<p>(.*?)</p>'))

        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'

        title_clean = re.sub('\([^\)]+\)', '', title).strip()

        tipo = 'tvshow' if '/tvshows/' in url else 'movie'
        if tipo == 'tvshow':
           continue

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, 
                                        contentType='movie', contentTitle=title_clean, infoLabels={'year': year, 'plot': plot} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title_clean, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, '<span class="current">.*?<a href="([^"]+)"')
    if next_page:
       itemlist.append(item.clone (url = next_page, title = '>> Página siguiente', action = 'list_search', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
