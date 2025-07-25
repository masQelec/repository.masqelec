# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


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


host = 'https://ww3.animeonline.ninja/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://animeonline1.ninja/', 'https://www1.animeonline.ninja/', 'https://ww2.animeonline.ninja/']


domain = config.get_setting('dominio', 'animeonline', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'animeonline')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'animeonline')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_animeonline_proxies', default=''):
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
    for ant in ant_hosts:
        url = url.replace(ant, host)

    if not headers: headers = {'Referer': host}

    if '/release/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_animeonline_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('animeonline', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('animeonline', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if BR or BR2:
            try:
                ck_name, ck_value = balandroresolver.get_sucuri_cookie(data)
                if ck_name and ck_value:
                    httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])

                if not url.startswith(host):
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    if hay_proxies:
                        data = httptools.downloadpage_proxy('animeonline', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
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

    domain_memo = config.get_setting('dominio', 'animeonline', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_animeonline', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='animeonline', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_animeonline', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_animeonline', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('animeonline') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'animeonline', thumbnail=config.get_thumb('animeonline') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'all', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'online/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'episodio/', group = 'last_epis', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all',  url = host + 'genero/en-emision/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'tendencias/?get=tv', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'ratings/?get=tv', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Premiados', action = 'list_all', url = host + 'genero/award-winning-anime/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Sin censura', action = 'list_all', url = host + 'genero/sin-censura/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Proximamente', action = 'list_all', url = host + 'genero/proximamente/', search_type = 'tvshow', text_color='yellowgreen' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'pelis', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    text_color = 'moccasin'

    itemlist.append(item.clone( title = 'Amazon prime video', action = 'list_all', url = host + 'genero/amazon-prime-video/', search_type = 'tvshow', text_color=text_color ))

    itemlist.append(item.clone( title = 'Dragon ball', action = 'dragons', search_type = 'tvshow', text_color=text_color ))

    itemlist.append(item.clone( title = 'En blu-ray / dvd', action = 'list_all', url = host + 'genero/blu-ray-dvd/', search_type = 'tvshow', text_color=text_color ))

    itemlist.append(item.clone( title = 'Live action', action = 'list_all', url = host + 'genero/live-action/', search_type = 'tvshow', text_color=text_color ))

    return itemlist


def dragons(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Dragon Ball', action = 'temporadas', url = host + 'online/dragon-ball-122023/',
                                contentType = 'tvshow', contentSerieName = 'Dragon Ball' ))

    itemlist.append(item.clone( title = 'Dragon Ball Kai', action = 'temporadas', url = host + 'online/dragon-ball-kai/',
                                contentType = 'tvshow', contentSerieName = 'Dragon Ball Kai' ))

    itemlist.append(item.clone( title = 'Dragon Ball Super', action = 'temporadas', url = host + 'online/dragon-ball-super-3/',
                                contentType = 'tvshow', contentSerieName = 'Dragon Ball Super' ))

    itemlist.append(item.clone( title = 'Dragon Ball GT', action = 'temporadas', url = host + 'online/dragon-ball-gt-3/',
                                contentType = 'tvshow', contentSerieName = 'Dragon Ball GT' ))

    itemlist.append(item.clone( title = 'Dragon Ball Heroes', action = 'temporadas', url = host + 'online/dragon-ball-heroes-3/',
                                contentType = 'tvshow', contentSerieName = 'Dragon Ball Heroes' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo [COLOR deepskyblue]Películas[/COLOR]', action = 'list_all', url = host + 'pelicula/' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'tendencias/?get=movies' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'ratings/?get=movies' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'genero/anime-castellano/', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'genero/audio-latino/', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    generos = [
       'accion',
       'aventura',
       'belica',
       'ciencia-ficcion',
       'comedia',
       'crimen',
       'documental',
       'drama',
       'familia',
       'fantasia',
       'misterio',
       'musica',
       'romance',
       'suspense',
       'terror',
       'zeroanime'
       ]

    for genero in generos:
        url = host + '/genero/' + genero + '/'

        itemlist.append(item.clone( title = genero.capitalize(), url = url, action = 'list_all', text_color='springgreen' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    url_anio = url = host + 'release/'

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1984, -1):
        url = url_anio + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '<header><h1>' in data: parte = '<header><h1>'
    else: parte = '<h1>'

    bloque = scrapertools.find_single_match(data, parte + '(.*?)</h2>')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        lang = scrapertools.find_single_match(match, '<span class="quality">(.*?)</span>')
        lang = lang.replace('Audio', '').lower().strip()

        if lang == 'latino' or lang == 'laninofinal': lang = 'Lat'
        elif lang == 'castellano' or lang == 'español': lang = 'Esp'
        elif lang == 'multi': lang = 'Multi-Audio'
        elif lang == 'triple': lang = 'Triple-Audio'
        else: lang = ''

        qlty = scrapertools.find_single_match(match, '<span class="quality">(.*?)</span>').lower()
        if 'audio' in qlty: qlty = ''
        elif 'castellano' in qlty: qlty = ''
        elif 'español' in qlty: qlty = ''

        if qlty == 'final' or qlty == 'corto' or qlty == 'sin censura': qlty = ''

        year = scrapertools.find_single_match(match, '</h3><span>(.*?)</span>')
        if not year:
            if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")
            else: year = '-'

        title = title.replace('&#8217;', '').replace('&#8211;', '').replace('&#8220;', '').replace('&#8221;', '').replace('&#8230;', '').replace('&#038;', '')

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if item.group == 'last_epis' or tipo == 'movie':
            if tipo == 'movie':
                if item.search_type != 'all':
                    if item.search_type == 'tvshow': continue

                PeliName = corregir_SerieName(title)

                itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                            qualities=qlty, languages=lang, fmt_sufijo=sufijo,
                                            contentType='movie', contentTitle=PeliName, infoLabels={'year': year} ))

                continue

            else:
                if item.search_type != 'all':
                    if item.search_type == 'movie': continue

                if '>Película<' in match: continue

                SerieName = corregir_SerieName(title)

                epis = scrapertools.find_single_match(title, 'Cap(.*?)$').strip()
                if not epis: epis = 1

                title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

                title = title.replace('Cap ', '[COLOR goldenrod]Epis. [/COLOR]').replace('Episode ', '[COLOR goldenrod]Epis. [/COLOR]')

                titulo = '[COLOR goldenrod]Epis. [/COLOR]' + str(epis) + ' ' + title.replace('Epis. ', '').strip()

                itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                            qualities=qlty, languages=lang, fmt_sufijo=sufijo,
                                            contentType = 'episode', contentSerieName = SerieName,
                                            contentSeason = 1, contentEpisodeNumber=epis, infoLabels={'year': year} ))

                continue

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            SerieName = corregir_SerieName(title)

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, qualities=qlty, languages=lang, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data,'<span class="current">.*?' + "<a href='(.*?)'")
            if not next_page: next_page = scrapertools.find_single_match(data,'<span class="current">.*?<a href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile("<span class='se-t.*?'>(.*?)</span>", re.DOTALL).findall(data)
    if not temporadas: temporadas = re.compile('<span class="se-t.*?">(.*?)</span>', re.DOTALL).findall(data)

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

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = tempo, page = 0, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>%s</span>(.*?)</div></div>" % (item.contentSeason))
    if not bloque: bloque = scrapertools.find_single_match(data, '<span class="se-t.*?">%s</span>(.*?)</div></div>' % (item.contentSeason))

    episodes = re.compile("<li class='mark-(.*?)</li>", re.DOTALL).findall(bloque)
    if not episodes: episodes = re.compile('<li class="mark-(.*?)</li>', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(episodes)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('AnimeOnline', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for epi in episodes[item.page * item.perpage:]:
        epis = scrapertools.find_single_match(epi, "(.*?)'>")
        if not epis: epis = scrapertools.find_single_match(epi, '(.*?)">')

        if not epis: epis = 1

        thumb = scrapertools.find_single_match(epi, "data-src='(.*?)'")
        if not thumb: thumb = scrapertools.find_single_match(epi, 'data-src="(.*?)"')

        url = scrapertools.find_single_match(epi, "<a href='(.*?)'")
        if not url: url = scrapertools.find_single_match(epi, '<a href="(.*?)"')

        title = scrapertools.find_single_match(epi, "<div class='episodiotitle'>.*?'>(.*?)</a>")
        if not title: title = scrapertools.find_single_match(epi, '<div class="episodiotitle">.*?">(.*?)</a>')

        if item.contentSerieName: 
            titulo = '%sx%s %s' % (str(item.contentSeason), str(epis), title)

            titulo = titulo + ' ' + item.contentSerieName

        else: titulo = item.title

        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]')

        if '.' in epis: epis = epis.split(".")[0]

        if url:
            itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb, 
                                        contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(epis) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)

    players = scrapertools.find_multiple_matches(data, "<li id='player-option-(.*?)</ul>")
    if not players: players = scrapertools.find_multiple_matches(data, '<li id="player-option-(.*?)</ul>')

    ses = 0

    for datos in players:
        ses += 1

        _server = scrapertools.find_single_match(datos, "<span class='server'>(.*?)</span>")
        if not _server: _server = scrapertools.find_single_match(datos, '<span class="server">(.*?)</span>')

        if not 'saidochesto' in _server: continue

        data_type = scrapertools.find_single_match(datos, "data-type='(.*?)'")
        if not data_type: data_type = scrapertools.find_single_match(datos, 'data-type="(.*?)"')

        data_post = scrapertools.find_single_match(datos, "data-post='(.*?)'")
        if not data_post: data_post = scrapertools.find_single_match(datos, 'data-post="(.*?)"')

        data_nume = scrapertools.find_single_match(datos, 'data-nume="(.*?)"')
        if not data_nume: data_nume = scrapertools.find_single_match(datos, "data-nume='(.*?)'")

        if not data_type or not data_post or not data_nume: continue

        url = host + '/wp-json/dooplayer/v1/post/' + data_post + '?type=' + data_type + '&source=' + data_nume

        data = do_downloadpage(url)

        link = scrapertools.find_single_match(data, '"embed_url":"(.*?)"')

        if not link: continue

        link = link.replace('\\/', '/')

        servers = do_downloadpage(link)

        _servers = scrapertools.find_multiple_matches(servers, '<li onclick="go_(.*?)</li>')

        for dat_server in _servers:
            ses += 1

            url = scrapertools.find_single_match(dat_server, "to_player.*?'(.*?)'")

            if '/saikoudane.' in url: continue
            elif '/saidochesto.' in url: continue

            if url:
                if url == 'undefined': continue

                if url.startswith('https:/streamwish.'): url = url.replace('https:/streamwish.', 'https://streamwish.')
                elif url.startswith('https://filemooon.'): url = url.replace('https://filemooon.', 'https://filemoon.')

                if '/netuplayer.top/' in url: url = url.replace('/netuplayer.top/', '/netu.to/')

                if 'Audio Japones' in dat_server: lang = 'Jap'
                elif 'Sub Español' in dat_server: lang = 'Vose'
                elif 'Sub Latino' in dat_server: lang = 'Vose'
                elif 'Latino' in dat_server: lang = 'Lat'
                elif 'Castellano' in dat_server or 'español' in dat_server: lang = 'Esp'
                else: lang = '?'

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                link_other = ''

                if config.get_setting('developer_mode', default=False):
                    try:
                       if '//' in url: link_other = url.split('//')[1]
                       else: link_other = url.split('/')[1]

                       link_other = link_other.split('/')[0]
                    except:
                       link_other = url
                else: link_other = url

                link_other = link_other.replace('www.', '').replace('.com', '').replace('.net', '').replace('.org', '').replace('.top', '').replace('.do', '')
                link_other = link_other.replace('.co', '').replace('.cc', '').replace('.sh', '').replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '').replace('.hu', '')
                link_other = link_other.replace('.eu', '').replace('.ws', '').replace('.ag', '').replace('.sx', '').replace('.online', '').replace('.lat', '').replace('.link', '').replace('.fun', '')

                if servidor == 'various': other = servertools.corregir_other(link_other)
                else:
                    link_other = servertools.corregir_servidor(link_other)

                    if link_other == servidor: link_other = ''
                    else: link_other = link_other

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = link_other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]
    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if 'Live Action' in SerieName: SerieName = SerieName.split("Live Action")[0]
    if 'Netflix' in SerieName: SerieName = SerieName.split("Netflix")[0]
    if 'NETFLIX' in SerieName: SerieName = SerieName.split("NETFLIX")[0]

    if ' S1 ' in SerieName: SerieName = SerieName.split(" S1 ")[0]
    elif ' S2 ' in SerieName: SerieName = SerieName.split(" S2 ")[0]
    elif ' S3 ' in SerieName: SerieName = SerieName.split(" S3 ")[0]
    elif ' S4 ' in SerieName: SerieName = SerieName.split(" S4 ")[0]
    elif ' S5 ' in SerieName: SerieName = SerieName.split(" S5 ")[0]
    elif ' S6 ' in SerieName: SerieName = SerieName.split(" S6 ")[0]
    elif ' S7 ' in SerieName: SerieName = SerieName.split(" S7 ")[0]
    elif ' S8 ' in SerieName: SerieName = SerieName.split(" S8 ")[0]
    elif ' S9 ' in SerieName: SerieName = SerieName.split(" S9 ")[0]

    if ' T1 ' in SerieName: SerieName = SerieName.split(" T1 ")[0]
    elif ' T2 ' in SerieName: SerieName = SerieName.split(" T2 ")[0]
    elif ' T3 ' in SerieName: SerieName = SerieName.split(" T3 ")[0]
    elif ' T4 ' in SerieName: SerieName = SerieName.split(" T4 ")[0]
    elif ' T5 ' in SerieName: SerieName = SerieName.split(" T5 ")[0]
    elif ' T6 ' in SerieName: SerieName = SerieName.split(" T6 ")[0]
    elif ' T7 ' in SerieName: SerieName = SerieName.split(" T7 ")[0]
    elif ' T8 ' in SerieName: SerieName = SerieName.split(" T8 ")[0]
    elif ' T9 ' in SerieName: SerieName = SerieName.split(" T9 ")[0]

    if '2nd' in SerieName: SerieName = SerieName.split("2nd")[0]
    if '3rd' in SerieName: SerieName = SerieName.split("3rd")[0]
    if '4th' in SerieName: SerieName = SerieName.split("4th")[0]
    if '5th' in SerieName: SerieName = SerieName.split("5th")[0]
    if '6th' in SerieName: SerieName = SerieName.split("6th")[0]
    if '7th' in SerieName: SerieName = SerieName.split("7th")[0]
    if '8th' in SerieName: SerieName = SerieName.split("8th")[0]
    if '9th' in SerieName: SerieName = SerieName.split("9th")[0]

    if 'Cap' in SerieName: SerieName = SerieName.split("Cap")[0]

    if ': ' in SerieName: SerieName = SerieName.split(": ")[0]

    SerieName = SerieName.strip()

    return SerieName


def search(item, texto):
    logger.info()
    try:
        item.url =  host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
