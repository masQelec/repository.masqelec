# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://repelis.re/'


api = 'wp-json/cuevana/v1/'


useragent = httptools.get_user_agent()


perpage = 25


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_repelisre_proxies', default=''):
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


def do_downloadpage(url, ref, post=None, headers=None):
    if not host in url:
        if ref.startswith('/'): ref = host[:-1] + ref
        else: ref = host + ref

        url = host + api + url

        if '/page/' in ref: page = scrapertools.find_single_match(ref, '/page/(.*?)$')
        else: page = '1'

        headers = dict()
        headers["User-Agent"] = useragent

        headers["Accept"] = "application/json, text/plain, */*"
        headers["Accept-Language"] = "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"
        headers["paged"] = str(page)
        headers["limit"] = "25" 
        headers["Sec-Fetch-Dest"] = "empty"
        headers["Sec-Fetch-Mode"] = "cors"
        headers["Sec-Fetch-Site"] = "same-origin"

        headers["Referer"] = ref

    hay_proxies = False
    if config.get_setting('channel_repelisre_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('repelisre', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not 'recherche?q=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('RePelisRe', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('repelisre', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='repelisre', folder=False, text_color='chartreuse' ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', ref = '/peliculas-online' ))

    itemlist.append(item.clone( title = 'Últimos Estrenos', action = 'list_all', ref = '/peliculas-estrenos', group = 'news', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_mas', url = 'topdia?paged=movies', ref = '/peliculas-tendencias/dia' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_mas', url = 'topsemana?paged=movies', ref = '/peliculas-tendencias/semana' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all',
                                url = 'taxonomy?tax-data={"name":"language","term":"mx"}', ref = '/peliculas/mx/', group = 'langs', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Latino', action = 'list_all',
                                url = 'taxonomy?tax-data={"name":"language","term":"en"}', ref = '/peliculas/en/', group = 'langs', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all',
                                url = 'taxonomy?tax-data={"name":"language","term":"es"}', ref = '/peliculas/es/', group = 'langs', text_color = 'moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage('menu', item.ref)

    bloque = scrapertools.find_single_match(str(data), '"Generos"(.*?)$')

    matches = scrapertools.find_multiple_matches(str(bloque), '"name":"(.*?)".*?"link":"(.*?)"')

    for title, ref in matches:
        title = clean_title(title)

        ref = ref.replace('\\/', '/')

        genre = scrapertools.find_single_match(ref, '/genero-de-la-pelicula/(.*?)/')

        url = 'taxonomy?tax-data={"name":"genre","term":"' + genre + '"}'

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, ref = ref, group = 'genres', text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    if item.group == 'news': item.url = 'estrenos?paged=' + str(item.page) + '&ptype=movies&limit=25&lang=any'

    elif item.group == 'langs': item.url = item.url + '&paged=' + str(item.page) + '&ptype=movies,series&limit=25&lang=any'

    elif item.group == 'genres': item.url = item.url + '&paged=' + str(item.page) + '&ptype=movies,series&limit=25&lang=any'

    if not item.url: item.url = 'moviespage?paged=' + str(item.page) + '&limit=25'

    data = do_downloadpage(item.url, item.ref)

    data = data.replace('"_id":', '"_id":"')

    matches = scrapertools.find_multiple_matches(str(data), '"link":(.*?)"genres"')

    for match in matches:
        ref = scrapertools.find_single_match(str(match), '.*?"(.*?)"')
        _id = scrapertools.find_single_match(str(match), '_id":"(.*?)"')

        _id = _id.replace(',', '').strip()

        if not ref or not _id: continue

        if not '/pelicula' in ref: continue

        title = scrapertools.find_single_match(str(match), '"title":"(.*?)"')

        title = clean_title(title)

        title = title.replace('&#8217;', "'").replace('&amp;', '&').replace('&#8211;', '')

        thumb = scrapertools.find_single_match(str(match), '"cover":"(.*?)"')

        thumb = thumb.replace('\\/', '/')

        thumb = host[:-1] + thumb

        plot = scrapertools.find_single_match(str(match), '"desc":"(.*?)"')

        plot = clean_title(plot)

        year = scrapertools.find_single_match(str(match), '"release":"(.*?)"')
        year = scrapertools.find_single_match(year, '(.*?)-')
        if not year: year = '-'

        ref = ref.replace('\\/', '/')

        if not host in ref: ref = host[:-1] + ref

        itemlist.append(item.clone( action='findvideos', url = 'player/', id = _id, ref = ref, title = title, thumbnail = thumb,
                                    contentType='movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if item.group == 'news': return itemlist
    elif 'search?' in item.url:  return itemlist

    if itemlist:
        tot_pages = scrapertools.find_single_match(str(data), '"total_pages":(.*?)$')

        tot_pages = tot_pages.replace('}', '').strip()

        if tot_pages:
            tot_pages = int(tot_pages)
            next_page = item.page + 1

            if next_page <= tot_pages:
                if 'moviespage' in item.url: url = ''
                else: url = item.url

                if not '/page/' in item.ref:
                    if not item.ref.endswith('/'): ref = item.ref + '/page/' + str(next_page) + '/'
                    else: ref = item.ref + 'page/' + str(next_page) + '/'
                else:
                    ref = scrapertools.find_single_match(item.ref, '(.*?)/page/')
                    if not ref.endswith('/'): ref = ref + '/page/' + str(next_page) + '/'
                    else: ref = ref + 'page/' + str(next_page) + '/'

                itemlist.append(item.clone( title='Siguientes ...', url = url, ref = ref, page = next_page, action='list_all', text_color='coral' ))

    return itemlist


def list_mas(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url, item.ref)

    data = data.replace('"_id":', '"_id":"')

    matches = scrapertools.find_multiple_matches(str(data), '"link":(.*?)"genres"')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        ref = scrapertools.find_single_match(str(match), '.*?"(.*?)"')
        _id = scrapertools.find_single_match(str(match), '_id":"(.*?)"')

        _id = _id.replace(',', '').strip()

        if not ref or not _id: continue

        if not '/pelicula' in ref: continue

        title = scrapertools.find_single_match(str(match), '"title":"(.*?)"')

        title = clean_title(title)

        title = title.replace('&#8217;', "'").replace('&amp;', '&').replace('&#8211;', '')

        thumb = scrapertools.find_single_match(str(match), '"cover":"(.*?)"')

        thumb = thumb.replace('\\/', '/')

        thumb = host[:-1] + thumb

        plot = scrapertools.find_single_match(str(match), '"desc":"(.*?)"')

        plot = clean_title(plot)

        year = scrapertools.find_single_match(str(match), '"release":"(.*?)"')
        year = scrapertools.find_single_match(year, '(.*?)-')
        if not year: year = '-'

        ref = ref.replace('\\/', '/')

        if not host in ref: ref = host[:-1] + ref

        itemlist.append(item.clone( action='findvideos', url = 'player/', id = _id, ref = ref, title = title, thumbnail = thumb,
                                    contentType='movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page = item.page + 1, action='list_mas', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url + item.id, item.ref)

    matches = scrapertools.find_multiple_matches(str(data), '"audio":"(.*?)"server"')

    ses = 0

    for option in matches:
        ses += 1

        lang = scrapertools.find_single_match(str(option), '(.*?)"')

        if lang == 'CASTELLANO': lang = 'Esp'
        elif lang == 'LATINO': lang = 'Lat'
        elif lang == 'SUBTITULADO': lang = 'Vose'
        elif lang == 'INGLES': lang = 'Vose'

        qlty = scrapertools.find_single_match(str(option), '"quality":"(.*?)"')

        url = scrapertools.find_single_match(str(option), '"url":"(.*?)"')

        url = url.replace('\\/', '/')

        if '/cinestart.' in url: continue
        elif '/1fichier.' in url: continue

        if host in url: continue
        elif url.endswith('.srt'): continue

        url = url.replace('/netu.repelis.run/', '/waaw.to/')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if 'okru.' in url: servidor = 'okru' 

        if not servidor == 'torrent':
            if not 'http' in url: continue

        other = ''

        if config.get_setting('developer_mode', default=False):
            if servidor == 'directo':
                try:
                   if '//' in url: other = url.split('//')[1]
                   else: other = url.split('/')[1]

                   other = other.split('/')[0]
                except:
                   other = url

        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language = lang, quality = qlty, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def clean_title(title):
    logger.info()

    title = title.replace('\\u00e1', 'a').replace('\\u00c1', 'a').replace('\\u00e9', 'e').replace('\\u00ed', 'i').replace('\\u00f3', 'o').replace('\\u00fa', 'u')
    title = title.replace('\\u00f1', 'ñ').replace('\\u00bf', '¿').replace('\\u00a1', '¡').replace('\\u00ba', 'º').replace('\\u2013', '-')
    title = title.replace('\\u00eda', 'a').replace('\\u00f3n', 'o').replace('\\u00fal', 'u').replace('\\u00e0', 'a')
    title = title.replace('\\u00c9', 'E').replace('\\u00da', 'U')
    title = title.replace("\\u00f3", "o").replace("\\u00ed", "i").replace("\\u00f1", "ñ").replace("&#8217;", "").replace("\\u00e1", "a").replace("\\u00e9", "e").replace("\\", "")

    title = title.replace('\\', '').replace('\\/', '').strip()

    return title


def search(item, texto):
    logger.info()
    try:
        item.url = 'search?q=' + texto.replace(" ", "+")
        item.ref = 'search?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
