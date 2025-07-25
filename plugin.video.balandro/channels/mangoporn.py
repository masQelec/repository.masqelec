# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://mangoporn.co/'


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://mangoporn.net/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    raise_weberror = True
    if '/year/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

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

    itemlist.append(item.clone( title = '[B]Películas:[/B]', folder=False, text_color='moccasin' ))

    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'adult/genres/porn-movies/' ))

    itemlist.append(item.clone( title = ' - Tendencias', action = 'list_all', url = host + 'adult/trending/' ))

    itemlist.append(item.clone( title = '[B]Vídeos:[/B]', folder=False, text_color='moccasin' ))

    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'xxxfree/' ))

    itemlist.append(item.clone( title = ' - Tendencias', action = 'list_all', url = host + 'xxxfree/trending/' ))

    itemlist.append(item.clone( title = ' - Más valorados', action = 'list_all', url = host + 'xxxfree/ratings/' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'categorias', url = host, group = 'canales' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host, group = 'categorias'))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', url = host))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    if item.group == 'canales': text_color = 'violet'
    else: text_color = 'moccasin'

    if item.group == 'canales': data = scrapertools.find_single_match(data, '>Studios<(.*?)</ul>')
    else: data = scrapertools.find_single_match(data, '>Genres<(.*?)</ul>')

    matches = re.compile('href="(.*?)">(.*?)</a></li>', re.DOTALL).findall(data)

    for url, title in matches:
        title = title.replace('&#038;', '&').strip()

        if 'http:' in url: url = url.replace('http:', 'https:')

        itemlist.append(item.clone (action='list_all', title=title, url=url, text_color=text_color ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1999, -1):
        url = host + 'year/' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='orange' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    matches = re.compile('<article(.*?)</article>',re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if '?php' in title:
            title = scrapertools.find_single_match(match, '<h3>.*?">(.*?)</a>')
            if not title: title = scrapertools.find_single_match(match, 'alt=".*?alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('Porn Online Free', '').replace('Watch', '').strip()

        title = title.replace('&#8211;', '').replace('&#038;', '&').replace('&#8217;', "'").replace('&#8230;', '').strip()

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'data-wpfc-original-src="(.*?)"')

        time = scrapertools.find_single_match(match, "<span class='duration'>(.*?)</span>")

        titulo = title

        if time:
            time = time.replace(' hrs.', 'h').replace(' mins.', 'm').replace(' min.', 'm')

            titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)

        itemlist.append(item.clone (action='findvideos', title=titulo, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        next_page = scrapertools.find_single_match(data,'<div class="pagination">.*?<span class="current">.*?' + "<a href='(.*?)'")
        if not next_page: next_page = scrapertools.find_single_match(data,'<div class="pagination">.*?<span class="current">.*?<a href="(.*?)"')

        if next_page:
            if '/page/' in next_page:
                if not next_page.startswith('http'): next_page = host[:-1] + next_page

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

    item.url = item.url.replace('http://', 'https://')

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', '', data)

    bloque = scrapertools.find_single_match(data, '>Video Sources(.*?)</div></div></div></div')

    matches = re.compile('href="(.*?)"', re.DOTALL).findall(bloque)

    ses = 0

    for url in matches:
        ses += 1

        if url:
            if url == '#': continue

            url = url.replace('/netu.wiztube.xyz/player/embed_player.php?', '/waaw.to/watch_video.php?v=').replace('&autoplay=yes', '').strip()

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            other = ''

            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'zures': other = servertools.corregir_zures(url)

            if not servidor == 'directo':
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                      language = 'Vo', other = other.capitalize() ))

    # ~  Download
    if '>Download Sources' in data:
        bloque = scrapertools.find_single_match(data, '>Download Sources(.*?)</div></div></div></div')

        matches = re.compile('href="(.*?)"', re.DOTALL).findall(bloque)

        for url in matches:
            ses += 1

            if 'link=' in url: url = scrapertools.find_single_match(url, 'link=(.*?)$')

            if url:
                if '/rapidgator.' in url: continue
                elif '/nitro.' in url: continue
                elif '/nitroflare.' in url: continue
                elif '/katfile.' in url: continue
                elif '/turbobit.' in url: continue
                elif '/fikper.' in url: continue
                elif '/hitfile.' in url: continue
                elif '/frdl.' in url: continue

                url = url.replace('//filemoon.sx/download/', '//filemoon.sx/d/')

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                other = 'D'

                if servidor == 'various': other = servertools.corregir_other(url) + ' ' + other
                elif servidor == 'zures': other = servertools.corregir_zures(url) + ' ' + other

                if not servidor == 'directo':
                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                          language = 'Vo', other = other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    servidor = item.server

    if item.server == 'directo':
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<source src="(.*?)"')

        if not url: return itemlist

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

    itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'adult/?s=%s' % (texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
