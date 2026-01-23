# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://xxxi.porn/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host  + 'search?sort_by=post_date&from_videos=1' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host  + 'search?sort_by=most_commented&from_videos=1' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host  + 'search?sort_by=rating_month&from_videos=1' ))
    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host  + 'search?sort_by=video_viewed_month&from_videos=1' ))
    itemlist.append(item.clone( title = 'Más candentes', action = 'list_all', url = host  + 'search?sort_by=most_favourited&from_videos=1' ))

    itemlist.append(item.clone( title = 'Long play', action = 'list_all', url = host  + 'search?sort_by=duration&from_videos=1' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'listas', url = host + 'sites?sort_by=total_videos&from=1' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'listas', url = host + 'porno-cats?sort_by=title' ))

    itemlist.append(item.clone( title = 'Por estrella', action = 'listas', url = host + 'porno-models?sort_by=total_videos&from=1' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="list-videos">(.*?)</script>')

    patron = '<div class="item ">.*?<a href="(.*?)".*?title="(.*?)".*?data-original="(.*?)"(.*?)</div> </div> </a>'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, title, thumb, resto in matches:
        duration = scrapertools.find_single_match(resto, '<div class="duration">(.*?)</div>').strip()

        titulo = "[COLOR tan]%s[/COLOR] %s" % (duration, title)

        thumb = thumb.replace(' ', '%20').strip()

        _hd = False

        if '<span class="hd-label">' in resto: _hd = True

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, _hd = _hd,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="pagination"(.*?)</ul>')

        next_page = scrapertools.find_single_match(bloque, '<li class="page-current">.*?</li>.*?<a href="(.*?)"')

        ant_page = ''
        sig_page = ''

        if "#" in next_page:
            next_page = ''

            if '&from_videos=' in item.url:
                ant_page = scrapertools.find_single_match(item.url, '&from_videos=(.*?)$')
            elif '&from=' in item.url:
                ant_page = scrapertools.find_single_match(item.url, '&from=(.*?)$')
            elif '/sites' in item.url:
                ant_page = scrapertools.find_single_match(item.url, '/sites(.*?)/')
            elif '/porno-models' in item.url:
                ant_page = scrapertools.find_single_match(item.url, '/porno-models(.*?)/')

            if ant_page:
                try:
                   sig_page = int(ant_page)
                   sig_page += 1
                except:
                   pass

            if sig_page:
                if '&from_videos=' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '(.*?)&from_videos=')

                    next_page = next_page + '&from_videos=' + str(sig_page)

                elif '&from=' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '(.*?)&from=')

                    next_page = next_page + '&from=' + str(sig_page)

                elif '/sites' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '/sites(.*?)/')

                    next_page = '/sites' + next_page + '?' + str(sig_page) + '/'

                elif '/porno-models' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '/porno-models(.*?)/')

                    next_page = '/porno-models' + next_page + '?' + str(sig_page) + '/'

        if next_page:
            if not host in next_page: next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def listas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if '/porno-cats' in item.url: text_color = 'moccasin'
    elif '/sites' in item.url: text_color = 'violet'
    else: text_color = 'orange'

    bloque = scrapertools.find_single_match(data, '<div class="main-container">(.*?)</html>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<div class="box models-list">(.*?)</html>')

    patron = '<a class="item".*?href="([^"]+)".*?title="([^"]+)".*?data-original="([^"]+)"'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, title, thumb in matches:
        title = title.capitalize()

        thumb = thumb.replace(' ', '%20').strip()

        itemlist.append(item.clone(action="list_all", title = title, url = url, thumbnail = thumb,
                                   text_color = text_color, contentType = 'movie', contentTitle = title ))

    if not '/porno-models' in item.url: return sorted(itemlist,key=lambda x: x.title)

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="pagination"(.*?)</ul>')

        next_page = scrapertools.find_single_match(bloque, '<li class="page-current">.*?</li>.*?<a href="(.*?)"')

        ant_page = ''
        sig_page = ''

        if '/sites' in item.url:
            ant_page = scrapertools.find_single_match(item.url, '/sites(.*?)/')
        elif '/porno-models' in item.url:
            ant_page = scrapertools.find_single_match(item.url, '/porno-models(.*?)/')

        if ant_page:
            try:
               sig_page = int(ant_page)
               sig_page += 1
            except:
               sig_page = ''

        if sig_page:
            if '/sites' in item.url:
                next_page = scrapertools.find_single_match(item.url, '(.*?)/sites')

                next_page = next_page + '/sites' + '?' + str(sig_page) + '/'

            elif '/porno-models' in item.url:
                next_page = scrapertools.find_single_match(item.url, '(.*?)/porno-models')

                next_page = next_page + '/porno-models' + '?' + str(sig_page) + '/'

        if next_page:
            if not host in next_page: next_page = host[:-1] + next_page

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

    bloque = scrapertools.find_single_match(data, '<div class="info-block"(.*?)</form>')

    pornstars = scrapertools.find_multiple_matches(bloque, '/(?:pornstars|models|model|pornosztarok)/[A-z0-9-]+(?:/|)')

    for x, value in enumerate(pornstars):
        pornstars[x] = host[:-1] + value

        pornstar = ' & '.join(pornstars)

        pornstar = "[COLOR orange]%s[/COLOR]" % pornstar

        lista = item.contentTitle.split()

        if item._hd:
            lista.insert (2, pornstar)
        else:
            lista.insert (1, pornstar)

        item.contentTitle = ' '.join(lista)

    itemlist.append(Item( channel = item.channel, action='play', title='', server = 'ktp', url = item.url, language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = "%ssearch/%s?sort_by=post_date&from_videos=1" % (host, texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
