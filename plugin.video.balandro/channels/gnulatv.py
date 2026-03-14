# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www2.gnula.one/'


perpage = 21


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_gnulatv_proxies', default=''):
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


def do_downloadpage(url, post=None):
    hay_proxies = False
    if config.get_setting('channel_gnulatv_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('gnulatv', url, post=post, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='GnulaTv', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/estreno/' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_last', url = host, group = 'estrenos', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_last', url = host, group = 'novedades' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'category/recomendada/' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'generos/')

    bloque = scrapertools.find_single_match(data, '>Lista de géneros<(.*?)</table>')

    matches = re.compile('<strong>(.*?)</strong>.*?href="(.*?)"', re.DOTALL).findall(bloque)

    for title, url in matches:
        if 'Series' in title: continue

        title = title.replace('&amp;', '&')

        if " (" in title: title = title.split(" (")[0]

        title = title.strip()

        if title == 'Estreno': continue
        elif title == 'Recomendada': continue

        itemlist.append(item.clone( title=title, url=url, action='list_all', text_color = 'deepskyblue' ))

    return sorted(itemlist, key=lambda it: it.title)


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div id="content">(.*?)</table>')

    matches = re.compile('<a href="(.*?)".*?title="(.*?)".*?data-lazyload="(.*?)"', re.DOTALL).findall(bloque)

    num_matches = len(matches)

    for url, title, thumb in matches[item.page * perpage:]:
        title = title.replace('&#8217;', "'")

        if " (" in title: title = title.split(" (")[0]

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > ((item.page + 1) * perpage):
            itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, action='list_all', text_color='coral' ))
            buscar_next = False

        if buscar_next:
            next_page = scrapertools.find_single_match(data, '<div class="navigation pagination">.*?<a class="page-link current".*?</a>.*?href="(.*?)".*?</div>')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = url, action = 'list_all', page = 0, text_color='coral' ))

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    if item.group == 'estrenos':
        bloque = scrapertools.find_single_match(data, '<strong>ESTRENOS DE CINE</strong>(.*?)</table>')
    else:
        bloque = scrapertools.find_single_match(data, '<strong>NOVEDADES DE PELÍCULAS</strong>(.*?)</table>')

    matches = re.compile('<a href="(.*?)".*?title="(.*?)".*?data-lazyload="(.*?)"', re.DOTALL).findall(bloque)

    num_matches = len(matches)

    for url, title, thumb in matches[item.page * perpage:]:
        title = title.replace('&#8217;', "'")

        if " (" in title: title = title.split(" (")[0]

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > ((item.page + 1) * perpage):
            itemlist.append(item.clone( title="Siguientes ...", page=item.page + 1, action='list_last', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'castellano': 'Esp', 'cas': 'Esp', 'latino': 'Lat', 'lat': 'Lat', 'vose': 'Vose', 'sub': 'Vose', 'subtitulado': 'Vose'}

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<strong>Ver película online</strong>(.*?)<strong>Reportar</strong>')

    matches = re.compile('data-lazy-src="(.*?)"', re.DOTALL).findall(bloque)

    ses = 0

    # ~ players
    for url in matches:
        ses += 1

        if '/links.cuevana.ac/' in url:
            datal = do_downloadpage(url)

            links = re.compile("go_to_player.*?'(.*?)'", re.DOTALL).findall(datal)

            downs = re.compile('<a href="(.*?)"', re.DOTALL).findall(datal)

            matchesl = links + downs

            for url in matchesl:
                if '/powvideo' in url: continue
                elif '/streamplay' in url: continue
                elif '/fembed' in url or '.fembed.' in url: continue
                elif '/1fichier' in url: continue
                elif '/uptobox' in url: continue
                elif '/filemirage' in url: continue
                elif '/filepv' in url: continue
                elif '/multiup' in url: continue
                elif '/formatearwindows' in url: continue

                lang = ''

                if "#lang=" in url:
                    lang = scrapertools.find_single_match(url, '#lang=(.*?)$').lower()
                    url = url.split("#lang=")[0]

                if "#idioma=" in url:
                    if not lang: lang = scrapertools.find_single_match(url, '#idioma=(.*?)$').lower()
                    url = url.split("#idioma=")[0]

                url = url.replace('/player.cuevana.ac/' , '/waaw.to/')

                servidor = servertools.get_server_from_url(url)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                other = servidor

                if servidor == 'various': other = servertools.corregir_other(url)
                elif servidor == 'zures': other = servertools.corregir_zures(url)

                if servidor == other: other = ''

                lng = IDIOMAS.get(lang, lang)

                if not lng: lng = '?'

                itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor,
                                      language = lng, other = other ))

            continue

        if '/powvideo' in url: continue
        elif '/streamplay' in url: continue
        elif '/fembed' in url or '.fembed.' in url: continue
        elif '/1fichier' in url: continue
        elif '/uptobox' in url: continue
        elif '/filemirage' in url: continue
        elif '/filepv' in url: continue
        elif '/multiup' in url: continue
        elif '/formatearwindows' in url: continue

        lang = ''

        if "#lang=" in url:
            lang = scrapertools.find_single_match(url, '#lang=(.*?)$').lower()
            url = url.split("#lang=")[0]

        if "#idioma=" in url:
            if not lang: lang = scrapertools.find_single_match(url, '#idioma=(.*?)$').lower()
            url = url.split("#idioma=")[0]

        url = url.replace('/player.cuevana.ac/' , '/waaw.to/')

        servidor = servertools.get_server_from_url(url)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = servidor

        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        if servidor == other: other = ''

        lng = IDIOMAS.get(lang, lang)

        if not lng: lng = '?'

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor,
                              language = lng, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    servidor = servertools.get_server_from_url(url)

    url = servertools.normalize_url(servidor, url)

    if servidor == 'directo':
        new_server = servertools.corregir_other(url).lower()
        if new_server.startswith("http"):
            if not config.get_setting('developer_mode', default=False): return itemlist
        servidor = new_server

    itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def _news(item):
    logger.info()

    item.url = host
    item.group = 'estrenos'
    item.search_type = 'movie'

    return list_last(item)


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
