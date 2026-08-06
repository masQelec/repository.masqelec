# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://repelishd.fit/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_repelishd_proxies', default=''):
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


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://repelishd.cam/', 'https://repelishd.city/', 'https://repelishd.run/',
                 'https://repelishd.ceo/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    if not headers: headers = {'Referer': host}

    if '/?years=' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_repelishd_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('repelishd', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if not data:
        if not '?story=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('RepelisHd', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            if hay_proxies:
                data = httptools.downloadpage_proxy('repelishd', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='repelishd', folder=False, text_color='chartreuse' ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'pelicula/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'cine/', search_type = 'movie', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    url_idio = host + 'pelicula/'

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = url_idio + '?language=castellano', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = url_idio + '?language=latino', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = url_idio + '?language=sub', text_color = 'deepskyblue' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'pelicula/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Calidad(.*?)<span>Aplicar')

    matches = scrapertools.find_multiple_matches(bloque, 'value="(.*?)"')

    for value in matches:
        title = value

        url = host + 'pelicula/?quality=' + value

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'pelicula/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Genres(.*?)<span>Aplicar')

    matches = scrapertools.find_multiple_matches(bloque, 'value="(.*?)".*?<label for=".*?">(.*?)</label>')

    for value, title in matches:
        if title == 'Cine/Estrenos': continue
        elif title == 'Series': continue

        title = title.capitalize()

        url = host + 'pelicula/?genere=' + value

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    url_anio = host + 'pelicula/?years='

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1929, -1):
        url = url_anio + str(x) + ';' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    url_pais = host + 'pelicula/'

    data = do_downloadpage(url_pais)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'País(.*?)<span>Aplicar')

    matches = scrapertools.find_multiple_matches(bloque, 'value="(.*?)"')

    for value in matches:
        title = value

        url = url_pais + '?country=' + value

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Añadido recientemente<(.*?)>Películas Destacadas<')

    matches = re.compile('<article(.*?)</article>').findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, '<a href="(.*?)"')

        title = scrapertools.find_single_match(article, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace("&#8217;", "'").replace("&amp;", '&').replace("&#039;s", "'s")

        thumb = scrapertools.find_single_match(article, '<img src="(.*?)"')
        if not 'https' in thumb: thumb = host[:-1] + thumb

        qlty = scrapertools.find_single_match(article, '<span class="quality">(.*?)</span>')

        langs = []
        if '<div class="castellano"' in article: langs.append('Esp')
        if '<div class="latino"' in article: langs.append('Lat')
        if '<div class="subtitulado"' in article: langs.append('Vose')

        year = scrapertools.find_single_match(article, '</h3> <span>(.*?)</span>')
        if not year: year = '-'

        itemlist.append(item.clone( action='findvideos', url=url, title = title, thumbnail = thumb, qualities=qlty, languages=', '.join(langs),
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?</span>.*?<a href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title='Siguientes ...', url = next_page, action='list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'castellano': 'Esp', 'español': 'Esp', 'latino': 'Lat', 'subtitulado': 'Vose', 'sub español': 'Vose'}

    lang = item.languages

    if not lang: lang = '?'

    ses = 0

    if item.datos:
        matches = re.compile('data-link="(.*?)"').findall(item.datos)

        for url in matches:
            ses += 1

            if url.startswith('/player/'): continue

            elif '/verhdlink.' in url: continue

            if not 'http' in url: url = 'https:' + url

            servidor = servertools.get_server_from_url(url)

            url = servertools.normalize_url(servidor, url)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language=lang, other=other ))

            continue

        if itemlist: return itemlist

        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
        return

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    enlace = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

    if enlace:
       datae = do_downloadpage(enlace)
       datae = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', datae)

       actives = scrapertools.find_multiple_matches(datae, '<ul class="_player-mirrors (.*?)</ul>')

       for active in actives:
           ses += 1

           if 'castellano' in active or 'español' in active: lang = 'Esp'
           elif 'latino' in active: lang = 'Lat'
           elif 'subtitulado' in active: lang = 'Vose'
           else: lang = '?'

           urls = scrapertools.find_multiple_matches(active, 'data-link="(.*?)"')

           for url in urls:
               if not url: continue

               ses += 1

               if '/verhdlink.' in url: continue

               if not 'http' in url: url = 'https:' + url

               servidor = servertools.get_server_from_url(url)

               url = servertools.normalize_url(servidor, url)

               other = ''
               if servidor == 'various': other = servertools.corregir_other(url)
               elif servidor == 'zures': other = servertools.corregir_zures(url)

               itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language=lang, other=other ))

    if not itemlist:
        if '/vimeus.' in item.url:
            new_url = item.url

            datav = do_downloadpage(new_url)

            embed = scrapertools.find_single_match(datav, '"embeds":(.*?)</script>')

            links = scrapertools.find_multiple_matches(embed, '"url":"(.*?)"')

            for link in links:
                ses += 1

                url = link

                servidor = servertools.get_server_from_url(url)

                if servidor == 'directo': continue

                other = ''

                if servidor == 'various': other = servertools.corregir_other(url)
                elif servidor == 'zures': other = servertools.corregir_zures(url)

                itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url,
                                      language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def _news(item):
    logger.info()

    item.url = host + 'cine/'
    item.search_type = 'movie'

    return list_all(item)


def search(item, texto):
    logger.info()
    try:
        url = host

        if item.search_type == 'movie': url = host + 'pelicula/'

        item.url = url + '?story=' + texto.replace(" ", "+") + '&do=search&subaction=search'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
