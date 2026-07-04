# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://www.porntrex.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host  + 'latest-updates/' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host  + 'most-popular/' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host  + 'top-rated/' ))

    itemlist.append(item.clone( title = 'Por colección', action = 'listas', url = host + 'playlists/' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'listas', url = host + 'channels/' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'listas', url = host + 'categories/?sort_by=title' ))
    itemlist.append(item.clone( title = 'Por estrella', action = 'listas', url = host + 'models/?sort_by=avg_videos_popularity' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if "playlists" in item.url:
        patron = '<div class="video-item item  ".*?'
    else:
        patron = '<div class="video-preview-screen video-item thumb-item  ".*?'

    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)"\s*alt="([^"]+)".*?'
    patron += '<span class="quality">([^<]+)<.*?'
    patron += '</i>([^<]+)<'

    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumb, title, qlty, duration in matches:
        if not thumb.startswith("https"): thumb = "https:" + thumb

        duration = duration.strip()

        titulo = "[COLOR tan]%s[/COLOR] [COLOR darksalmon]%s[/COLOR] %s" % (duration, qlty, title)

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?href="([^"]+)"')

        if "#" in next_page:
            next_page = scrapertools.find_single_match(data, '<li class="next">.*?data-parameters="([^"]+)">')
            next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
            next_page = "?%s" % next_page

        if next_page:
            next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def listas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    data = scrapertools.find_single_match(data, '<div class="main-container">(.*?)</html>')

    if "/channels/" in item.url:
        text_color = 'violet'

        patron = '<div class="video-item   ">.*?<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?<li>([^<]+)<'

    elif "/playlists/" in item.url:
        text_color = 'pink'

        patron = '<div class="item ">.*?<a href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?<div class="totalplaylist">([^<]+)<'

    elif "/models/" in item.url:
        text_color = 'orange'

        patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?<div class="videos">([^<]+)<'

    else:
        text_color = 'moccasin'

        patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?<div class="videos">([^<]+)<'

    matches = scrapertools.find_multiple_matches(data, patron)

    for url, title, thumb, videos in matches:
        if not thumb.startswith("https"): thumb = "https:" + thumb

        if videos:
            title = title.replace('__', '').strip()

            title = title.capitalize()

        thumb = thumb.replace(' ', '%20')

        itemlist.append(item.clone(action="list_all", title = title, url = url, thumbnail = thumb,
                                   text_color = text_color, contentType = 'movie', contentTitle = title ))

    if not '/models/' in item.url: return sorted(itemlist,key=lambda x: x.title)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?href="([^"]+)"')

        if "#" in next_page:
            next_page = scrapertools.find_single_match(data, '<li class="next">.*?data-parameters="([^"]+)">')
            next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
            next_page = "?%s" % next_page

        if next_page:
            next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='listas', title='Siguientes ...', url=next_page, text_color = 'coral') )

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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    plot = ''

    bloque = scrapertools.find_single_match(data, '<div class="block-details">(.*?)</form>')

    pornstars = scrapertools.find_multiple_matches(bloque, '/models/[A-z0-9-]+/')

    for x, value in enumerate(pornstars):
        pornstars[x] = host[:-1] + value

        pornstar = ' & '.join(pornstars)

        pornstar = "[COLOR orange]%s[/COLOR]" % pornstar

        if len(pornstars) <= 3:
            lista = item.contentTitle.split()

            if "[COLOR darksalmon]" in item.title: lista.insert (5, pornstar)
            else: lista.insert (3, pornstar)
 
            item.contentTitle = ' '.join(lista)
        else:
            plot = pornstar

    itemlist.append(Item( channel = item.channel, action='play', title='', server = 'ktp', url = item.url, plot = plot, language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = "%ssearch/%s/latest-updates/" % (host, texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
