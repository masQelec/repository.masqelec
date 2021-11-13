# -*- coding: utf-8 -*-

import re, os

from platformcode import logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://pctfenix.com/'

perpage = 30


def item_configurar_proxies(item):
    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)

def do_downloadpage(url, post=None, headers=None):
    # ~ data = httptools.downloadpage(url, post=post, headers=headers).data
    data = httptools.downloadpage_proxy('pctfenix', url, post=post, headers=headers).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    itemlist.append(item_configurar_proxies(item))
    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo (castellano)', action = 'list_all', url = host + 'descargar-peliculas/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Catálogo (latino)', action = 'list_all', url = host + 'descargar-peliculas/latino', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'descargar-peliculas/estrenos-de-cine/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_last', url = host + 'descargar-lo-ultimo/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'mas-valorados/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'mas-visitados/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En HD', action = 'list_all', url = host + 'descargar-peliculas/hd/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'En x264 MKV', action ='list_all', url = host + 'descargar-peliculas/x264-mkv/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'En 3D', action ='list_all', url = host + 'descargar-peliculas/3d/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad (en castellano)', action = 'por_calidad', url = host + '/torrents-de-peliculas.html',
                                search_type = 'movie', calidad_type = 'cast' ))
    itemlist.append(item.clone( title = 'Por calidad (en latino)', action = 'por_calidad', url = host + '/secciones.php?sec=ultimos_torrents',
                                search_type = 'movie', calidad_type = 'latino' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    itemlist.append(item_configurar_proxies(item))
    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Series TV', action = 'list_all', url = host + 'descargar-series/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Series HD', action = 'list_all', url = host + 'descargar-series/hd/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_last', url = host + 'descargar-lo-ultimo/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'mas-valorados/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'mas-visitados/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    itemlist.append(item_configurar_proxies(item))
    return itemlist


# ~ por si venimos de grupos
def calidades(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Por calidad (en castellano)', action = 'por_calidad', url = host + '/torrents-de-peliculas.html',
                                search_type = 'movie', calidad_type = 'cast' ))
    itemlist.append(item.clone( title = 'Por calidad (en latino)', action = 'por_calidad', url = host + '/secciones.php?sec=ultimos_torrents',
                                search_type = 'movie', calidad_type = 'latino' ))

    return itemlist


def por_calidad(item):
    logger.info()
    itemlist = []

    if item.calidad_type == "cast":
        url = host + "descargar-peliculas"
    elif item.calidad_type == "latino":
        url = host + "descargar-peliculas/latino/"

    data = do_downloadpage(url)

    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)
    data = scrapertools.find_single_match(data, r'<div class="title-hd">(.*?)<\/div>')

    matches = scrapertools.find_multiple_matches(data, '<a href="([^"]+)" title="([^"]+)"')

    for url, title in matches:
        itemlist.append(item.clone( title = title, action = 'list_all', url = url if url.startswith("http") else host[:-1] + url, page=0))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item): 
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    if item.page == 0:
        data = do_downloadpage(item.url)

        data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

        matches = re.compile('<img src="([^"]+)" alt="([^"]+)".*?a href="([^"]+)".*?<strong>([^<]+)').findall(data)
        num_matches = len(matches)

        for thumb, title, url, qlty in matches:
            if not url or not title: continue

            titulo = title.split('(')[0].strip()

            if "Temp" in titulo and item.search_type == "tvshow": 
                tmdb_title = re.sub('(?i)(Temp.*)', '', titulo)
            else:
                tmdb_title = title

            qlty = qlty.replace('(', '').replace(')', '').strip()

            if not thumb.startswith('http'): thumb = "https:" + thumb

            if item.search_type == 'tvshow':
                if not "/temporada-" in url and not "/capitulo-" in url: continue

                itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb,
                                            contentType='tvshow', contentSerieName=tmdb_title, infoLabels={'year': '-'} ))
            else:
                 if "/temporada-" in url or "/capitulo-" in url: continue

                 itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, qualities=qlty,
                                            contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))

            if len(itemlist) >= perpage: break          

    else:

        data = do_downloadpage(host + "controllers/load-more.php", post="i=%s&c=%s&u=%s" % (item.page, perpage, '/' + item.url.replace(host, '')))

        data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

        matches = re.compile('<img src="([^"]+)" alt="([^"]+)".*?a href="([^"]+)"').findall(data)
        num_matches = len(matches)

        for thumb, title, url in matches:
            if not url or not title: continue

            titulo = title.split('(')[0].strip()
            if "Temp" in titulo and item.search_type == "tvshow": 
                tmdb_title = re.sub('(?i)(Temp.*)', '', titulo)
            else:
                tmdb_title = title

            if not thumb.startswith('http'): thumb = "https:" + thumb

            if item.search_type == 'tvshow':
                if not "/temporada-" in url and not "/capitulo-" in url: continue

                itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb,
                                            contentType='tvshow', contentSerieName=tmdb_title, infoLabels={'year': '-'} ))
            else:
                if "/temporada-" in url or "/capitulo-" in url: continue

                itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb,
                                            contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if num_matches >= perpage:
        itemlist.append(item.clone( title='>> Página siguiente', url=item.url, page=item.page + 1, action='list_all', text_color='coral' ))

    return itemlist


def list_last(item): 
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<img src="([^"]+)" alt="([^"]+)".*?a href="([^"]+)".*?<strong>([^<]+)').findall(data)
    num_matches = len(matches)

    for thumb, title, url, qlty in matches[item.page * perpage:]:
        if not url or not title: continue

        titulo = title.split('(')[0].strip()

        if "Temp" in titulo and item.search_type == "tvshow": 
            tmdb_title = re.sub('(?i)(Temp.*)', '', titulo)
        else:
            tmdb_title = title

        qlty = qlty.replace('(', '').replace(')', '').strip()

        if not thumb.startswith('http'): thumb = "https:" + thumb

        if item.search_type == 'tvshow':
            if not "/temporada-" in url and not "/capitulo-" in url: continue

            itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=tmdb_title, infoLabels={'year': '-'} ))
        else:
            if "/temporada-" in url or "/capitulo-" in url: continue

            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, qualities=qlty,
                                            contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break          

    tmdb.set_infoLabels(itemlist)

    if num_matches > perpage:
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_last', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    if not item.url.startswith("http"): item.url = host[:-1] + item.url

    item.url = item.url.replace(host, host + 'descargar-gratis/')

    data = do_downloadpage(item.url)

    notificado = False
    titulo = item.contentSerieName.replace('&#038;', '&').replace('-', '').strip()

    if 'function loadDD' in data:
        notificado = True
        platformtools.dialog_notification(titulo, '[COLOR blue]Cargando vídeos [/COLOR]')

        data0 = ''
        data1 = ''
        data2 = ''

        url = host + 'controllers/load.chapters.type.php'

        patron = '<script type="text/javascript">var.*?CNAME.*?'
        patron += "'(.*?)'.*?CID.*?"
        patron += "'(.*?)'"

        try:
           _cname, _cid, = scrapertools.find_single_match(data, patron)

           bloque = scrapertools.find_single_match(data, r'function loadDD(.*?)console.dir')

           _cidr = scrapertools.find_single_match(bloque, '==0.*?CIDR.*?=(.*?);')
           _cidr = _cidr.strip()
           if _cidr:
               _o = 0
               post = {'_cname': _cname, '_cid': _cid, '_cidr': _cidr, '_o': _o}
               data0 = do_downloadpage(url, post = post)

           _cidr = scrapertools.find_single_match(bloque, '==1.*?CIDR.*?=(.*?);')
           _cidr = _cidr.strip()
           if _cidr:
               _o = 1
               post = {'_cname': _cname, '_cid': _cid, '_cidr': _cidr, '_o': _o}
               data1 = do_downloadpage(url, post = post)

           else:

               _cidr = scrapertools.find_single_match(bloque, '==1.*?else.*?CIDR.*?=(.*?);')
               _cidr = _cidr.strip()
               if _cidr:
                   _o = 2
                   post = {'_cname': _cname, '_cid': _cid, '_cidr': _cidr, '_o': _o}
                   data2 = do_downloadpage(url, post = post)

           data = data0 + data1 + data2   

        except:
           pass

    matches = scrapertools.find_multiple_matches(data, r"onClick='modCap\((\d+)\)'>\s*([^<]+)")

    if len(matches) >= 50:
        if not notificado:
            platformtools.dialog_notification(titulo, '[COLOR blue]Cargando vídeos [/COLOR]')

    i = 0

    for id, title in matches:
        i += 1

        itemlist.append(item.clone( action='findvideos', title=title, episodeId=id,
                                    contentType='episode', contentSeason = 1, contentEpisodeNumber = i ))

    return itemlist    


def findvideos(item):
    logger.info()
    itemlist = []

    if not item.url.startswith("http"): item.url = host[:-1] + item.url

    if item.contentType == "movie":
        item.url = item.url.replace(host, host + 'descargar-gratis/')
        data = do_downloadpage(item.url)
    else:
        headers = {'Referer': item.url}

        data = do_downloadpage(host + "controllers/show.chapters.php", post='id=' + str(item.episodeId), headers=headers)

    url_torrent = scrapertools.find_single_match(data, '<div class="ctn-download-torrent".*?<a href="javascript:[^"]+".*?id="[^"]+".*?data-ut\s*=\s*"([^"]+)"')

    if '[castellano]' in data: 
        lang = 'Esp'
    else:
        lang = 'Lat'

    if url_torrent:
        itemlist.append(Item( channel = item.channel, action = 'play', title = '', language = lang,
                                                      url = url_torrent if url_torrent.startswith("http") else "https:" + url_torrent, server = 'torrent'))

    if '<div class="box-content-links">' in data:
        block = scrapertools.find_single_match(data, '<div class="box-content-links">(.*?)</div')
        matches = scrapertools.find_multiple_matches(block, '<a href="([^"]+)".*?">(.*?)</a>')

        for url, servidor in matches:
            url = url.strip()
            servidor = servertools.corregir_servidor(servidor)

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', language = lang, url = url, server = servidor))

    elif '>Links de Descarga<' in data:
        block = scrapertools.find_single_match(data, '>Links de Descarga<(.*?)</div')
        matches = scrapertools.find_multiple_matches(block, '<a href="([^"]+)".*?">(.*?)</a>')

        for url, servidor in matches:
            url = url.strip()
            servidor = servertools.corregir_servidor(servidor)

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', language = lang, url = url, server = servidor))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.url.endswith('.torrent'):
        from platformcode import config

        data = do_downloadpage(item.url)
        file_local = os.path.join(config.get_data_path(), "temp.torrent")
        with open(file_local, 'wb') as f: f.write(data); f.close()

        itemlist.append(item.clone( url = file_local, server = 'torrent' ))
    else:
        itemlist.append(item.clone( url= item.url, server = item.server ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url, post = item.post)

    patron = '<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, thumb, title in matches:
        if not url or not title: continue

        if "/temporada-" in url or "/capitulo-" in url:
            contentType = "tvshow"
        else:
            contentType = "movie"

        titulo = title.split('(')[0].strip()

        if contentType == "tvshow":
            if "Temp" in titulo: 
                tmdb_title = re.sub('(?i)(Temp.*)', '', titulo)
            else:
                tmdb_title = title
        else:
            tmdb_title = title

        if not thumb.startswith('http'): thumb = "https:" + thumb

        tipo = 'tvshow' if contentType == "tvshow" else 'movie'
        if item.search_type not in ['all', tipo]: continue

        sufijo = '' if item.search_type != 'all' else tipo

        if contentType == 'tvshow':
            if not item.search_type == 'all':
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=tmdb_title, infoLabels={'year': '-'} ))
        else:
            if not item.search_type == 'all':
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist
	
def search(item, texto):
    logger.info()
    try:
       item.url = host + 'controllers/search-mini.php'
       item.post = 's=%s' % texto.replace(" ", "+")
       return list_search(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []

