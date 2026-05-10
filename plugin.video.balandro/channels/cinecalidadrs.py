# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cinecalidad.rs/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_cinecalidadrs_proxies', default=''):
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


def do_downloadpage(url, post=None, headers=None):
    hay_proxies = False
    if config.get_setting('channel_cinecalidadrs_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('cinecalidadrs', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('CineCalidadRs', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('cinecalidadrs', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='cinecalidadrs', folder=False, text_color='chartreuse' ))

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

    itemlist.append(item.clone( title = '[B]En castellano:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'espana/', search_type = 'movie' ))

    itemlist.append(item.clone( title = '[B]En latino:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - En [COLOR moccasin]4K[/COLOR]', action = 'list_all', url = host + 'peliculas/4k-ultra-hd/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action='anios', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<ul id=menu-menu class=menu>(.*?)</ul>')

    matches = re.compile('<a href=(.*?)>(.*?)</a>').findall(bloque)

    for url, title in matches:
        if '#' in url: continue

        elif title == '4K UHD': continue
        elif title == 'Películas por año': continue

        url = url.strip()

        if not host in url:
            url = host[:-1] + url

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1969, -1):
        url = host + 'peliculas/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, 'post_box">(.*?)</a></div>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        url = scrapertools.find_single_match(match, '<a href=(.*?)>').strip()

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src=(.*?)class=').strip()

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#039;s', "'s").replace('&#038;', '&').replace('&amp;', '&')

        if '/espana/' in item.url:
           if not '?castellano=sp' in item.url: url = url + '?castellano=sp'

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class=wp-pagenavi role=navigation>' in data:
            next_page = scrapertools.find_single_match(data, '<div class=wp-pagenavi role=navigation>.*?class=current>.*?href=(.*?)>').strip()

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title='Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'latino': 'Lat', 'castellano': 'Esp', 'subtitulado': 'Vose'}

    lang = 'Lat'

    if '?castellano=sp' in item.url: lang = 'Esp'

    data = do_downloadpage(item.url)

    ses = 0

    if '>Ver' in data or '>VER' in data:
        if '>Descargar' in data in data: _final = '>Descargar'
        elif '>DESCARGAR' in data: _final = '>DESCARGAR'
        else: _final = '</aside>'

        bloque = scrapertools.find_single_match(data, '>Ver(.*?)' + _final)
        if not bloque: bloque = scrapertools.find_single_match(data, '>VER(.*?)' + _final)

        matches = scrapertools.find_multiple_matches(bloque, 'data=(.*?)>.*?<li>(.*?)</li>')

        for data_url, servidor in matches:
            ses += 1

            servidor = servidor.lower().strip()

            if servidor == 'trailer' or servidor == 'youtube': continue

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            url = ''

            if servidor == 'filemoon': url = 'https://filemoon.sx/d/' + data_url
            elif servidor == 'doodstream': url = 'https://doodstream.com/d/' + data_url
            elif servidor == 'voe': url = 'https://voe.sx/e/' + data_url
            elif servidor == 'mega': url = 'https://mega.nz/file/' + data_url

            if not url:
                if config.get_setting('developer_mode', default=False):
                    platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]Comprobar Enlaces[/B][/COLOR]')
                    continue

            other = ''
            if servidor == 'filemoon':
                other = servidor
                servidor = 'various'

            if url:
                itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', url = url,
				                      language = lang, other = other.capitalize() ))

    # ~ Descargas  No se tratan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

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
