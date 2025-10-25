# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools


host = 'https://www.porngo.com/'


perpage = 20


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

    itemlist.append(item.clone( title = '[B]BigWank[/B]', action = 'mainlist_submenu', ch = 'bigwank', host = 'https://www.bigwank.tv/', thumbnail = 'https://i.postimg.cc/N0DNJB4D/bigwank.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]FapGuru[/B]', action = 'mainlist_submenu', ch = 'fapguru', host = 'https://www.fapguru.com/', thumbnail = 'https://i.postimg.cc/dQgpbQ2t/fapguru.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]PornCake[/B]', action = 'mainlist_submenu', ch = 'porncake', host = 'https://www.porncake.com/', thumbnail = 'https://i.postimg.cc/QxWS1pWj/porncake.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]PornGo[/B]', action = 'mainlist_submenu', ch = 'porngo', host = 'https://www.porngo.com/', thumbnail = 'https://i.postimg.cc/p9dFtR2C/porngo.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]PornPapa[/B]', action = 'mainlist_submenu', ch = 'pornpapa', host = 'https://www.pornpapa.com/', thumbnail = 'https://i.postimg.cc/Y0cry05W/pornpapa.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]PornTry[/B]', action = 'mainlist_submenu', ch = 'porntry', host = 'https://www.porntry.com/', thumbnail = 'https://i.postimg.cc/jSdvDGKJ/porntry.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]TitsHub[/B]', action = 'mainlist_submenu', ch = 'titshub', host = 'https://www.titshub.com/', thumbnail = 'https://i.postimg.cc/T3GqZBh4/titshub.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]VeryFreePorn[/B]', action = 'mainlist_submenu', ch = 'veryfreeporn', host = 'https://www.veryfreeporn.com/', thumbnail = 'https://i.postimg.cc/QNmTFVM0/veryfreeporn.png', text_color = 'orange' ))

    itemlist.append(item.clone( title = '[B]XxxFiles[/B]', action = 'mainlist_submenu', ch = 'xxxfiles', host = 'https://www.xxxfiles.com/', thumbnail = 'https://i.postimg.cc/ry0jBvN8/xxxfiles.png', text_color = 'orange' ))

    return itemlist


def mainlist_submenu(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( title = 'Buscar vídeo ...', chanel = item.chanel, action = 'search', url = item.host, search_type = 'movie', search_video = 'adult', text_color = 'orange' ))

    itemlist.append(item.clone( title = 'Catálogo', chanel = item.chanel, action = 'list_all', url = item.host + 'latest-updates/1/' ))

    itemlist.append(item.clone( title = 'Más populares', chanel = item.chanel, action = 'list_all', url = item.host + 'most-popular/1/' ))
    itemlist.append(item.clone( title = 'Más valorados', chanel = item.chanel, action = 'list_all', url = item.host + 'top-rated/1/' ))

    itemlist.append(item.clone( title = 'Por canal', chanel = item.chanel, action = 'canales', url = item.host + 'sites/' ))

    itemlist.append(item.clone( title = 'Por categoría', chanel = item.chanel, action = 'categorias', url = item.host + 'categories/' ))

    itemlist.append(item.clone( title = 'Por estrella', chanel = item.chanel, action = 'pornstars', url = item.host + 'models/most-viewed/' ))

    return itemlist


def canales(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div data-ajax>(.*?)<nav class="nav">')

    matches = re.compile('<h2 class="headline__title">.*?<span>(.*?)</span>.*?<img src="(.*?)".*?<div class="block-related__bottom">.*?<a href="(.*?)"', re.DOTALL).findall(bloque)

    for title, thumb, url in matches:
        title = title.capitalize()

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail = thumb, text_color = 'violet' ))

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination__item"><span class="pagination__link pagination__link_disabled">.*?href="(.*?)"')

            if next_page:
                next_page = item.host[:-1] + next_page

                itemlist.append(item.clone (action='canales', title='Siguientes ...', url = next_page, text_color = 'coral' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="letter-section">(.*?)</div></div></div>')

    matches = re.compile('<a href="(.*?)".*?<span>(.*?)</span>', re.DOTALL).findall(bloque)

    for url, title in matches:
        itemlist.append(item.clone (action='list_all', title=title, url=url, text_color='moccasin' ))

    return itemlist


def pornstars(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '<div data-ajax>(.*?)<nav class="nav">')

    matches = re.compile('<div class="thumb">(.*?)</div>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        logger.info("check-00-dude-thumb: %s" % thumb)

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail = thumb, text_color = 'violet' ))

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination__item"><span class="pagination__link pagination__link_disabled">.*?href="(.*?)"')

            if next_page:
                next_page = item.host[:-1] + next_page

                itemlist.append(item.clone (action='pornstars', title='Siguientes ...', url = next_page, text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    matches = re.compile('<div class="thumb item(.*?)</div></div></div></div>', re.DOTALL).findall(data)

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        duration = scrapertools.find_single_match(match, '<span class="thumb__duration">(.*?)</span>')

        duration = duration.replace('&nbsp;', '').strip()

        title = "[COLOR tan]%s[/COLOR] %s" % (duration, title)

        itemlist.append(item.clone (action='findvideos', title=title, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults' ))

        if len(itemlist) >= perpage: break

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            if '<div class="pagination">' in data:
                next_page = scrapertools.find_single_match(data, '<div class="pagination__item"><span class="pagination__link pagination__link_disabled">.*?href="(.*?)"')

                if next_page:
                    next_page = item.host[:-1] + next_page

                    itemlist.append(item.clone (action='list_all', title='Siguientes ...', page = 0, url = next_page, text_color = 'coral' ))

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

    bloque = scrapertools.find_single_match(str(data), "<video id='video-(.*?)</video>")

    matches = scrapertools.find_multiple_matches(bloque, "<source src='(.*?)'.*?" + 'label="(.*?)"')

    if not matches:
        platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Sin enlaces Disponibles[/B][/COLOR]')
        return

    for url, qlty in matches:
        itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server='directo', quality = qlty, language = 'Vo' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        if not item.host:
            item.ch = 'porngo'
            item.host = host

        item.url = item.host + 'search/' + texto.replace(" ", "+") + '/1/'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
