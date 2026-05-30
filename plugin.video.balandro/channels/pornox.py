# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://pornox.hu/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host  + 'en/search?sort_by=post_date&from_videos=1' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host  + 'en/search?sort_by=most_commented&from_videos=1' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host  + 'en/search?sort_by=rating_month&from_videos=1' ))
    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host  + 'en/search?sort_by=video_viewed_month&from_videos=1' ))
    itemlist.append(item.clone( title = 'Más candentes', action = 'list_all', url = host  + 'en/search?sort_by=most_favourited&from_videos=1' ))

    itemlist.append(item.clone( title = 'Long play', action = 'list_all', url = host  + 'en/search?sort_by=duration&from_videos=1' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'listas', url = host + 'en/szexcsatorna/1/' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'listas', url = host + 'en/szex-kategoriak/' ))

    itemlist.append(item.clone( title = 'Por estrella', action = 'listas', url = host + 'en/pornosztarok/1/' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="list-videos">(.*?)</script>')

    if '/en/?q=' in item.url: bloque = scrapertools.find_single_match(data, '<div class="list-videos">(.*?)<div id="list_albums_albums_list_search_result">')

    patron = '<div class="item">.*?<a href="(.*?)".*?title="(.*?)".*?src="(.*?)"(.*?)</div></a></div>'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, title, thumb, resto in matches:
        duration = scrapertools.find_single_match(resto, '<span class="is-hd">(.*?)</span>').strip()

        titulo = "[COLOR tan]%s[/COLOR] %s" % (duration, title)

        thumb = thumb.replace(' ', '%20').strip()

        thumb = thumb.replace("336x189", "320x180")

        _hd = False

        if '<span class="is-hd' in resto: _hd = True

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, _hd = _hd,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="load-more"(.*?)</div>')

        if not bloque:
            bloque = scrapertools.find_single_match(data, '<li class="page">(.*?)</div>')

        next_page = scrapertools.find_single_match(bloque, '<a href="(.*?)"')

        ant_page = ''
        sig_page = ''

        if "#" in next_page:
            next_page = ''

            if item._listas: sig_page = 1

            elif '&from_videos=' in item.url:
                  ant_page = scrapertools.find_single_match(item.url, '&from_videos=(.*?)$')
            elif '&from=' in item.url:
                  ant_page = scrapertools.find_single_match(item.url, '&from=(.*?)$')
            elif '/en/szex-kategoriak/' in item.url:
                  ant_page = scrapertools.find_single_match(item.url, 'en/szex-kategoriak/(.*?)/')
            elif '/en/szexcsatorna/' in item.url:
                  ant_page = scrapertools.find_single_match(item.url, '/en/szexcsatorna/(.*?)/')
            elif '/en/pornosztarok/' in item.url:
                 ant_page = scrapertools.find_single_match(item.url, '/en/pornosztarok/(.*?)/')

            if ant_page:
                try:
                   sig_page = int(ant_page)
                   sig_page += 1
                except:
                   pass

            if sig_page:
                if item._listas:
                    next_page = item.url + 'search?sort_by=post_date&from_videos=' + str(sig_page)

                elif '&from_videos=' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '(.*?)&from_videos=')

                    next_page = next_page + '&from_videos=' + str(sig_page)

                elif '&from=' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '(.*?)&from=')

                    next_page = next_page + '&from=' + str(sig_page)

                elif '/en/szex-kategoriak/' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '/en/szex-kategoriak/(.*?)/')

                    next_page = '/en/szex-kategoriak/' + next_page + str(sig_page) + '/'

                elif '/en/szexcsatorna/' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '/en/szexcsatorna/(.*?)/')

                    next_page = '/en/szexcsatorna/' + next_page + str(sig_page) + '/'

                elif '/en/pornosztarok/' in item.url:
                    next_page = scrapertools.find_single_match(item.url, '/en/pornosztarok/(.*?)/')

                    next_page = '/en/pornosztarok/' + next_page + str(sig_page) + '/'

        if next_page:
            if not host in next_page: next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, _listas = False, text_color = 'coral') )

    return itemlist


def listas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '/en/szex-kategoriak/' in item.url: text_color = 'moccasin'
    elif '/en/szexcsatorna/' in item.url: text_color = 'violet'
    else: text_color = 'orange'

    bloque = scrapertools.find_single_match(data, '<div class="main-container">(.*?)</html>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<div class="box models-list">(.*?)</html>')

    patron = '<div class="item">.*?<a href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)"'

    if '/en/szex-kategoriak/' in item.url or '/en/pornosztarok/' in item.url:
        patron = '<a class="item".*?href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)"'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, title, thumb in matches:
        title = title.capitalize()

        if '/en/szex-kategoriak/' in item.url:
            title = title.replace('porn', '').strip()

        thumb = thumb.replace(' ', '%20').strip()

        _listas = False

        if '/en/szex-kategoriak/' in item.url or '/en/pornosztarok/' in item.url: _listas = True

        itemlist.append(item.clone(action="list_all", title = title, url = url, thumbnail = thumb, _listas = _listas,
                                   text_color = text_color, contentType = 'movie', contentTitle = title ))

    if '/en/szex-kategoriak/' in item.url: return sorted(itemlist,key=lambda x: x.title)

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="load-more"(.*?)</div>')

        next_page = scrapertools.find_single_match(bloque, '<a href="(.*?)"')

        ant_page = ''
        sig_page = ''

        if '/en/szex-kategoriak/' in item.url:
            ant_page = scrapertools.find_single_match(item.url, '/en/szex-kategoriak/(.*?)/')
        elif '/en/szexcsatorna/' in item.url:
            ant_page = scrapertools.find_single_match(item.url, '/en/szexcsatorna/(.*?)/')
        elif '/en/pornosztarok/' in item.url:
            ant_page = scrapertools.find_single_match(item.url, '/en/pornosztarok/(.*?)/')

        if ant_page:
            try:
               sig_page = int(ant_page)
               sig_page += 1
            except:
               sig_page = ''

        if sig_page:
            if '/en/szex-kategoriak/' in item.url:
                next_page = scrapertools.find_single_match(item.url, '(.*?)/en/szex-kategoriak/')

                next_page = next_page + '/en/szex-kategoriak/' + str(sig_page) + '/'

            elif '/en/szexcsatorna/' in item.url:
                next_page = scrapertools.find_single_match(item.url, '(.*?)/en/szexcsatorna/')

                next_page = next_page + '/en/szexcsatorna/' + str(sig_page) + '/'

            elif '/en/pornosztarok/' in item.url:
                next_page = scrapertools.find_single_match(item.url, '(.*?)/en/pornosztarok/')

                next_page = next_page + '/en/pornosztarok/' + str(sig_page) + '/'

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

    if bloque:
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

    else:
        url = scrapertools.find_single_match(data, 'data-preview="(.*?)"')

        if url:
            itemlist.append(Item( channel = item.channel, action='play', title='', server = 'directo', url = url, language = 'Vo', other = 'tráiler') )

        url = scrapertools.find_single_match(data, '<source src="(.*?)"')

        if url:
            itemlist.append(Item( channel = item.channel, action='play', title='', server = 'directo', url = url, language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = "%sen/?q=%s&sort_by=post_date&from_videos=1" % (host, texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
