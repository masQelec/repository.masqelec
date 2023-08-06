# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True


import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb


host = 'https://mejortorrent.se'


perpage = 30


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_mejortorrentnz_proxies', default=''):
        tit = '[COLOR %s][B]Quitar los proxies del canal[/B][/COLOR]' % color_list_proxies
        context.append({'title': tit, 'channel': item.channel, 'action': 'quitar_proxies'})

    tit = '[COLOR %s]Ajustes categoría proxies[/COLOR]' % color_exec
    context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = '[B]Configurar proxies a usar ...[/B]', action = 'configurar_proxies', folder=False, context=context, plot=plot, text_color='red' )

def quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)
    return True

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://mejortorrent.nz', 'https://mejortorrent.cc']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    timeout = None
    if host in url:
        if config.get_setting('channel_mejortorrentnz_proxies', default=''): timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        data = httptools.downloadpage_proxy('mejortorrentnz', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '/?s=' in url:
                platformtools.dialog_notification('MejorTorrentNz', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')
                data = httptools.downloadpage_proxy('mejortorrentnz', url, post=post, headers=headers, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='mejortorrentnz', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))
    itemlist.append(item.clone( title = 'Documentales', action = 'mainlist_documentales', text_color = 'cyan' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/peliculas-13/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_last', url = host + '/ultimos-torrents-3/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En HD', action = 'list_all', url = host + '/peliculas-hd-3/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/series-3/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_last', url = host + '/ultimos-torrents-3/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'En HD', action = 'list_all', url = host + '/series-hd-2/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

    return itemlist


def mainlist_documentales(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/documentales-3/', search_type = 'documentary' ))

    itemlist.append(item.clone( title = 'Últimos', action = 'list_list', url = host + '/ultimos-torrents-3/', search_type = 'documentary' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'documentary' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    elif item.search_type == 'tvshow': text_color = 'hotpink'
    else: text_color = 'cyan'

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if item.search_type == 'tvshow':
            url = host + '/listado/?cat=series&letra=' + letra
        if item.search_type == 'movie':
            url = host + '/listado/?cat=peliculas&letra=' + letra
        else:
            url = host + '/listado/?cat=documentales&letra=' + letra

        itemlist.append(item.clone( title = letra, action = 'list_alfa', url = url, letra = letra, text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<td><div align="justify"><center>(.*?)torrent</h2>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<img src="(.*?)".*?alt="(.*?)"')

    num_matches = len(matches)

    for url, thumb, title, in matches[item.page * perpage:]:
        if title == 'Documentales': continue

        if not url or not title: continue

        title = title.replace('[720p]', '').strip()

        title = title.replace('&#215;', 'x').replace("&#8217;", "'")

        titulo = title.split('-')[0].strip()

        if item.search_type == 'tvshow': 
            if '&#' in titulo: titulo = scrapertools.find_single_match(titulo, '(.*?) ')

        title = re.sub(r' \(.*?\)', '', title)

        if item.search_type == 'movie':
            titulo = titulo.replace('4K', '').replace('[HDRip]', '').replace('[BluRay', '').replace('[MicroHD', '').strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))
        else:
            if " Temporada" in title: SerieName = title.split(" Temporada")[0]
            else: SerieName = title

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, contentType='tvshow', contentSerieName=SerieName, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title = 'Siguientes ...', page = item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            next_page = scrapertools.find_single_match(data, "class='nopaginar'>.*?href='(.*?)'")

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title='Siguientes ...', page = 0, action='list_all', url=next_page, text_color='coral' ))

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if item.search_type == 'movie':
        fin_movies = 'Series:' if 'Series:' in data else 'Juegos:'
        if fin_movies == 'Juegos:' and not 'Juegos:' in data: fin_movies = '</table>'

        data = scrapertools.find_single_match(data, 'Peliculas:(.*?)' + fin_movies)
    else:
        fin_tvshows = 'Variados:' if 'Variados:' in data else '</table>>'
        data = scrapertools.find_single_match(data, 'Series:(.*?)' + fin_tvshows)

    matches = scrapertools.find_multiple_matches(data, "href='([^']+)'.*?>(.*?)<.*?'>(.*?)<")

    for url, title, qlty in matches:
        title = title.replace('[720p]', '').strip()

        titulo = title.split('-')[0].strip()
        if item.search_type == 'tvshow': 
            if '&#' in titulo: titulo = scrapertools.find_single_match(titulo, '(.*?) ')

        title = re.sub(r' \(.*?\)', '', title)

        qlty = qlty.replace('(', '').replace(')', '').strip()

        if '[' in title:
            if qlty: title = title.replace('[' + qlty + ']', '').strip()

        if item.search_type == 'movie':
            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, qualities = qlty, contentType = 'movie', contentTitle = titulo, infoLabels = {'year': '-'} ))
        else:
            itemlist.append(item.clone( action='episodios', url = url, title = title,  qualities = qlty, contentType = 'tvshow', contentSerieName = titulo, infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_alfa(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Mostrando(.*?)</table>')

    matches = scrapertools.find_multiple_matches(bloque, "href='([^']+)'.*?>(.*?)<")

    num_matches = len(matches)

    for url, title in matches[item.page * perpage:]:
        title = title.replace('[720p]', '').strip()

        titulo = title.split('-')[0].strip()
        if item.search_type == 'tvshow': 
            if '&#' in titulo: titulo = scrapertools.find_single_match(titulo, '(.*?) ')

        title = re.sub(r' \(.*?\)', '', title)

        if not title: continue

        if item.search_type == 'movie':
            refer = scrapertools.find_single_match(url, '/peli-descargar-torrent-(.*?)-')

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, qualities = refer, contentType = 'movie', contentTitle = titulo, infoLabels = {'year': '-'} ))

        if item.search_type == 'tvshow':
            itemlist.append(item.clone( action='episodios', url = url, title = title, grupo = 'selecc', contentType = 'tvshow', contentSerieName = titulo, infoLabels = {'year': '-'} ))

        if item.search_type == 'documentary':
            refer = scrapertools.find_single_match(url, '/peli-descargar-torrent-(.*?)-')

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, qualities = refer, contentType = 'movie', contentTitle = titulo, infoLabels = {'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title = 'Siguientes ...', page = item.page + 1, action='list_alfa', text_color='coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    i = 0

    if item.search_type == 'documentary':
         bloque = scrapertools.find_single_match(data, 'Listado de los episodios(.*?)Marcar/Desmarcar Todos')

         matches = scrapertools.find_multiple_matches(bloque, "bgcolor='#C8DAC8'.*?</td>.*?'>(.*?)</td>.*?name='(.*?)'.*?value='(.*?)'")

         for title, id, value in matches:
             title = title.strip()

             if item.grupo == 'selecc': title = title + '  ' + item.title
             else: title = title + ' ' + str(item.contentSerieName)

             i += 1

             itemlist.append(item.clone( action='findvideos', id = id, value = value, ref = item.url, title = title,
                                         contentType='episode', contentSeason = 1, contentEpisodeNumber = i ))

         return itemlist

    bloque = scrapertools.find_single_match(data, 'Listado de los episodios(.*?)Descargar Seleccionados')

    matches = scrapertools.find_multiple_matches(bloque, "bgcolor='#C8DAC8'.*?" + '<a href="(.*?)">(.*?)</a>.*?' + "name='(.*?)'.*?value='(.*?)'")

    for url, temp_epis, id, value in matches:
        title = temp_epis.strip()

        if item.name_search:
           if not title.lower() in item.name_search.lower(): continue

        if item.grupo == 'selecc': title = title + '  ' + item.title
        else: title = title + ' ' + str(item.contentSerieName)

        if 'Temporada' in title:
            title = title.split("Temporada")[0]
            title = title.strip()

        tempo = scrapertools.find_single_match(temp_epis, '(.*?)X')

        if ' y ' in temp_epis: epis = scrapertools.find_single_match(temp_epis, 'X(.*?)y').strip()
        else: epis = scrapertools.find_single_match(temp_epis, 'X(.*?)$')

        SerieName = scrapertools.find_single_match(item.contentSerieName, '(.*?)Temporada').strip()

        itemlist.append(item.clone( action='findvideos', id = id, value = value, ref = item.url, title = title,
                                    contentSerieName = SerieName, contentType='episode', contentSeason = tempo, contentEpisodeNumber = epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    url = ''

    if item.search_type == 'movie':
        data = do_downloadpage(item.url)
    else:
        if not item.id or not item.value: return itemlist

        if item.search_type == 'documentary':
            data = do_downloadpage(item.url)

            id_post = scrapertools.find_single_match(data, '<input type="hidden" value="(.*?)" name="id_post">')
            if id_post: item.value = id_post

        post = {item.id : item.value}

        try:
           vid = host + '/download_tv.php'

           if not vid.startswith(host):
               resp = httptools.downloadpage(vid, post = post, headers = {'Referer': item.ref}, raise_weberror=False)
           else:
               resp = httptools.downloadpage_proxy('mejortorrentnz', vid, post = post, headers = {'Referer': item.ref}, raise_weberror=False)

           data = resp.data
        except:
           return itemlist

    hash = scrapertools.find_single_match(data, '<input type="hidden".*?<input type="hidden".*?value="(.*?)"')
    if not hash: hash = scrapertools.find_single_match(data, '<a class="opcion.*?u=(.*?)"')

    if not hash: return itemlist

    lang = 'Esp'

    qlty = scrapertools.find_single_match(data, "<b>Formato.*?</b>(.*?)<br>").strip()
    qlty = qlty.replace('&nbsp;', '').strip()

    size = scrapertools.find_single_match(data, "<b>Tamaño.*?</b>(.*?)<br>").strip()
    size = size.replace('&nbsp;', '').strip()

    itemlist.append(Item( channel = item.channel, action = 'play', title = '', hash = hash, server = 'torrent', language = lang, quality = qlty, other = size ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.hash:
        url = host + '/torrent_dmbk.php?u=' + item.hash

        if not url.startswith(host):
            resp = httptools.downloadpage(url, headers={'Referer': host + '/download_torrent.php'}, follow_redirects=False)
        else:
            resp = httptools.downloadpage_proxy('mejortorrentnz', url, headers={'Referer': host + '/download_torrent.php'}, follow_redirects=False)

        link = ''

        if 'location' in resp.headers:
            link = resp.headers['location']

        if not link:
            return 'Archivo [COLOR plum]No localizado[/COLOR]'

        data = do_downloadpage(link, headers={'Referer': host + '/download_torrent.php'})

        url = link

        if PY3:
            from core import requeststools
            data = requeststools.read(url, 'mejortorrentnz')
        else:
            data = do_downloadpage(url)

        if data:
            if '<h1>Not Found</h1>' in str(data) or '<!DOCTYPE html>' in str(data) or '<!DOCTYPE>' in str(data):
                return 'Archivo [COLOR red]Inexistente[/COLOR]'

            import os

            file_local = os.path.join(config.get_data_path(), "temp.torrent")
            with open(file_local, 'wb') as f: f.write(data); f.close()

            itemlist.append(item.clone( url = file_local, server = 'torrent' ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, r'Has realizado una búsqueda(.*?)</table>')

    matches = scrapertools.find_multiple_matches(bloque, "href='(.*?)'.*?" + '">' + "(.*?)</a>.*?'>(.*?)</a>.*?<.*?'>(.*?)</td>")

    num_matches = len(matches)

    for url, title, qlty, type in matches[item.page * perpage:]:
        if type == 'Peliculas': pass 
        elif type == 'Series': pass
        elif type == 'Series HD': pass
        elif type == 'Capitulos': pass
        elif type == 'Documentales': pass
        else: continue

        if item.search_type != 'all':
            if item.search_type == 'movie':
                if type == 'Series' or type == 'Series HD' or type == 'Capitulos': continue
                elif type == 'Documentales': continue
            else:
                if type == 'Peliculas': continue
                elif type == 'Documentales': continue

        sufijo = ''

        search_type = item.search_type

        if item.search_type == 'all':
            if type == 'Peliculas':
               search_type = 'movie'
               sufijo = 'movie'
            elif type == 'Series' or type == 'Series HD' or type == 'Capitulos':
               search_type = 'tvshow'
               sufijo = 'tvshow'
            else:
               sufijo = '[COLOR cyan]Documental[/COLOR]'
               search_type = 'documentary'

        title = title.replace("<font Color='darkblue'>", '').replace('</font>', '').replace("<span style='color:gray;'>", '').replace('</span>', '').strip()
        title = title.replace('[720p]', '').strip()
        title = title.replace('&#215;', 'x')

        titulo = title.split('-')[0].strip()
        title = re.sub(r' \(.*?\)', '', title)

        qlty = qlty.replace('(', '').replace(')', '').strip()

        if type == 'Capitulos': name_search = titulo
        else: name_search = ''

        if search_type == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            titulo = titulo.replace('4K', '').replace('[HDRip]', '').replace('[BluRay', '').replace('[MicroHD', '').strip()

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, qualities = qlty, fmt_sufijo = sufijo,
                                        search_type = search_type, contentType = 'movie', contentTitle = titulo, infoLabels = {'year': '-'} ))

        if search_type == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            if " Temporada" in title: SerieName = title.split(" Temporada")[0]
            else: SerieName = title

            itemlist.append(item.clone( action='episodios', url = url, title = title, qualities = qlty, fmt_sufijo = sufijo, name_search = name_search,
                                        search_type = search_type, contentType = 'tvshow', contentSerieName = SerieName, infoLabels = {'year': '-'} ))

        if item.search_type == 'documentary':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            titulo = title

            titulo = titulo.replace('4K', '').replace('[HDRip]', '').replace('[BluRay', '').replace('[MicroHD', '').strip()

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, qualities = qlty, fmt_sufijo = sufijo,
                                        search_type = search_type, contentType = 'movie', contentTitle = titulo, infoLabels = {'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title = 'Siguientes ...', page = item.page + 1, action='list_search', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '/?s=' + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
