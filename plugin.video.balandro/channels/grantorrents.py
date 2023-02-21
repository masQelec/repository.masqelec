# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb

from lib import decrypters


host = 'https://grantorrent.lat/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://grantorrents.org/', 'https://grantorrents.pro/', 'https://grantorrent.co/',
             'https://grantorrent.plus/', 'https://grantorrent.uk/', 'https://grantorrent.win/',
             'https://grantorrent.lat/', 'https://grantorrent.co/', 'https://www1.grantorrent.co/']


domain = config.get_setting('dominio', 'grantorrents', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'grantorrents')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'grantorrents')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_grantorrents_proxies', default=''):
        tit = '[COLOR %s][B]Quitar los proxies del canal[/B][/COLOR]' % color_list_proxies
        context.append({'title': tit, 'channel': item.channel, 'action': 'quitar_proxies'})

    tit = '[COLOR %s]Ajustes categoría proxies[/COLOR]' % color_exec
    context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, context=context, plot=plot, text_color='red' )

def quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)
    return True

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    if '/fechas/' in url: raise_weberror = False

    # ~ data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    data = httptools.downloadpage_proxy('grantorrents', url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'grantorrents', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_grantorrents', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='grantorrents', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_grantorrents', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

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


    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'pelis/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'tendencias/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'tendencias/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>GÉNEROS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if 'Estrenos' in title: continue

        itemlist.append(item.clone( action = 'list_all', title = title, url = url ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1949, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'fechas/' + str(x) + '/', action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h2>(.*?)>Más Descargadas</h2>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<h1>(.*?)>Más Descargadas</h2>')
    if not bloque: bloque = data

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not url or not title: continue

        title = title.replace('Descargar', '').replace('en torrent', '').replace('torrent', '').strip()

        title = title.replace('&#8217;', "'")

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        year = scrapertools.find_single_match(match, '</h3> <span>.*? .*? (.*?)</span>').strip()
        if not year: year = '-'

        lang = 'Esp'

        if '/tendencias/' in item.url:
            if item.search_type == 'tvshow':
                if not '/temporadas/' in url: continue
            elif item.search_type == 'movie':
                if not '/pelis/' in url: continue

        if '/series/' in url:
            if " castellano" in title: SerieName = title.split(" castellano")[0]
            else: SerieName = title

            if ' castellano ' in title: title = title.replace(' castellano ', '').strip()
            if 'HD' in title: title = title.replace('HD', '').strip()

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages = lang,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

        elif '/temporadas/' in url:
            SerieName = title

            if ": Temporada" in title: SerieName = title.split(": Temporada")[0]

            if ' castellano ' in title: title = title.replace(' castellano ', '').strip()
            if 'HD' in title: title = title.replace('HD', '').strip()

            tempo = scrapertools.find_single_match(url, '-temporada-(.*?)-')
            if not tempo: tempo = 1

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, languages = lang,
                                        contentSerieName = SerieName, contentType = 'season', contentSeason = tempo,
                                        infoLabels={'year': year} ))

        else:
            if " castellano" in title: titulo = title.split(" castellano")[0]
            else: titulo = title

            if ' castellano ' in title: title = title.replace(' castellano ', '').strip()
            if 'HD' in title: title = title.replace('HD', '').strip()

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, languages = lang,
                                        contentType = 'movie', contentTitle = titulo, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<span class="current">.*?href="([^"]+)')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile("<span class='se-t.*?'>(.*?)</span>", re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>" + str(item.contentSeason) + "</span>(.*?)</div></div>")
    if not bloque: bloque = data

    patron = "<li class='mark-(.*?)'>.*?src='(.*?)'.*?<a href='(.*?)'>(.*?)</a>"
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    if item.page == 0:
        sum_parts = len(matches)

        try: tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
        except: tvdb_id = ''

        if tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('GranTorrents', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('GranTorrents', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('GranTorrents', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]100[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('GranTorrents', '[COLOR cyan]Cargando 100 elementos[/COLOR]')
                    item.perpage = 100

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('GranTorrents', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts

    for epis, thumb, url, title in matches[item.page * item.perpage:]:
        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    lang = 'Esp'

    data = do_downloadpage(item.url)

    patron = "<tr id='link-.*?<a href='(.*?)'.*?<strong class='quality'>(.*?)</strong>.*?<strong class='quality'>(.*?)</strong>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, quality, peso in matches:
        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = 'torrent',
                              language = lang, quality = quality, other = peso ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = ''

    if '&urlb64=' in item.url:
        new_url = scrapertools.find_single_match(item.url, "&urlb64=(.*?)$")
        url = base64.b64decode(new_url).decode("utf-8")

        # ~ url = httptools.downloadpage(url, follow_redirects=False).headers['location']
        url = httptools.downloadpage_proxy('grantorrents', url, follow_redirects=False).headers['location']

    if not item.url.endswith('.torrent'):
        host_torrent = host[:-1]
        url_base64 = decrypters.decode_url_base64(item.url, host_torrent)

        if url_base64.endswith('.torrent'): url = url_base64

    if not url:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<a id="link".*?href="(.*?)"')

    if url.endswith('.torrent'):
        if 'url=' in url:
            url = scrapertools.find_single_match(str(url), 'url=(.*?)$')
            if not url.endswith('.torrent'): return itemlist

        url = url.replace('https://vk.com/away.php?to=', '').strip()

        if '/grantorrents.pro/' in url: url = url.replace('https://grantorrents.pro/', host)

        elif '/dl.grantorrents.com/' in url: url = url.replace('/dl.grantorrents.com/', '/dl.grantorrent.lat/')

        itemlist.append(item.clone( url = url, server = 'torrent' ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)>Año de lanzamiento<')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, ' alt="(.*?)"')
        if not url or not title: continue

        title = title.replace('Descargar', '').replace('en torrent', '').replace('torrent', '').strip()

        thumb = scrapertools.find_single_match(match, '<noscript><img src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>').strip()
        if not year: year = '-'

        lang = 'Esp'

        tipo = 'movie' if '/pelis/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            if " castellano" in title: SerieName = title.split(" castellano")[0]
            else: SerieName = title

            if ' castellano ' in title: title = title.replace(' castellano ', '').strip()
            if 'HD' in title: title = title.replace('HD', '').strip()

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages = lang, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            if " castellano" in title: titulo = title.split(" castellano")[0]
            else: titulo = title

            if ' castellano ' in title: title = title.replace(' castellano ', '').strip()
            if 'HD' in title: title = title.replace('HD', '').strip()

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, languages = lang, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = titulo, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
