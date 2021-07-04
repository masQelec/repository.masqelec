# -*- coding: utf-8 -*-

import re

from platformcode import logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools, jsontools


host = 'https://www.pelis24.in/'


# ~ def item_configurar_proxies(item):
    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    # ~ return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

# ~ def configurar_proxies(item):
    # ~ from core import proxytools
    # ~ return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data
    # ~ data = httptools.downloadpage_proxy('pelis24', url, post=post, headers=headers).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    # ~ itemlist.append(item_configurar_proxies(item))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'genre/estrenos/' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'pelis24/?get=movies', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'movie' ))

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


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'genre/castellano' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + '/genre/latino' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<div class="fixed-sidebar-blank">(.*?)</ul></nav></div><div class="dt_mainmeta">')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)"[^>]*>([^<]+)')

    for url, title in matches:
        if '/genre/estrenos/' in url: continue
        elif '/genre/castellano/' in url: continue
        elif '/genre/latino/' in url: continue

        if url.startswith('/'): url = host + url[1:]

        if '/genre/' not in url: url = url.replace(host, host + 'genre/')

        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title=str(x), url= url, action='list_all' ))

    return itemlist


def plataformas(item):
    logger.info()
    itemlist = []

    web_plataformas = [
	   ['ae', 'A&E'],
	   ['abc', 'ABC'],
	   ['adult-swim', 'Adult Swim'],
	   ['amazon', 'Amazon'],
	   ['amc', 'AMC'],
	   ['antena-3', 'Antena 3'],
	   ['axn', 'AXN'],
	   ['bbc-america', 'BBC America'],
	   ['bbc-one', 'BBC One'],
	   ['bbc-two', 'BBC Two'],
	   ['cbc-television', 'CBC Television'],
	   ['cbs', 'CBS'],
	   ['cbs-all-access', 'CBS All Access'],
	   ['channel-4', 'Channel 4'],
	   ['ctv', 'CTV'],
	   ['cuatro', 'Cuatro'],
	   ['disney-channel', 'Disney Channel'],
	   ['disney-xd', 'Disney XD'],
	   ['disney', 'Disney+'],
	   ['dmax', 'DMax'],
	   ['epix', 'Epix'],
	   ['fox', 'FOX'],
	   ['fox-espana', 'FOX España'],
	   ['freeform', 'Freeform'],
	   ['fx', 'FX'],
	   ['hbo', 'HBO'],
	   ['history', 'History'],
	   ['hulu', 'Hulu'],
	   ['itv', 'ITV'],
	   ['la-1', 'La 1'],
	   ['la-une', 'La Une'],
	   ['movistar', 'Movistar+'],
	   ['mtv', 'MTV'],
	   ['nbc', 'NBC'],
	   ['netflix', 'Netflix'],
	   ['rai-1', 'Rai 1'],
	   ['ruv', 'RÚV'],
	   ['showcase', 'Showcase'],
	   ['showtime', 'Showtime'],
	   ['sky-atlantic', 'Sky Atlantic'],
	   ['sky-one', 'Sky One'],
	   ['syfy', 'Syfy'],
	   ['starz', 'Starz'],
	   ['tbs', 'TBS'],
	   ['the-cw', 'The CW'],
	   ['the-wb', 'The WB'],
	   ['telecinco', 'Telecinco'],
	   ['telemundo', 'Telemundo'],
	   ['tnt', 'TNT'],
	   ['tv3', 'TV3'],
	   ['univision', 'Univision'],
	   ['usa-network', 'USA Network'],
	   ['viaplay', 'Viaplay']
	   ]

    for x in web_plataformas:
        title = x[1]
        title = title.replace('-', ' ')

        url = host + '/network/' + x[0] + '/'

        itemlist.append(item.clone( title = title, url = url, action ='list_all' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#':
        itemlist.append(item.clone( title = letra, action = 'list_letra', letra = letra.lower() ))

    return itemlist


def list_all(item): 
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1>(.*?)Mas Vistas</h2>')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')

        tipo = 'tvshow' if '/tvshows/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        title = scrapertools.find_single_match(article, 'alt="([^"]+)"')
        thumb = scrapertools.find_single_match(article, '<img src="([^"]+)"')
        qlty = scrapertools.find_single_match(article, '<span class="quality">([^"]+)</span>')
        year = scrapertools.find_single_match(article, '<h3>.*?<span>(\d{4})<')

        if '(' + year +')' in title:
            title = title.replace('(' + year +')', '').strip()

        langs = []
        if '_icon_es.png' in article: langs.append('Esp')
        if '_icon_la.png' in article: langs.append('Lat')
        if '_icon_mx.png' in article: langs.append('Lat')
        if '_icon_sub.png' in article: langs.append('Vose')

        if not langs:
            otros = scrapertools.find_single_match(article, 'mini_icon_(.*?).png').capitalize()
            langs.append(otros)

        if '/tvshows/' in url:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, qualities=qlty, languages=','.join(langs),
                                        fmt_sufijo=sufijo, contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))
        else:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title = title, thumbnail = thumb, qualities=qlty, languages=','.join(langs),
                                        fmt_sufijo=sufijo, contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    # Paginador
    next_page = scrapertools.find_single_match(data, '<a class=\'arrow_pag\' href="([^"]+)">')
    if not next_page:
        next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?' + "href='(.*?)'")
        if not '/page/' in next_page: next_page = ''

    if next_page:
        itemlist.append(item.clone( title='>> Página siguiente', url = next_page, action='list_all', text_color='coral' ))

    return itemlist


def list_letra(item):
    logger.info()
    itemlist = []

    url = host + 'wp-json/dooplay/glossary/?term=' + item.letra + '&nonce=a11212fcf3&type='

    if item.search_type == 'movie': url = url + 'movies'
    else: url = url + 'tvshows'

    data = httptools.downloadpage(url).data
    # ~ logger.debug(data)

    try:
        data_js = jsontools.load(data)

        if not 'error' in data_js:
            for match in data_js:
                elem = data_js[match]

                url = elem['url']
                url = url.replace('\/', '/')

                if not url: continue

                title = elem['title']
                thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem['img'])

                try:
                    year = elem['year']
                except:
                    year = '-'

                if '/movies/' in url:
                    if item.search_type == 'tvshow': continue

                    itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                            contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))
                else:
                    if item.search_type == 'movie': continue

                    itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb,
                                                contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))
    except:
        pass

    if itemlist: 
        tmdb.set_infoLabels(itemlist)

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

    IDIOMAS = {'Español': 'Esp', 'Latino': 'Lat', 'Subtitulado': 'Vose'}

    data = do_downloadpage(item.url)
    # ~ logger.debug(data)

    bloque = scrapertools.find_single_match(data,"(?s)<div id='fakeplayer'(.*?)</ul></div></div>")   

    patron = "(?s)<li id='player-option-\d+' class='dooplay_player_option' data-type='.*?' data-post='.*?' .*?nume='.*?'.*?'title'>.*?<.*?'server'>.*?<"

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for match in matches:    
        _type = scrapertools.find_single_match(match,"data-type='(.*?)'")
        _post = scrapertools.find_single_match(match,"data-post='(.*?)'")
        _nume = scrapertools.find_single_match(match,"data-nume='(.*?)'")

        servidor = scrapertools.find_single_match(match,"class='server'>(.*?)<")
        servidor = servidor.split('.')[0]
        servidor = servertools.corregir_servidor(servidor)

        lang = scrapertools.find_single_match(match,"class='title'>(.*?)<")
        lang = IDIOMAS.get(lang, lang)
        if not lang: lang = '?'

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '',
                              _type = _type, _post = _post, _nume = _nume, language = lang ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    post = {'action': 'doo_player_ajax', 'post': item._post, 'nume': item._nume, 'type': item._type}
    headers = {'Referer': item.url}

    data = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=post, headers = headers).data

    url = scrapertools.find_single_match(data, 'src="(.*?)"')
    if not url: url = scrapertools.find_single_match(data, "src='(.*?)'")

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor and servidor != 'directo':
            url = servertools.normalize_url(servidor, url)
            itemlist.append(item.clone( url = url, server = servidor ))

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
