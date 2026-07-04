# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


from lib.pyberishaes import GibberishAES
from lib import decrypters


host = 'https://sololatino.net/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_sololatino_proxies', default=''):
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
    if '/filtro/' in url: raise_weberror = False

    if not headers: headers = {'Referer': host}

    hay_proxies = False
    if config.get_setting('channel_sololatino_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('sololatino', url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

        if not data:
            if not '/buscar?q=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('sololatino', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='sololatino', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if config.get_setting('mnu_doramas', default=False):
        itemlist.append(item.clone( title = 'Doramas', action = 'mainlist_doramas', text_color = 'firebrick' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', text_color = 'springgreen' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'peliculas?sort=popular', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'peliculas?sort=rating', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'series?genero=&sort=popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'series?sort=rating', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action= 'plataformas', search_type='tvshow', text_color = 'moccasin' ))

    return itemlist


def mainlist_doramas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', _type = 'search', search_type = 'tvshow', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'doramas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'doramas?sort=popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'doramas?sort=rating', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'doramas', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', group = 'doramas', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'animes?sort=popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'animes?sort=rating', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'animes', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', group = 'animes', search_type = 'tvshow' ))

    return itemlist


def plataformas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Amazon', action = 'list_all', url = host + 'red/amazon-prime-video', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Apple Tv+', action = 'list_all', url = host + 'red/apple-tv/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'AT x', action = 'list_all', url = host + 'red/at-x/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Bs 11', action = 'list_all', url = host + 'red/bs11/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Disney+', action = 'list_all', url = host + 'red/disney/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Hbo', action = 'list_all', url = host + 'red/hbo/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Hbo Max', action = 'list_all', url = host + 'red/hbo-max/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Hulu', action = 'list_all', url = host + 'red/hulu/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Nbc', action = 'list_all', url = host + 'red/nbc/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host + 'red/netflix/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Tokyo Mx', action = 'list_all', url = host + 'red/tokyo.mx/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Tv tokyo', action = 'list_all', url = host + 'red/tv-tokyo/', search_type = 'tvshow', text_color = 'moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        url_gen = host + 'peliculas'
        text_color = 'deepskyblue'
    else:
       if item.group == 'animes':
           url_gen = host + 'animes'
           text_color = 'springgreen'
       elif item.group == 'doramas':
           url_gen = host + 'doramas'
           text_color = 'firebrick'
       else:
           url_gen = host + 'series/'
           text_color = 'hotpink'

    data = do_downloadpage(url_gen)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '">Género:(.*?)</select>')

    matches = re.compile('<option value="(.*?)".*?>(.*?)</option>').findall(bloque)

    for gen, title in matches:
        if config.get_setting('descartar_anime', default=False):
           if title == 'anime': continue

        title = title.replace('&amp;', '&').lower().strip()

        if item.search_type == 'movie': url = host + 'peliculas?genero=' + gen
        else:
            if item.group == 'animes': url = host + 'animes?genero=' + gen
            elif item.group == 'doramas': url = host + 'doramas?genero=' + gen
            else: url = host + 'series?genero=' + gen

        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, text_color = text_color ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        text_color = 'deepskyblue'
    else:
       if item.group == 'animes':
           text_color = 'springgreen'
       elif item.group == 'doramas':
           text_color = 'firebrick'
       else:
           text_color = 'hotpink'

    if item.search_type == 'movie': tope_year = 1931
    else:
        if item.group == 'animes': tope_year = 1989
        else: tope_year = 1981

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, tope_year, -1):
        if item.search_type == 'movie': url = host + 'peliculas?genre=&año=' + str(x) + '/'
        else:
            if item.group == 'animes': url = host + 'animes?genre=&año=' + str(x) + '/'
            elif item.group == 'animes': url = host + 'doramas?genre=&año=' + str(x) + '/'
            else: url = host + 'series?genre=&año=' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<div class="card">(.*?)</div></div></a>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        if 'guia-solo-latino' in url: continue

        title = title.replace('&#8230;', '').replace('&#8211;', '').replace('&#038;', '').replace('&#8217;', "'").replace('&#039;', "'").replace('&amp;', '&').strip()

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="card__year">(.*?)</span>')
        if not year: year = '-'

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<span class="page-item active".*?<a href="(.*?)".*?</a></span>')

        if next_page:
            if 'page=' in next_page:
                next_page = next_page.replace('&amp;', '&')

                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile('<option value="(.*?)"', re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = tempo
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    _tmdb_id = scrapertools.find_single_match(data, '/title/tt(.*?)"')

    bloque = scrapertools.find_single_match(data, '<div data-season-panel="' + str(item.contentSeason) + '"(.*?)</a></div></div>')

    matches = re.compile('<a href="(.*?)".*?<img src="(.*?)".*?<p class="ep-num">E(.*?)</p>.*?<p class="text-sm font-semibold text-white leading-tight">(.*?)</p>', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, thumb, epis, title in matches[item.page * item.perpage:]:
        if not epis: epis = 1

        _tmdb_id = _tmdb_id.replace('/', '')

        if '-' in _tmdb_id: _tmdb_id = _tmdb_id.split("-")[0]

        nro_epi = str(epis)
        if len(nro_epi) == 1: nro_epi = '0' + nro_epi

        _tmdb_id = _tmdb_id + '-' + str(item.contentSeason) + 'x' + str(nro_epi)

        title = title.replace('&#039;s', "'s").replace('&quot;', '').replace('&amp;', '&').strip()

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        if 'Epis.' in titulo: titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb, _tmdb_id=_tmdb_id,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    _player_id = scrapertools.find_single_match(data, 'data-player-id="(.*?)"')

    if not _player_id: _player_id = scrapertools.find_single_match(data, 'data-server-url="(.*?)"')
 
    if not _player_id: _player_id = scrapertools.find_single_match(data, 'data-player-token="(.*?)"')

    if not _player_id: return itemlist

    if item._tmdb_id:
        _tmdb_id = item._tmdb_id
    else:
        _tmdb_id = scrapertools.find_single_match(data, '/title/tt(.*?)"')

    if not _tmdb_id: return itemlist
 
    if not 'iframe' in _player_id:
        headers = {'Referer': item.url}

        post = {'t': _player_id}

        api_url = host + 'api/player-url'

        data = do_downloadpage(api_url, post=post, headers=headers)

        new_url = scrapertools.find_single_match(data, '"url":"(.*?)"')

        if not new_url:
            new_url = 'https://embed69.org/f/tt' + _tmdb_id
    else:
        new_url = _player_id

    new_url = new_url.replace('\\/', '/')

    if not 'http' in new_url: return itemlist

    new_url = new_url.replace('/player.pelisserieshoy.com/', '/embed69.org/')

    if not '/embed69.' in new_url and not '/vidurl' in new_url: return itemlist

    data = do_downloadpage(new_url)

    ses = 0

    # ~ P1ayers
    dataLink = scrapertools.find_single_match(data, 'const dataLink =(.*?);')
    if not dataLink: dataLink = scrapertools.find_single_match(data, 'dataLink(.*?);')

    e_bytes = scrapertools.find_single_match(data, "const bytes =.*?'(.*?)'")
    if not e_bytes: e_bytes = scrapertools.find_single_match(data, "const safeServer =.*?'(.*?)'")

    e_links = dataLink.replace(']},', '"type":"file"').replace(']}]', '"type":"file"')

    age = ''
    if not dataLink or not e_bytes: age = 'crypto'

    langs = scrapertools.find_multiple_matches(str(e_links), '"video_language":(.*?)"type":"file"')

    for lang in langs:
         ses += 1

         lang = lang + '"type":"video"'

         links = scrapertools.find_multiple_matches(str(lang), '"servername":"(.*?)","link":"(.*?)".*?"type":"video"')

         if 'SUB' in lang: lang = 'Vose'
         elif 'LAT' in lang: lang = 'Lat'
         elif 'ESP' in lang: lang = 'Esp'
         elif 'JAP' in lang: lang = 'Jap'
         else: lang = '?'

         for srv, link in links:
             ses += 1

             srv = srv.lower().strip()

             if not srv: continue
             elif host in link: continue

             elif '1fichier.' in srv: continue
             elif 'plustream' in srv: continue
             elif 'embedsito' in srv: continue
             elif 'disable2' in srv: continue
             elif 'disable' in srv: continue
             elif 'xupalace' in srv: continue
             elif 'uploadfox' in srv: continue

             elif srv == 'download': continue
             elif srv == 'up2box': continue

             servidor = servertools.corregir_servidor(srv)

             if servertools.is_server_available(servidor):
                 if not servertools.is_server_enabled(servidor): continue
             else:
                 if not config.get_setting('developer_mode', default=False): continue

             other = ''
             cpow = ''

             if servidor == 'various': other = servertools.corregir_other(srv)

             if '.eyJs' in link: age = ''

             elif 'POW_CHALLENGE' in data:
                cpow = scrapertools.find_single_match(data, "POW_CHALLENGE\s*=\s*'([^']+)';" +
                                                           "\s*\w*\s*POW_DIFFICULTY\s*=\s*(\d+);" +
                                                           "\s*\w*\s*POW_SALT\s*=\s*'([^']+)';")
                if cpow: age = ''

             itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, title = '',
                                   crypto=link, bytes=e_bytes, age=age, cpow=cpow, language=lang, other=other ))

         continue

    # ~ Player 2
    match = scrapertools.find_single_match(data, '"dooplay_player_option ".*?<iframe.*?src="(.*?)".*?</iframe>')

    if not match:
        if not itemlist:
            match = new_url.replace('/embed69.org/f/', '/xupalace.org/video/')

    if match:
        if not '/embed69.' in match and not '/vidurl/' in match:
            data = do_downloadpage(match)

            matchesx = scrapertools.find_multiple_matches(data, "go_to_playerVast.*?'(.*?)'(.*?)</span>")

            for matchx, restox in matchesx:
                ses += 1

                if '/embedsito.' in matchx: continue
                elif '/player-cdn.' in matchx: continue
                elif '/1fichier.' in matchx: continue
                elif '/hydrax.' in matchx: continue
                elif '/xupalace.' in matchx: continue
                elif '/uploadfox.' in matchx: continue

                if 'data-lang="0"' in restox: lang = 'Lat'
                elif 'data-lang="1"' in restox: lang = 'Esp'
                elif 'data-lang="2"' in restox: lang = 'Vose'
                elif 'data-lang="3"' in restox: lang = 'Jap'
                else: lang = '?'

                servidor = servertools.get_server_from_url(matchx)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue 
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                other = ''
                if servidor == 'various': other = servertools.corregir_other(matchx)

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = matchx,
                                      language=lang, other=other, age='xp' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.crypto:
        crypto = str(item.crypto)
        bytes = str(item.bytes)

        url = ''

        if not bytes:
            if '.eyJs' in item.crypto:
                url = scrapertools.find_single_match(item.crypto, '\.(eyJs.*?)\.')
                url += '='

                try:
                    url = base64.b64decode(url).decode()
                    url = scrapertools.find_single_match(url, '"link":"(.*?)"')
                except:
                    url = ''

            elif item.cpow:
                res_pow = {"challenge": item.cpow[0], "difficulty": int(item.cpow[1]), "salt": item.cpow[2]}

                resolve_pow = decrypters.decode_pow(res_pow)
                aes_clave = resolve_pow.get("aes_key", "")

                if aes_clave:
                    url = decrypters.decode_decipher(crypto, aes_clave)

        if not url:
            if bytes:
                try:
                   url = GibberishAES.dec(GibberishAES(), string = crypto, pass_ = bytes)
                except:
                    url = ''

            if not url:
                if bytes:
                    url = decrypters.decode_decipher(crypto, bytes)

            if not url:
                if crypto.startswith("http"):
                    url = crypto.replace('\\/', '/')

                if not url:
                    return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

            elif not url.startswith("http"):
                return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

    if url:
        if '/hydrax.' in url or '/xupalace.' in url or '/uploadfox.' in url or '/embed69.' in url or '/pelisplay.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        servidor = servertools.get_server_from_url(url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'buscar?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

