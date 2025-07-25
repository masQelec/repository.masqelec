# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import re, os

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


host = 'https://www.cinecalidad.ec/'


_players = ['https://cinecalidad.', '.cinecalidad.']


# ~ por si viene de enlaces guardados
ant_hosts = ['https://cinecalidad.lol/', 'https://cinecalidad.link/', 'https://ww3.cinecalidad.link/',
             'https://ww2.cinecalidad.link/', 'https://ww5.cinecalidad.link/', 'https://cinecalidad.fan/',
             'https://cinecalidad.run/', 'https://cinecalidad.cat/', 'https://w1.cinecalidad.cat/',
             'https://w10.cinecalidad.cat/', 'https://w2.cinecalidad.cat/', 'https://w5.cinecalidad.cat/',
             'https://w11.cinecalidad.cat/', 'https://w15.cinecalidad.cat/', 'https://w16.cinecalidad.cat/',
             'https://w17.cinecalidad.cat/', 'https://w18.cinecalidad.cat/', 'https://ww1.cinecalidad.cat/',
             'https://ww2.cinecalidad.cat/', 'https://c1.cinecalidad.cat/', 'https://c2.cinecalidad.cat/',
             'https://c3.cinecalidad.cat/', 'https://c4.cinecalidad.cat/', 'https://cinecalidad.win/',
             'https://w1.cinecalidad.win/', 'https://w2.cinecalidad.win/', 'https://w5.cinecalidad.win/',
             'https://w6.cinecalidad.win/', 'https://w7.cinecalidad.win/', 'https://w8.cinecalidad.win/',
             'https://w9.cinecalidad.win/', 'https://c1.cinecalidad.win/', 'https://c2.cinecalidad.win/',
             'https://w10.cinecalidad.win/', 'https://w1.cinecalidad.ist/', 'https://cinecalidad.ist/',
             'https://cinecalidad.vet/', 'https://w1.cinecalidad.vet/', 'https://w2.cinecalidad.vet/',
             'https://w3.cinecalidad.vet/', 'https://w4.cinecalidad.vet/', 'https://w5.cinecalidad.vet/',
             'https://w6.cinecalidad.vet/', 'https://w7.cinecalidad.vet/', 'https://w8.cinecalidad.vet/',
             'https://w11.cinecalidad.vet/', 'https://w12.cinecalidad.vet/', 'https://ww.cinecalidad.vet/',
             'https://wc.cinecalidad.vet/', 'https://wy.cinecalidad.vet/', 'https://www.cinecalidad.men/',
             'https://vww.cinecalidad.men/', 'https://wwv.cinecalidad.men/', 'https://wvw.cinecalidad.men/',
             'https://ww.cinecalidad.men/', 'https://vw.cinecalidad.men/', 'https://wv.cinecalidad.men/',
             'https://vv.cinecalidad.men/', 'https://v.cinecalidad.men/', 'https://v1.cinecalidad.men/',
             'https://v2.cinecalidad.men/', 'https://v3.cinecalidad.men/', 'https://v4.cinecalidad.men/',
             'https://v5.cinecalidad.men/', 'https://www.cinecalidad.gg/', 'https://wvw.cinecalidad.gg/',
             'https://wwv.cinecalidad.gg/', 'https://vww.cinecalidad.gg/', 'https://vvv.cinecalidad.gg/'
             'https://ww.cinecalidad.gg/', 'https://w.cinecalidad.gg/', 'https://vvw.cinecalidad.gg/',
             'https://wv.cinecalidad.gg/', 'https://vwv.cinecalidad.gg/', 'https://wwc.cinecalidad.gg/',
             'https://cww.cinecalidad.gg/', 'https://oww.cinecalidad.gg/', 'https://wow.cinecalidad.gg/',
             'https://woo.cinecalidad.gg/', 'https://oow.cinecalidad.gg/', 'https://wwe.cinecalidad.gg/',
             'https://wwm.cinecalidad.gg/', 'https://mww.cinecalidad.gg/', 'https://wmw.cinecalidad.gg/',
             'https://wwa.cinecalidad.gg/', 'https://aww.cinecalidad.gg/', 'https://waw.cinecalidad.gg/',
             'https://wwz.cinecalidad.gg/', 'https://wwu.cinecalidad.gg/', 'https://wuw.cinecalidad.gg/',
             'https://wee.cinecalidad.gg/', 'https://eew.cinecalidad.gg/', 'https://wwx.cinecalidad.gg/',
             'https://xww.cinecalidad.gg/', 'https://wxw.cinecalidad.gg/']


domain = config.get_setting('dominio', 'cinecalidadlol', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'cinecalidadlol')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'cinecalidadlol')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_cinecalidadlol_proxies', default=''):
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
    if config.get_setting('channel_cinecalidadlol_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('cinecalidadlol', url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('CineCalidadLoL', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('cinecalidadlol', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
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
                        data = httptools.downloadpage_proxy('cinecalidadlol', url, post=post, headers=headers, raise_weberror=raise_weberror).data
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

    domain_memo = config.get_setting('dominio', 'cinecalidadlol', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_cinecalidadlol', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='cinecalidadlol', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_cinecalidadlol', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_cinecalidadlol', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('cinecalidadlol') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'cinecalidadlol', thumbnail=config.get_thumb('cinecalidadlol') ))

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
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'espana/?ref=es', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Más vistas', action = 'destacadas', url = host + 'espana/?ref=es', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - En [COLOR moccasin]4K[/COLOR]', action = 'list_all', url = host + 'genero-de-la-pelicula/peliculas-en-calidad-4k/?ref=es', search_type = 'movie' ))

    itemlist.append(item.clone( title = '[B]En latino:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Más vistas', action = 'destacadas', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - En [COLOR moccasin]4K[/COLOR]', action = 'list_all', url = host + 'genero-de-la-pelicula/peliculas-en-calidad-4k/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action='anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = '[B]En castellano:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'ver-serie/?ref=es', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = ' - Por género', action='generos', search_type = 'tvshow', group = '?ref=es' ))

    itemlist.append(item.clone( title = '[B]En latino:[/B]', folder=False, text_color='moccasin' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'ver-serie/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = ' - Por género', action='generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<ul id="menu-menu"(.*?)<a id="close_menu"')

    matches = re.compile('href="(.*?)">(.*?)</a>').findall(bloque)

    for url, title in matches:
        title = title.strip()

        if title == '4K UHD': continue
        elif title == 'Estrenos': continue
        elif title == 'Destacadas': continue
        elif title == 'Series': continue

        if config.get_setting('descartar_anime', default=False):
            if title == 'Anime': continue

        url = host[:-1] + url

        if item.group == '?ref=es': url = url + item.group

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1936, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color ='deepskyblue'  ))

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

        if url.startswith('/?post_id='): continue

        elif '-premium-12-meses' in url or '-premium-1-ano' in url or '-12-meses' in url or '/netflix/o/' in url or '/product/' in url or '.ggpickaff.' in url:
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
        else: year = ''

        if not year:
            year = scrapertools.find_single_match(match, '</p>.*?<p>(.*?)</p>')
            if not year: year ='-'

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#038;', '&')

        tipo = 'tvshow' if '/ver-serie/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if item.search_type == 'movie':
            if '/ver-serie/' in url: continue
        elif item.search_type == 'tvshow':
            if not '/ver-serie/' in url: continue

        if '/espana/' in item.url:
            if not '?ref=es' in item.url: url = url + '?ref=es'

        if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")

        if not year: year = '-'

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
        next_page = scrapertools.find_single_match(data, "<span class='pages'>.*?class='current'>.*?" + 'href="(.*?)"')
        if not next_page: next_page = scrapertools.find_single_match(data, '<span class="pages">.*?class="current">.*?' + 'href="(.*?)"')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title='Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))
    else:
        if not _promos == 0:
            next_page = scrapertools.find_single_match(data, "<span class='pages'>.*?class='current'>.*?" + 'href="(.*?)"')
            if not next_page: next_page = scrapertools.find_single_match(data, '<span class="pages">.*?class="current">.*?' + 'href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title='Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Destacadas</h2>(.*?)>Herramientas')

    matches = scrapertools.find_multiple_matches(bloque, '<a(.*?)</li>')

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if item.search_type == 'movie':
            if '/ver-serie/' in url: continue
        else:
            if '/ver-pelicula/' in url: continue

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else: year = ''

        if not year:
            year = scrapertools.find_single_match(match, '</p>.*?<p>(.*?)</p>')
            if not year: year = '-'

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

    matches = scrapertools.find_multiple_matches(data, '<span data-tab="(.*?)"')

    for tempo in matches:
        title = 'Temporada ' + tempo

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = item.url, page = 0, contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<b>Temporada ' + str(item.contentSeason) + '(.*?)</div></div>')

    matches = scrapertools.find_multiple_matches(bloque, '<li class="mark-.*?data-src="(.*?)".*?<div class="numerando">(.*?)</div>.*?<a href="(.*?)">(.*?)</a')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('CineCalidadLol', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, temp_epis, url, title in matches[item.page * item.perpage:]:
        epis = scrapertools.find_single_match(temp_epis, '.*?E(.*?)$')
        if not epis: epis = '0'

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

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

    lang = 'Lat'

    if '?ref=es' in item.url: lang = 'Esp'

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '>No hay opciones para ver en latino' in data:
        new_url = scrapertools.find_single_match(data, ">No hay opciones para ver en latino.*?<a href='(.*?)'>Ver en castellano<")
        if not new_url: new_url = scrapertools.find_single_match(data, '>No hay opciones para ver en latino.*?<a href="(.*?)">Ver en castellano<')

        if new_url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR yellowgreen][B]Sin opciones Play en Latino[/B][/COLOR]')

            item.url = new_url

            data = do_downloadpage(item.url)
            data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

            if '?ref=es' in item.url: lang = 'Esp'

    ses = 0

    if '>VER ONLINE<' in data:
        bloque = scrapertools.find_single_match(data, '>VER ONLINE<(.*?)>DESCARGAR<')

        if not '/flags/' in bloque:
            matches = scrapertools.find_multiple_matches(bloque, '<li id="player-option-.*?data-option="(.*?)">(.*?)<')

            for url, srv in matches:
                ses += 1

                if '/play/' in url: continue
                elif 'youtube' in url: continue

                srv = srv.lower().strip()

                if srv == 'vip': continue
                elif '1fichier' in srv: continue

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                qlty = '1080'

                language = lang

                other = ''

                if servidor == 'directo':
                    if srv == 'streamtape': servidor = 'streamtape'
                    elif srv == 'voe': servidor = 'voe'
                    elif srv == 'doods' or srv == 'doostream': servidor = 'doodstream'
                    elif srv == 'lamovie': servidor = 'clipwatching'

                    elif srv == 'netu' or servidor == 'hqq': servidor = 'waaw'

                    elif '/okru.' in url: servidor = 'okru'

                    else: servidor = servertools.corregir_servidor(srv)

                if servidor == 'various': other = srv.capitalize()

                itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                      quality = qlty, language = language, other = other ))

        else:

            matches = scrapertools.find_multiple_matches(bloque, '<li id="player-option-.*?data-option="(.*?)">(.*?)<.*?src=.*?/flags/(.*?).png')

            for url, srv, idio in matches:
                ses += 1

                if '/play/' in url: continue
                elif 'youtube' in url: continue

                srv = srv.lower().strip()

                if srv == 'vip': continue
                elif '1fichier' in srv: continue

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                qlty = '1080'

                language = lang
                if not '?ref=es' in item.url:
                   if idio == 'mx': language = 'Lat'
                   elif idio == 'es': language = 'Esp'
                   elif idio == 'en': language = 'Vose'
                else:
                   if idio == 'en': language = 'Vose'

                other = ''

                if servidor == 'directo':
                    if srv == 'streamtape': servidor = 'streamtape'
                    elif srv == 'voe': servidor = 'voe'
                    elif srv == 'doods' or srv == 'doostream': servidor = 'doodstream'
                    elif srv == 'lamovie': servidor = 'clipwatching'

                    elif srv == 'netu' or servidor == 'hqq': servidor = 'waaw'

                    elif '/okru.' in url: servidor = 'okru'

                    else: servidor = servertools.corregir_servidor(srv)

                if servidor == 'various': other = srv.capitalize()

                itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                      quality = qlty, language = language, other = other ))

    if '>DESCARGAR<' in data:
        bloque = scrapertools.find_single_match(data, '>DESCARGAR<(.*?)</ul>')

        matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)".*?">(.*?)</li>')

        for url, servidor in matches:
            ses += 1

            if url == '#':
                ses = ses - 1
                continue
            elif not servidor:
                ses = ses - 1
                continue
            elif '<div class="episodiotitle">' in servidor:
                ses = ses - 1
                continue

            qlty = '1080'

            if '<span' in servidor:
                if 'utorrent' in servidor.lower() or 'torrent' in servidor.lower():
                    qlty = scrapertools.find_single_match(servidor, '.*?">(.*?)</span>')

                servidor = scrapertools.find_single_match(servidor, '(.*?)<span')

            servidor = servidor.lower().strip()

            if '4k' in servidor or '4K' in servidor:
               qlty = '4K'
               servidor = servidor.replace('4k', '').replace('4K', '').strip()

            if servidor == 'subtítulos' or 'subtitulo' in servidor: continue

            elif 'forzado' in servidor: continue
            elif 'cinecalidad' in servidor: continue

            elif servidor == 'uptostream': continue

            elif servidor == 'utorrent': servidor = 'torrent'
            elif 'utorrent' in servidor: servidor = 'torrent'
            elif 'torrent' in servidor: servidor = 'torrent'

            elif servidor == 'google': servidor = 'gvideo'
            elif servidor == 'drive': servidor = 'gvideo'
            elif servidor == 'google drive': servidor = 'gvideo'

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            other = ''
            if url.startswith('?download='):
                other = 'D'
                url = item.url.replace('?ref=es', '') + url

            itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                  quality = qlty, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'cinecalidadlol', default='')

    if domain_memo: host_player = domain_memo
    else: host_player = host

    url = item.url

    url = url.replace('/netu.cinecalidad.com.mx/', '/waaw.to/')

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

                    platformtools.dialog_ok(config.__addon_name + ' CineCalidadLol', '[COLOR cyan][B]Al parecer el Canal cambió de Dominio.[/B][/COLOR]', '[COLOR yellow][B]' + url_avis + '[/B][/COLOR]', 'Por favor, Reviselo en [COLOR goldenrod][B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]')
                    return itemlist

    if host_player in url or str(_players) in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, 'target="_blank" href="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, 'target="_blank" value="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<iframe.*?data-src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, 'window.location.href = "(.*?)"')
        if not url: url = scrapertools.find_single_match(data, "window.location.href = '(.*?)'")
        if not url: url = scrapertools.find_single_match(data, 'data-href="(.*?)"')

        if '/?id=' in url:
            data = do_downloadpage(url)

            url: url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

        if url:
            url = url.replace('&amp;', '&')

            if url:
                url = url.replace('/netu.cinecalidad.com.mx/', '/waaw.to/')

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                if servidor == 'mega':
                    if url.startswith('#'): url = 'https://mega.nz/' + url
                    elif not url.startswith('http'): url = 'https://mega.nz/file/' + url

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
                    data = requeststools.read(url, 'cinecalidadlol')
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
