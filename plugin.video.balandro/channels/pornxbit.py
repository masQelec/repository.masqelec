# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://www.pornxbit.com'


def do_downloadpage(url, post=None, headers=None):
    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/?s=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('PornXbit', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not '/?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', search_video = 'adult', text_color = 'orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host  + '/porn-videos/?filter=latest' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host  + '/full-movie/' ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host  + '/porn-videos/?filter=most-viewed' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + '/categories/' ))

    itemlist.append(item.clone( title = 'Por estrella', action = 'pornstars', url = host + '/actors/' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail=thumb, text_color = 'moccasin' ))

    return itemlist


def pornstars(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail=thumb, tipo = 'pornstars', text_color='orange' ))

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<a class="current">.*?<a href="(.*?)".*?</li>')
            if not next_page: next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<a class="current">.*?' + "<a href='(.*?)'" + '.*?</li>')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone (action='pornstars', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        title = title.replace('&#8211;', '-').strip()

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        time = scrapertools.find_single_match(match, '<span class="duration">.*?</i>(.*?)</span>').strip()

        if time:
            titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)
        else:
            titulo = title

        itemlist.append(item.clone (action='findvideos', title=titulo, url=url, thumbnail=thumb,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<a class="current">.*?<a href="(.*?)".*?</li>')
            if not next_page: next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<a class="current">.*?' + "<a href='(.*?)'" + '.*?</li>')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Download / Stream Links<(.*?)</div></div>')

    matches = scrapertools.find_multiple_matches(bloque, '<a target="_blank".*?href="(.*?)"')

    ses = 0

    for url in matches:
        ses += 1

        if '/rapidgator.' in url: continue
        elif '/uploaded.' in url: continue
        elif '.filefactory.' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server = servidor, language = 'Vo', other = other) )

    # ~ Iframe
    if not itemlist:
        url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)".*?</iframe>')

        if url:
            ses += 1

            if '/aso.' in url: url = ''

            if url:
                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                if servertools.is_server_available(url):
                    if not servertools.is_server_enabled(url): url = ''
                else:
                    if not config.get_setting('developer_mode', default=False): url = ''

                if url:
                    url = servertools.normalize_url(servidor, url)

                    other = ''
                    if servidor == 'various': other = servertools.corregir_other(url)
                    elif servidor == 'zures': other = servertools.corregir_zures(url)

                    if not servidor == 'directo':
                        itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server = servidor, language = 'Vo', other = other) )

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play2(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.server == 'directo':
        data = do_downloadpage(url)

        if not data or '404 Not Found' in data:
            return 'Archivo [COLOR red]Inaccesible[/COLOR]'

        vid = scrapertools.find_single_match(data, '"url":"(.*?)"')

        if vid:
            try: vid = base64.b64decode(vid).decode('utf-8')
            except: vid = ''

            if vid: url = 'https://www.dailymotion.com/video/' + vid

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + '/?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
