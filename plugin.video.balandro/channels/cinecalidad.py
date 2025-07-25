# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import re, os, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

from lib import decrypters


LINUX = False
BR = False
BR2 = False

if PY3:
    try:
       import xbmc
       if xbmc.getCondVisibility("system.platform.Linux.RaspberryPi") or xbmc.getCondVisibility("System.Platform.Linux"): LINUX = True
    except: pass

try:
   if LINUX:
       try:
          from lib import balandroresolver2 as balandroresolver
          BR2 = True
       except: pass
   else:
       if PY3:
           from lib import balandroresolver
           BR = true
       else:
          try:
             from lib import balandroresolver2 as balandroresolver
             BR2 = True
          except: pass
except:
   try:
      from lib import balandroresolver2 as balandroresolver
      BR2 = True
   except: pass


host = 'https://www.cinecalidad.vg/'


_players = ['https://cinecalidad.', '.cinecalidad.']


# ~ por si viene de enlaces guardados
ant_hosts = ['https://www.cinecalidad.eu/', 'https://www.cinecalidad.im/', 'https://www.cinecalidad.is/',
             'https://www.cinecalidad.li/', 'https://www.cine-calidad.com/', 'https://cinecalidad.website/',
             'https://www.cinecalidad.lat/', 'https://cinecalidad3.com/', 'https://www5.cine-calidad.com/',
             'https://v3.cine-calidad.com/', 'https://cinecalidad.dev/', 'https://cinecalidad.ms/',
             'https://www3.cinecalidad.ms/', 'https://ww1.cinecalidad.ms/', 'https://www.cinecalidad.gs/',
             'https://www.cinecalidad.tf/', 'https://wvw.cinecalidad.tf/', 'https://vww.cinecalidad.tf/',
             'https://wwv.cinecalidad.tf/', 'https://www.cinecalidad.foo/', 'https://vw.cinecalidad.foo/',
             'https://ww.cinecalidad.foo/', 'https://w.cinecalidad.foo/', 'https://wwv.cinecalidad.foo/',
             'https://wv.cinecalidad.foo/', 'https://vwv.cinecalidad.foo/', 'https://wzw.cinecalidad.foo/',
             'https://v2.cinecalidad.foo/', 'https://www.cinecalidad.so/', 'https://wvw.cinecalidad.so/',
             'https://vww.cinecalidad.so/', 'https://wwv.cinecalidad.so/', 'https://vvv.cinecalidad.so/',
             'https://ww.cinecalidad.so/', 'https://w.cinecalidad.so/', 'https://vvw.cinecalidad.so/',
             'https://wv.cinecalidad.so/', 'https://vvvv.cinecalidad.so/', 'https://wvvv.cinecalidad.so/',
             'https://cinecalidad.fi/']


domain = config.get_setting('dominio', 'cinecalidad', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'cinecalidad')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'cinecalidad')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_cinecalidad_proxies', default=''):
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


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    raise_weberror = True
    if '/release/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_cinecalidad_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('cinecalidad', url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('cinecalidad', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if BR or BR2:
            try:
                ck_name, ck_value = balandroresolver.get_sucuri_cookie(data)
                if ck_name and ck_value:
                    httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])

                if not url.startswith(host):
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
                else:
                    if hay_proxies:
                        data = httptools.downloadpage_proxy('cinecalidad', url, post=post, headers=headers, raise_weberror=raise_weberror).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
            except:
                pass

    if '<title>Just a moment...</title>' in data:
        if not '?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'cinecalidad', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_cinecalidad', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='cinecalidad', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_cinecalidad', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_cinecalidad', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('cinecalidad') ))

    itemlist.append(Item( channel='helper', action='show_help_prales', title='[B]Cuales son sus Clones[/B]', thumbnail=config.get_thumb('cinecalidad'), text_color='turquoise' ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'cinecalidad', thumbnail=config.get_thumb('cinecalidad') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = '[B]En castellano:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'espana/', search_type = 'movie' ))

    itemlist.append(item.clone( title = '[B]En latino:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - [COLOR cyan]Estrenos[/COLOR]', action = 'list_all', url = host + 'estrenos/', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Más vistas', action = 'destacadas', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Más populares', action = 'list_all', url = host + 'peliculas-populares/', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - En [COLOR moccasin]4K[/COLOR]', action = 'list_all', url = host + '4k/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action='anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'serie/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'series-populares/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    opciones = [
        ('accion','Acción'),
        ('animacion','Animación'),
        ('aventura','Aventura'),
        ('belica','Bélica'),
        ('biografia','Biografía'),
        ('ciencia-ficcion','Ciencia ficción'),
        ('comedia','Comedia'),
        ('crimen','Crimen'),
        ('documental','Documental'),
        ('drama','Drama'),
        ('fantasia','Fantasía'),
        ('guerra','Guerra'),
        ('historia','Historia'),
        ('infantil','Infantil'),
        ('misterio','Misterio'),
        ('musica','Música'),
        ('musical','Musical'),
        ('romance','Romance'),
        ('suspenso','Suspenso'),
        ('terror','Terror'),
        ('thriller','Thriller'),
        ('western','Western')
    ]

    url_gen = host + 'categoria/'

    for opc, tit in opciones:
        itemlist.append(item.clone( title = tit, url = url_gen + opc + '/', action = 'list_all', text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1936, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    _promos = 0

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    if not matches:
        bloque = scrapertools.find_single_match(data, '<div id="content">(.*?)>Destacadas<')
        matches = scrapertools.find_multiple_matches(bloque, '<div class="home_post_content">(.*?)</div></div>')

    for match in matches:
        title = scrapertools.find_single_match(match, '<h2>.*?">(.*?)</h2>')
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        url = url.replace('\\/', '/')

        if '-premium-12-meses' in url or '-premium-1-ano' in url or '-12-meses' in url or '/netflix/o/' in url or '/product/' in url or '.ggpickaff.' in url:
            _promos += 1
            continue
        elif 'Netflix Premium' in match or 'Suscripción Disney Plus' in match or 'Suscripción HBO' in match:
            _promos += 1
            continue

        if not url or not title: continue

        plot = scrapertools.find_single_match(match, '<p>.*?">(.*?)</p>').strip()
        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        if year == '-': year = scrapertools.find_single_match(match, '6px;">(.*?)</div>')

        if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")

        if not year: year = '-'

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#038;', '&')

        tipo = 'tvshow' if '/serie/' in url or '/animes/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if item.search_type == 'movie':
            if '/serie/' in url or '/animes/' in url: continue
        elif item.search_type == 'tvshow':
            if not '/serie/' in url and not '/animes/' in url: continue

        if '/espana/' in item.url:
           if not '?castellano=sp' in item.url: url = url + '?castellano=sp'

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title,  infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page_link = scrapertools.find_single_match(data, '<a class="next page-numbers".*?href="(.*?)"')

        if next_page_link:
            itemlist.append(item.clone( title='Siguientes ...', url = next_page_link, action = 'list_all', text_color='coral' ))
    else:
        if not _promos == 0:
            next_page_link = scrapertools.find_single_match(data, '<a class="next page-numbers".*?href="(.*?)"')

            if next_page_link:
                itemlist.append(item.clone( title='Siguientes ...', url = next_page_link, action = 'list_all', text_color='coral' ))

    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Destacadas<(.*?)>Herramientas<')

    matches = scrapertools.find_multiple_matches(bloque, '<a(.*?)</a></li>')

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if item.search_type == 'movie':
            if '/serie/' in url or '/animes/' in url: continue
        else:
            if '/pelicula/' in url: continue

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#038;', '&')

        thumb = scrapertools.find_single_match(match, 'alt=".*?src="(.*?)"')

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        if item.search_type == 'movie':
            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))
        else:
            itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb,
                                        contentType = 'tvshow', contentSerieName = title,  infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<span data-serie="(.*?)".*?data-season="(.*?)"')

    for data_serie, tempo in matches:
        title = 'Temporada ' + tempo

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.data_serie = data_serie
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = item.url, page = 0, data_serie = data_serie,
                                    contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    post = {'action': 'action_change_episode', 'season': str(item.contentSeason), 'serie': str(item.data_serie)}

    headers = {'Referer': item.url}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post, headers = headers)

    matches = scrapertools.find_multiple_matches(data, '<img(.*?)alt=.*?"episode":"(.*?)".*?"url":"(.*?)"')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, epis, url in matches[item.page * item.perpage:]:
        if not epis: epis = '0'

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName

        thumb = thumb.replace('\\/', '/')
        thumb = thumb.replace('src=\\"', '').replace('\\"', '')

        url = url.replace('\\/', '/')

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'latino': 'Lat', 'castellano': 'Esp', 'subtitulado': 'Vose'}

    lang = 'Lat'

    if '?castellano=sp' in item.url: lang = 'Esp'

    data = do_downloadpage(item.url)

    ses = 0

    if '">Ver' in data or '">VER' in data:
        if '">Descargar' in data in data: _final = '">Descargar'
        elif '">DESCARGAR' in data: _final = '">DESCARGAR'
        else: _final = '</aside>'

        bloque = scrapertools.find_single_match(data, '">Ver(.*?)' + _final)
        if not bloque: bloque = scrapertools.find_single_match(data, '">VER(.*?)' + _final)

        matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-src="(.*?)".*?data-lmt="(.*?)".*?data-option>(.*?)</a>')

        if not matches:
            matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-src="(.*?)".*?data-lmt="(.*?)".*?data-option.*?>(.*?)</a>')

        for data_url, data_lmt, servidor in matches:
            ses += 1

            other = ''

            servidor = servidor.lower().strip()

            if servidor == 'trailer' or servidor == 'youtube': continue

            elif servidor == 'veri': continue
            elif servidor == 'player': continue
            elif servidor == 'vip': continue

            elif 'voesx' in servidor: servidor = 'voe'
            elif servidor == 'maxplay': servidor = 'voe'

            elif servidor == 'doos' or servidor == 'dood': servidor = 'doodstream'
            elif 'doostream' in servidor: servidor = 'doodstream'

            elif servidor == 'ok': servidor = 'okru'

            elif servidor == 'google': servidor = 'gvideo'
            elif servidor == 'drive': servidor = 'gvideo'
            elif servidor == 'google drive': servidor = 'gvideo'
            elif servidor == 'netu' or servidor == 'hqq': servidor = 'waaw'
            elif servidor == 'd0o0d' or servidor == 'do0od' or servidor == 'd0000d' or servidor == 'd000d': servidor = 'doodstream'

            elif servidor == 'goodstream': servertools.corregir_other(servidor)
            elif servidor == 'streamwish': servertools.corregir_other(servidor)

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            qlty = '1080'

            itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', data_url = data_url, data_lmt = data_lmt,
                                  quality = qlty, language = lang, other = other ))

    hay_descargas = False

    if '">Descargar' in data or '">DESCARGAR' in data:
        bloque = scrapertools.find_single_match(data, '">Descargar(.*?)</aside>')
        if not bloque: bloque = scrapertools.find_single_match(data, '">DESCARGAR(.*?)</aside>')

        matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-url="(.*?)".*?data-lmt="(.*?)".*?data-link>(.*?)</a>')
        if not matches:
            matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-url="(.*?)".*?data-lmt="(.*?)".*?data-link.*?>(.*?)</a>')

        for data_url, data_lmt, servidor in matches:
            hay_descargas = True

            ses += 1

            servidor = servidor.lower().strip()

            qlty = '1080'

            if '4k' in servidor or '4K' in servidor:
               qlty = '4K'
               servidor = servidor.replace('4k', '').replace('4K', '').strip()

            if servidor == 'subtítulos' or 'subtitulo' in servidor: continue

            elif servidor == 'veri': continue

            elif servidor == 'utorrent': servidor = 'torrent'

            elif servidor == 'bittorrent': servidor = 'torrent'

            elif 'bittorrent' in servidor: servidor = 'torrent'
            elif 'spanishtracker' in servidor: servidor = 'torrent'

            elif 'voesx' in servidor: servidor = 'voe'
            elif servidor == 'maxplay': servidor = 'voe'

            elif servidor == 'google': servidor = 'gvideo'
            elif servidor == 'drive': servidor = 'gvideo'
            elif servidor == 'google drive': servidor = 'gvideo'

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            if servidor == 'torrent':
                qlty = scrapertools.find_single_match(bloque, '.*?data-url="' + data_url + '".*?class="txtmf">(.*?)</span>')

            itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', data_url = data_url, data_lmt = data_lmt,
                                  quality = qlty, language = lang ))

    # ~ es por las series
    if not hay_descargas:
        if '">Descargar' in data or '">DESCARGAR' in data:
            bloque = scrapertools.find_single_match(data, '">Descargar(.*?)</noscript></noscript>')
            if not bloque: bloque = scrapertools.find_single_match(data, '">DESCARGAR(.*?)</noscript></noscript>')

            matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)">(.*?)</a>')

            for _url, servidor in matches:
                ses += 1

                servidor = servidor.lower().strip()

                if servidor == "subtítulos" or servidor == 'subtitulos': continue

                elif servidor == 'veri': continue

                elif servidor == 'bittorrent': servidor = 'torrent'

                elif 'bittorrent' in servidor: servidor = 'torrent'

                elif 'voesx' in servidor: servidor = 'voe'
                elif servidor == 'maxplay': servidor = 'voe'

                elif servidor == 'google drive': servidor = 'gvideo'

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                url = item.url + _url

                itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', url = url, other = 'd' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'cinecalidad', default='')

    if domain_memo: host_player = domain_memo
    else: host_player = host

    if item.server == 'directo' or item.other == 'd':
        url = ''

        if item.url:
            data = do_downloadpage(item.url)

            url = scrapertools.find_single_match(data, '<a target="_blank".*?href="(.*?)"')

            if url.endswith('.torrent'):
                if config.get_setting('proxies', item.channel, default=''):
                    if PY3:
                        from core import requeststools
                        data = requeststools.read(url, 'cinecalidad')
                    else:
                        data = do_downloadpage(url)

                    file_local = os.path.join(config.get_data_path(), "temp.torrent")
                    with open(file_local, 'wb') as f: f.write(data); f.close()

                    itemlist.append(item.clone( url = file_local, server = 'torrent' ))
                else:
                    itemlist.append(item.clone( url = url, server = 'torrent' ))

                return itemlist

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            itemlist.append(item.clone(url = url, server = servidor))

            return itemlist

    url = base64.b64decode(item.data_url).decode("utf-8")

    url = url.replace('&amp;', '&')

    servidor = item.server

    # ~ por si esta en ant_hosts
    if url.startswith("http"):
        for ant in ant_hosts:
            url = url.replace(ant, host_player)

        if not host_player in url:
            for _player in _players:
                if _player in url:
                    url_avis = url
                    if '/?' in url_avis: url_avis = url.split('?')[0]

                    platformtools.dialog_ok(config.__addon_name + ' CineCalidad', '[COLOR cyan][B]Al parecer el Canal cambió de Dominio.[/B][/COLOR]', '[COLOR yellow][B]' + url_avis + '[/B][/COLOR]', 'Por favor, Reviselo en [COLOR goldenrod][B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]')
                    return itemlist

    if url:
        if host_player in url:
            data = do_downloadpage(url)

            url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, 'id="btn_enlace">.*?href="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, '<a id="some_link">.*?value="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, 'window.location.href = "(.*?)"')
            if not url: url = scrapertools.find_single_match(data, "window.location.href = '(.*?)'")

            url = url.replace('&amp;', '&')

            if servidor == 'mega':
               if url.startswith('#'): url = 'https://mega.nz/' + url
               elif not url.startswith('http'): url = 'https://mega.nz/file/' + url

            if not url:
                if '/acortalink.' in data:
                    return 'Tiene [COLOR plum]Acortador[/COLOR] del enlace'

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

    if '/protect/v.php' in url or '/protect/v2.php' in url:
        enc_url = scrapertools.find_single_match(url, "i=([^&]+)")
        url = base64.b64decode(enc_url).decode("utf-8")

        if not 'magnet' in url: url = url.replace('/file/', '/embed#!')

    if url:
        if '/acortalink.' in url:
            host_torrent = host_player[:-1]
            url_base64 = decrypters.decode_url_base64(url, host_torrent)

            if url_base64.endswith('.torrent'): url = url_base64
            elif url_base64.startswith('magnet:'): url = url_base64

            else:
               if url_base64:
                   new_server = servertools.get_server_from_url(url_base64)
                   new_server = servertools.corregir_other(new_server)				   

                   if not new_server == 'directo':
                       url = url_base64
                       servidor = new_server

        if '/acortalink.' in url:
           return 'Tiene [COLOR plum]Acortador[/COLOR] del enlace'

        if url.endswith('.torrent'):
            if config.get_setting('proxies', item.channel, default=''):
                if PY3:
                    from core import requeststools
                    data = requeststools.read(url, 'cinecalidad')
                else:
                    data = do_downloadpage(url)

                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))
            else:
                itemlist.append(item.clone( url = url, server = 'torrent' ))

            return itemlist

        elif 'magnet:' in url:
            itemlist.append(item.clone( url = url, server = 'torrent' ))
            return itemlist

        if servidor == 'directo':
            if not url.startswith('http'): return itemlist

            if '/okru.' in url: servidor = 'okru'
            else:
                new_server = servertools.corregir_other(url).lower()
                if new_server.startswith("http"):
                    if not config.get_setting('developer_mode', default=False): return itemlist
                servidor = new_server

        if servidor == 'zplayer': url = url + '|' + host_player

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
