# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.tubepelis.com/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_tubepelis_proxies', default=''):
        tit = '[COLOR %s][B]Quitar los proxies del canal[/B][/COLOR]' % color_list_proxies
        context.append({'title': tit, 'channel': item.channel, 'action': 'quitar_proxies'})

    tit = '[COLOR %s]Ajustes categoría proxies[/COLOR]' % color_exec
    context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = '[B]Configurar proxies a usar[/B] ...', action = 'configurar_proxies', folder=False, context=context, plot=plot, text_color='red' )

def quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)
    return True

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None):
    hay_proxies = False
    if config.get_setting('channel_tubepelis_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('tubepelis', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/buscar/?q=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('TubePelis', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('tubepelis', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not 'buscar?p=1&q=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='tubepelis', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_tubepelis', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('tubepelis') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host, search_type = 'movie' ))

    url = host + 'pelicula/ultimas-peliculas/'

    itemlist.append(item.clone( title = 'Últimas', action = 'list_all', url = url, grp = url, search_type = 'movie', text_color='cyan' ))

    url = host + 'pelicula/peliculas-mas-vistas/'

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = url, grp = url, search_type = 'movie' ))

    url = host + 'pelicula/peliculas-mas-votadas/'

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = url, grp = url, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Selecciona tu categoria<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if config.get_setting('descartar_xxx', default=False):
            if title == 'Eroticas +18': continue

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, grp = url, text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '>Resultados para' in data:
        bloque = scrapertools.find_single_match(data, '>Resultados para(.*?)</div> </div> </div>')
    else:
        bloque = scrapertools.find_single_match(data, '<center>(.*?)</li></ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<li class="peli_bx br1px brdr10px ico_a">(.*?)</div></div></div>')
    if not matches: matches = scrapertools.find_multiple_matches(bloque, '<li class="peli_bx br1px brdr10px ico_a">(.*?)</div> </div>')
    if not matches: matches = scrapertools.find_multiple_matches(bloque, '<li class="peli_bx br1px brdr10px ico_a">(.*?)</div></div></div>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#039;s', "'s")

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<ul class="nav bgdeg4 bold brdr10px bxshd2 clr fs18px lnht30px liasbrdr10px lstinl pd10px txt_cen white">' in data:
            next_page = scrapertools.find_single_match(data, '<ul class="nav bgdeg4 bold brdr10px bxshd2 clr fs18px lnht30px liasbrdr10px lstinl pd10px txt_cen white">.*?</b>.*?<a href="(.*?)".*?</ul>')

            if next_page:
                if '?page=' in next_page or '&page=' in next_page:
                    if not item.grp:
                        next_page = host + next_page
                    else:
                        next_page = item.grp + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<iframe src="(.*?)"')

    ses = 0

    for url in matches:
        ses += 1

        if '.mystream.' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = servidor

        if servidor == 'various': other = servertools.corregir_other(url)

        if servidor == other: other = ''

        elif not servidor == 'directo':
           if not servidor == 'various': other = ''

        if servidor == 'directo':
            if not config.get_setting('developer_mode', default=False): continue
            other = url.split("/")[2]
            other = other.replace('https:', '').strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = 'Lat', other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
       url = host + 'buscar/?q=' + texto.replace(" ", "+")
       item.url = url
       item.grp = host + 'buscar/'
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

