# -*- coding: utf-8 -*-

import re

from platformcode import logger, platformtools, recaptcha, recaptchav2
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

host = 'https://movidy.tv/'


# ~ def item_configurar_proxies(item):
    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    # ~ return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

# ~ def configurar_proxies(item):
    # ~ from core import proxytools
    # ~ return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    url = url.replace('https://xdede.co/', 'https://movidy.tv/')
    url = url.replace('https://movidy.co/', 'https://movidy.tv/')

    if not headers: headers = {}

    if 'Referer' not in headers: headers['Referer'] = host

    resp = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror)

    # ~ data = httptools.downloadpage_proxy('movidy', url, post=post, headers=headersraise_weberror=raise_weberror).data
    return resp.data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    itemlist.append(item.clone( title = 'Buscar intérprete ...', action = 'search', group = 'actor', search_type = 'person',
                       plot = 'Debe indicarse el nombre y apellido/s del intérprete.'))
    itemlist.append(item.clone( title = 'Buscar dirección ...', action = 'search', group = 'director', search_type = 'person',
                       plot = 'Debe indicarse el nombre y apellido/s del director.'))

    # ~ itemlist.append(item_configurar_proxies(item))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'peliculas/?estreno', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'peliculas/?mejor-valoradas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    # ~ itemlist.append(item_configurar_proxies(item))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_episodes', url = host + 'series/?novedades', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'series/?estreno', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'series/?mejor-valoradas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    # ~ itemlist.append(item_configurar_proxies(item))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    genres = [
       'Acción',
       'Animación',
       'Aventura',
       'Bélica',
       'Ciencia ficción',
       'Comedia',
       'Crimen',
       'Documental',
       'Drama',
       'Familia',
       'Fantasia',
       'Historia',
       'Misterio',
       'Música',
       'Romance',
       'Suspense',
       'Terror',
       'Wester'
       ]

    url_gen = host + 'peliculas/?genero[]='

    for genre in genres:
        title = genre

        url = url_gen + genre.replace(' ', '%20') + '&estreno[]='

        itemlist.append(item.clone( action = "list_all", title = title, url = url ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    limit_year = 1965 if item.search_type == 'movie' else 1986

    if item.search_type == 'movie':
        url_any = host + 'peliculas/?genero[]=&estreno[]='
    else:
        url_any = host + 'series/?genero[]=&estreno[]='

    for x in range(current_year, limit_year, -1):
        url = url_any +  str(x)

        itemlist.append(item.clone( action='list_all', title=str(x), url=url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    es_busqueda = '?s=' in item.url or '/actor/' in item.url or '/director/' in item.url
    tipo_url = 'tvshow' if '/serie' in item.url else 'movie'

    data = do_downloadpage(item.url)
    # ~ logger.debug(data)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)
    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' data-echo="([^"]+)"')
        title = scrapertools.find_single_match(article, ' title="([^"]+)"').strip()
        if not url or not title: continue

        tid = scrapertools.find_single_match(url, '(\d+)-')
        if tid:
            infoLabels = {'tmdb_id':tid, 'year': '-'}
        else:
            infoLabels = {'year': '-'}

        if es_busqueda:
            tipo = 'tvshow' if '/serie' in url else 'movie'
            if item.search_type not in ['all', tipo]: continue
        else:
            tipo = tipo_url

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            qlty = 'Low' if 'CALIDAD BAJA' in article else ''

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail  = thumb, qualities = qlty, fmt_sufijo = sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = infoLabels ))
        else:
            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo = sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = infoLabels ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"[^>]*>Pagina siguiente')
    if next_page_link:
        itemlist.append(item.clone( title = '>> Página siguiente', url = next_page_link, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile(' onclick="activeSeason\(this,\'temporada-(\d+)', re.DOTALL).findall(data)

    for numtempo in matches:
        title = 'Temporada ' + numtempo

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = numtempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)

def episodios(item):
    logger.info()
    itemlist=[]

    if not item.page: item.page = 0
    perpage = 50

    data = do_downloadpage(item.url)

    if '<footer>' in data: final = '<footer>'
    else:
       final = '</body>'

    cuantas = scrapertools.find_multiple_matches(data, '<div class="season temporada-(.*?)">')

    if len(cuantas) == 1:
         bloque = scrapertools.find_single_match(data, '<div class="season temporada-' + str(item.season) + '(.*?)' + final)
    else:
         bloque = scrapertools.find_single_match(data, '<div class="season temporada-' + str(item.season) + '(.*?)<div class="season temporada-')
         if not bloque:
             bloque = scrapertools.find_single_match(data, '<div class="season temporada-' + str(item.season) + '(.*?)' + final)

    patron = '<li>.*?<a href="(.*?)".*?data-echo="(.*?)".*?<h2>(.*?)</h2>.*?<div class="startEp">.*?<span>(.*?)</span>.*?<span>(.*?)</span>'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, thumb, title, season_episode, fecha in matches[item.page * perpage:]:
        season = scrapertools.find_single_match(season_episode, '(.*?)-').strip()
        episode = scrapertools.find_single_match(season_episode, '-(.*?)$').strip()

        if item.contentSeason and item.contentSeason != int(season): continue

        titulo = '%sx%s %s' % (season, episode, title)

        if fecha:  titulo = titulo + '  (' + fecha + ')'

        itemlist.append(item.clone( action = 'findvideos', title = titulo, thumbnail = thumb, url = url,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = episode ))

        if len(itemlist) >= perpage:
            break

    itemlist = sorted(itemlist, key = lambda it: it.contentEpisodeNumber)
	
    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color='coral' ))

    return itemlist

# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['screener', 'TS', '360p', '480p', 'rip', 'hdrip', 'hdrvrip', '720p', 'HDTV', '1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

# Si hay excepciones concretas de este canal, añadir aquí, si son genéricas añadir en servertools.corregir_servidor
def corregir_servidor(servidor):
    servidor = servidor.replace('www.', '').replace('.com', '').replace('.net', '').replace('.org', '').replace('.co', '').replace('.cc', '')
    servidor = servidor.replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '').replace('.eu', '').replace('.ws', '')
    servidor = servidor.replace('.', '')

    servidor = servertools.corregir_servidor(servidor)

    if servidor == 'pro': return 'fembed'
    if servidor in ['beta', 'bot', 'soap']: return 'directo'
    return servidor


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'castellano': 'Esp', 'español castellano': 'Esp', 'latino': 'Lat', 'subtitulado': 'Vose', 'ingles subtitulado': 'Vose', 'ingles': 'VO'}

    datos = do_downloadpage(item.url)
    # ~ logger.debug(datos)

    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", datos)

    # Enlaces Descarga y Externos
    for part_data in data.split('<div class="contEP contepID_3">'):
        patron = r'<li><a href="([^"]+)" rel="nofollow noopener" target="_blank">.*?<span><[^>]+>([^<]+)<b>([^<]+).*?' \
                 r'src="https://movidy\.tv/wp-content/themes/Movidy/images/(.*?)\.png"'

        matches = scrapertools.find_multiple_matches(part_data, patron)

        for url, servidor, qlty, lang in matches:
            url = host[:-1] + url
            servidor = servidor.split('.', 1)[0]
            servidor = corregir_servidor(servidor)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, referer = item.url,
                                  language = IDIOMAS.get(lang, 'VO'), quality = qlty, quality_num = puntuar_calidad(qlty) ))

    # Enlaces Ver Online
    source = scrapertools.find_single_match(datos, 'src="(/video/\d+.mp4)')
    url = 'https://movidy.tv' + source

    data_source = do_downloadpage(url, raise_weberror=False)

    data_source = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data_source)

    matches = scrapertools.find_multiple_matches(data_source, '.*?<li id="(.*?)".*?<span>(.*?)</span><p>(.*?)</p>')

    for opt, servidor, qlty in matches:
        url = scrapertools.find_single_match(datos, "getElementById\('%s'\).setAttribute\('onclick', 'go_to_player\(.'([^']+)" % opt)[:-1]
        url = host[:-1] + url

        servidor = servidor.lower()
        servidor = corregir_servidor(servidor)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, referer = item.url,
                              language = IDIOMAS.get(lang, 'VO'), quality = qlty, quality_num = puntuar_calidad(qlty) ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    headers = {'Referer': item.referer}

    logger.info("check-11-movidy-tv: %s" % item.url)

    data = do_downloadpage(item.url, headers=headers)
    logger.info("check-12-movidy-tv: %s" % data)

    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    sitekey = scrapertools.find_single_match(data, 'data-sitekey="([^"]+)')
    if not sitekey:
        return 'Opción aún sin desarrollar'

    #response = recaptcha.get_recaptcha_response(sitekey, item.url)
    #return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

    resp = httptools.downloadpage(item.url, add_referer=True)
    if not resp.sucess:
        return 'El fichero no existe o ha sido borrado'

    data = resp.data

    key = scrapertools.find_single_match(data, 'render=([^"]+)"')
    co = "aHR0cHM6Ly9ldm9sb2FkLmlvOjQ0Mw"
    loc = "https://movidy.tv"
    tk = recaptchav2.rev2(key, co, "", loc)
    player_url = item.url #"https://movidy.tv/SecurePlayer"
    code = item.url #scrapertools.find_single_match(item.url, "/e/([A-z0-9]+)")
    post = {"code": code, "token": tk}

    data = httptools.downloadpage(player_url, headers={"User-Agent": httptools.get_user_agent(), "Referer": item.url}, post=post).data

    logger.info("check-13-mtv: %s" % data)

    response = tk

    #headers = {'Referer': item.url, 'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X)'}
    headers = {}

    #resp = httptools.downloadpage(item.url, headers=headers, raise_weberror=False)

    if '/enlace/' in item.url:
        #id = scrapertools.find_single_match(data, 'input name="id" value="([^"]+)"')
        post = {'g-recaptcha-response': response, 'id': tk} #key}

        resp = httptools.downloadpage(item.url, post=post, headers=headers, follow_redirects=False)
        logger.info("check-14-movidy-tv: %s" % resp)

        url = resp.headers.get('location')
    else:
        id = scrapertools.find_single_match(data, "player.id='([^']+)")
        post = {'token': response, 'id': id, 'ajax': 'true'}
        resp = do_downloadpage(item.url, post=post, headers=headers)
        url = scrapertools.find_single_match(resp.data,'link":"([^"]+)').replace('\\','')

    if url:
       servidor = servertools.get_server_from_url(url)
       if servidor != 'directo':
           url = servertools.normalize_url(servidor, url)
           itemlist.append(item.clone( url = url, server = servidor ))

    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        if item.group:
            item.url = host + item.group + '/' + texto.replace(" ", "-") + '/'
        else:
            item.url = host + '?s=' + texto.replace(" ", "+")

        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

