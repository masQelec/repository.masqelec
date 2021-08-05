# -*- coding: utf-8 -*-

import re

from platformcode import logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://pelis24.in/'


# ~ def item_configurar_proxies(item):
    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    # ~ return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

# ~ def configurar_proxies(item):
    # ~ from core import proxytools
    # ~ return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/release/' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    # ~ data = httptools.downloadpage_proxy('pelis24', url, post=post, headers=headers, raise_weberror=raise_weberror).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    # itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    # itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    # itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    # ~ itemlist.append(item_configurar_proxies(item))

    return mainlist_pelis(item)

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Recomendadas (al azar)', action = 'list_all', url = host + 'movies/', group = 'azar', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    # ~ itemlist.append(item_configurar_proxies(item))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'tvshows/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'pelis24/?get=tvshows', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'plataformas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    # ~ itemlist.append(item_configurar_proxies(item))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url = host + 'movies/'

    data = do_downloadpage(url)

    matches = scrapertools.find_multiple_matches(data, '<li class="cat-item cat-item-\d+"><a href="([^"]+)">([^<]+)')

    for url, title in matches:
        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1922, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title=str(x), url= url, action='list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)>Recomendamos<')

    if item.group == 'azar':
         bloque = scrapertools.find_single_match(data, '>Recomendamos<(.*?)>Categorias<')

    matches = re.compile('(?s)<article class="post dfx fcl movies">(.*?)</article>').findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, 'href="([^"]+)"')

        tipo = 'tvshow' if '/tvshows/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        title = scrapertools.find_single_match(article, '<h2[^>]+>([^<]+)')
        thumb = scrapertools.find_single_match(article, '<img.*?src="([^"]+)"\Wclass')
        qlty = scrapertools.find_single_match(article, '<span class="Qlty">([^<]+)')

        langs = []
        if 'Spain.png' in article: langs.append('Esp')
        if 'Mexico.png' in article: langs.append('Lat')

        if not langs:
            otros = scrapertools.find_single_match(article, 'mini_icon_(.*?).png').capitalize()
            langs.append(otros)

        if '/tvshows/' in url:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, qualities=qlty, languages=', '.join(langs),
                                        fmt_sufijo=sufijo, contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': '-'} ))
        else:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title = title, thumbnail = thumb, qualities=qlty, languages=', '.join(langs),
                                        fmt_sufijo=sufijo, contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if not item.group == 'azar':
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">SIGUIENTE')
        if next_page:
            itemlist.append(item.clone( title='>> Página siguiente', url = next_page, action='list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, "<div id='seasons'>(.*?)<h2>")

    matches = re.compile("<span class='se-t.*?>(.*?)</span>", re.DOTALL).findall(bloque)

    for season in matches:
        title = 'Temporada ' + season

        url = item.url

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.url = url
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = season
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = url, contentType = 'season', contentSeason = season, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    season = item.contentSeason

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, "<div id='seasons'>(.*?)<h2>")

    blk_temp = scrapertools.find_single_match(bloque, "<span class='se-t.*?>" + str(season) + "</span>(.*?)</ul></div></div></div></div></div>")

    matches = re.compile(".*?<li class='mark-(.*?)</div></li>", re.DOTALL).findall(blk_temp)

    for datos in matches[item.page * perpage:]:
        thumb = scrapertools.find_single_match(datos, " src.*?'(.*?)'")
        url = scrapertools.find_single_match(datos, " href.*?'(.*?)'")
        title = scrapertools.find_single_match(datos, " href.*?'>(.*?)</a>")

        epis = scrapertools.find_single_match(datos, "<div class='numerando'>(.*?)</div>")
        epis = epis.split('-')[1].strip()

        titulo = season + 'x' + epis + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def puntuar_calidad(txt):
    txt = txt.replace(' ', '').replace('-', '').lower()
    orden = ['tsscreener',  'webscreener', 'dvdrip', 'hdrip', 'webdl720p', 'hd720p', 'hd1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {
      'castellano': 'Esp',
      'español': 'Esp',
      'spain': 'Esp',
      'mexico': 'Lat',
      'latino': 'Lat',
      'subtitulado': 'Vose',
      'sub español': 'Vose',
      'sub': 'Vose',
      'ingles': 'Vos'
      }

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<div id="(options-\d+)"[^<]+\s*<iframe[^"]+"([^"]+)')

    for option, url in matches:
        if 'hqq' in url or 'facebook' in url: continue

        languages = scrapertools.find_single_match(data, '<li><a class="btn.*?href="#%s".*?server">([^<]+)</span' % (option))
        lang = re.sub('^[^-]+-', '', languages) if '-' in languages else ''
        lang = IDIOMAS.get(lang.lower(), lang)

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor != 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', url=url, server = servidor, title = '', language = lang ))

    matches = scrapertools.find_multiple_matches(data, '(?s)<td><span class="num">#\d+</span>\s*([A-Za-z\d+]+)</td>\s*<td>([^<]+)</td>.*?href="([^"]+)')

    for servidor, lang, url in matches:
        lang = IDIOMAS.get(lang.lower(), lang)
        url = url.replace('&#038;', '&')

        itemlist.append(Item( channel = item.channel, action = 'play', url=url, server = servidor, title = '', language = lang ))

    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
