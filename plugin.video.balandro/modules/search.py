# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3: PY3 = True
else: PY3 = False


import os, time

from threading import Thread

from platformcode import config, logger, platformtools
from core.item import Item
from core import channeltools, scrapertools


fanart = os.path.join(config.get_runtime_path(), 'fanart.jpg')


color_list_prefe = config.get_setting('channels_list_prefe_color', default='gold')
color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')
color_list_inactive = config.get_setting('channels_list_inactive_color', default='gray')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')


search_no_accesibles = config.get_setting('search_no_accesibles', default=False)


srv_pending = ''
con_incidencias = ''
no_accesibles = ''
con_problemas = ''

try:
    with open(os.path.join(config.get_runtime_path(), 'dominios.txt'), 'r') as f: txt_status=f.read(); f.close()
except:
    try: txt_status = open(os.path.join(config.get_runtime_path(), 'dominios.txt'), encoding="utf8").read()
    except: txt_status = ''

if txt_status:
    # ~ Pending
    bloque = scrapertools.find_single_match(txt_status, 'SITUACION SERVIDORES(.*?)SITUACION CANALES')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR orchid]' in match: srv_pending += '[B' + match + '/I][/B][/COLOR][CR]'

    # ~ Incidencias
    bloque = scrapertools.find_single_match(txt_status, 'SITUACION CANALES(.*?)CANALES TEMPORALMENTE DES-ACTIVADOS')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR moccasin]' in match: con_incidencias += '[B' + match + '/I][/B][/COLOR][CR]'

    # ~ No Accesibles
    bloque = scrapertools.find_single_match(txt_status, 'CANALES PROBABLEMENTE NO ACCESIBLES(.*?)ULTIMOS CAMBIOS DE DOMINIOS')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR moccasin]' in match: no_accesibles += '[B' + match + '/I][/B][/COLOR][CR]'

    # ~ Con Problemas
    bloque = scrapertools.find_single_match(txt_status, 'CANALES CON PROBLEMAS(.*?)$')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR moccasin]' in match: con_problemas += '[B' + match + '/I][/B][/COLOR][CR]'

    if con_problemas:
        hay_problemas = str(con_problemas).replace('[B][COLOR moccasin]', 'CHANNEL').replace('[COLOR lime]', '/CHANNEL')
        channels_con_problemas = scrapertools.find_multiple_matches(hay_problemas, "CHANNEL(.*?)/CHANNEL")

no_results_proxies = config.get_setting('search_no_results_proxies', default=True)
no_results = config.get_setting('search_no_results', default=False)

context_cfg_search = []

tit = '[COLOR green][B]Información Búsquedas[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_help_search'})

tit = '[COLOR violet][B]Info Búsquedas Tmdb[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'tmdblists', 'action': 'show_help'})

tit = '[COLOR darkcyan][B]Info Búsquedas Filmaffinity[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'filmaffinitylists', 'action': 'show_help'})

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR fuchsia][B]Preferencias Play[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_play_parameters'})

tit = '[COLOR powderblue][B]Preferencias Buscar[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_help_parameters_search'})

tit = '[COLOR red][B]Preferencias Proxies[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_prx_parameters'})

tit = '[COLOR %s]Ajustes categoría Menú y Buscar[/COLOR]' % color_exec
context_cfg_search.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


def mainlist(item):
    logger.info()
    itemlist = []

    thumb_filmaffinity = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'filmaffinity.jpg')
    thumb_tmdb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'tmdb.jpg')

    item.category = 'Buscar'

    itemlist.append(item.clone( action='', title='[B]BUSCAR:[/B]', folder=False, text_color='yellow' ))

    itemlist.append(item.clone( action='show_infos', title='[COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if config.get_setting('sub_mnu_cfg_search', default=True):
        itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'all', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

    if config.get_setting('sub_mnu_favoritos', default=False):
        if  item.mnupral == 'main':
             itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

    titulo = '[B]Búsquedas por Titulo:[/B]'
    if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False): titulo = '[B]Búsquedas por Título en los Canales:[/B]'

    itemlist.append(item.clone( action='', title= titulo, folder=False, text_color='chartreuse', thumbnail=config.get_thumb('stack') ))

    if config.get_setting('channels_link_main', default=True):
        itemlist.append(item.clone( action='search', search_type='all', title= ' - [COLOR yellow][B]Película y/ó Serie[/B][/COLOR] ...', plot = 'Indicar el Título para Buscarlo indistintamente en Películas y/ó Series en Todos los Canales' ))

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_pelis', default=True):
            itemlist.append(item.clone( action='search', search_type='movie', title= ' - [COLOR deepskyblue][B]Película[/B][/COLOR] ...', thumbnail=config.get_thumb('movie'), plot = 'Indicar el Título de una Película para buscarla en los canales de Películas' ))

        if config.get_setting('mnu_series', default=True):
            itemlist.append(item.clone( action='search', search_type='tvshow', title= ' - [COLOR hotpink][B]Serie[/B][/COLOR] ...', thumbnail=config.get_thumb('tvshow'), plot = 'Indicar el Título de una Serie para buscarla en los Canales de Series' ))

        if config.get_setting('mnu_documentales', default=True):
            itemlist.append(item.clone( action='search', search_type='documentary', title= ' - [COLOR cyan][B]Documental[/B][/COLOR] ...', thumbnail=config.get_thumb('documentary'), plot = 'Indicar el Título de un Documental para buscarlo en los Canales de Documentales' ))

        if config.get_setting('mnu_torrents', default=True):
            if not config.get_setting('search_no_exclusively_torrents', default=False):
                itemlist.append(item.clone( action='search', search_type='all', title=' - [COLOR blue][B]Torrent[/B][/COLOR]', thumbnail=config.get_thumb('torrents'), search_special = 'torrent', plot = 'Indicar el Título para Buscarlo indistintamente en Películas y/ó Series Solo en los Canales Exlusivos de Torrents' ))

        if config.get_setting('mnu_doramas', default=True):
            itemlist.append(item.clone( action='search', search_type='all', title= ' - [COLOR firebrick][B]Dorama[/B][/COLOR] ...',  thumbnail=config.get_thumb('computer'), search_special = 'dorama', plot = 'Indicar el Título de un Dorama para buscarlo Solo en los Canales Exlusivos de Doramas' ))

        if config.get_setting('mnu_animes', default=True):
            if not config.get_setting('descartar_anime', default=True):
               itemlist.append(item.clone( action='search', search_type='all', title= ' - [COLOR springgreen][B]Anime[/B][/COLOR] ...', thumbnail=config.get_thumb('anime'), search_special = 'anime', plot = 'Indicar el Título de un Anime para buscarlo Solo en los Canales Exlusivos de Animes' ))

        if config.get_setting('mnu_adultos', default=True):
            itemlist.append(item.clone( action='search', title='- [B][COLOR orange]+18 Vídeo[/COLOR][/B] ...', extra = '+18', search_video = 'adult', thumbnail=config.get_thumb('adults'), text_color='yellow' ))

    if config.get_setting('search_extra_trailers', default=False):
         itemlist.append(item.clone( channel='trailers', action='search', title= ' - [COLOR darkgoldenrod][B]Tráiler[/B][/COLOR] ...', thumbnail=config.get_thumb('trailers'), plot = 'Indicar el Título de una película para buscar su Tráiler' ))

    itemlist.append(item.clone( action='', title= '[B]Búsquedas de Personas en los Canales:[/B]', thumbnail=config.get_thumb('stack'), text_color='salmon' ))

    itemlist.append(item.clone( title = ' - [COLOR aquamarine][B]Intérprete[/B][/COLOR] ...', action = 'search', search_type = 'person',
                                plot = 'Indicar el nombre y/ó apellido/s del intérprete.'))
    itemlist.append(item.clone( title = ' - [COLOR mediumaquamarine][B]Dirección[/B][/COLOR] ...', action = 'search', search_type = 'person',
                                plot = 'Indicars el nombre y/ó apellido/s del director.'))

    if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
        itemlist.append(item.clone( action='', title= '[B]Búsquedas Especiales:[/B]', folder=False, text_color='yellowgreen' ))

        itemlist.append(item.clone( channel='tmdblists', action='mainlist', title= ' - Búsquedas y listas en [COLOR violet][B]TMDB[/B][/COLOR]', thumbnail=thumb_tmdb, plot = 'Buscar personas y ver listas de películas y series de la base de datos de The Movie Database' ))

        itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', title= ' - Búsquedas y listas en [COLOR violet][B]Filmaffinity[/B][/COLOR]', thumbnail=thumb_filmaffinity, plot = 'Buscar personas y ver listas de películas, series ó documentales de Filmaffinity' ))

    return itemlist


def show_infos(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]BUSCAR Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_search', title=' - [COLOR green][B]Información [COLOR yellow]Búsquedas[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_audios', title= ' - [COLOR green][B]Información[/B][/COLOR] [COLOR cyan][B]Idiomas[/B][/COLOR] en los Audios de los Vídeos', thumbnail=config.get_thumb('news') ))

    if config.get_setting('mnu_torrents', default=True):
        itemlist.append(item.clone( channel='helper', action='show_help_semillas', title= ' - [COLOR green][B]Información[/B][/COLOR] archivos Torrent [COLOR goldenrod][B]Semillas[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' - Canales [COLOR gold][B]Resumen y Distribución[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='helper', action='channels_with_crypto', title= ' - Canales que requieren [COLOR darksalmon][B]Descifrar Enlaces[/B][/COLOR]' ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title=' - Canales [COLOR tan][B]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= ' - Canales [COLOR indianred][B]No Accesibles[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' - Canales [COLOR tomato][B]Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list_temporaries', title= ' - Canales que están [COLOR darkcyan][B]Temporalmente[/B][/COLOR] Inactivos', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='filters', action='no_actives', title= ' - Qué canales [COLOR goldenrod][B]Nunca[/B][/COLOR] intervendrán en las búsquedas', no_searchables = True, thumbnail=config.get_thumb('stack') ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_pending', title='[COLOR fuchsia][B]Servidores[COLOR orchid] Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    return itemlist


def show_infos_proxies(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR salmon][B]PROXIES Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_proxies', title= ' - [COLOR green][B]Información[/B][/COLOR] Uso de proxies', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_providers', title= ' - [COLOR green][B]Información[/B][/COLOR] Proveedores de proxies', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_providers2', title= ' - [COLOR green][B]Información[/B][/COLOR] Lista [COLOR aqua][B]Ampliada[/B][/COLOR] Proveedores de proxies', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_recommended', title= ' - Qué [COLOR green][B]Proveedores[/B][/COLOR] de proxies están [COLOR lime][B]Recomendados[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    return itemlist


def search(item, tecleado):
    logger.info()

    item.category = 'Buscar ' + tecleado
    if item.search_type == '': item.search_type = 'all'

    itemlist = do_search(item, tecleado)

    return itemlist


def do_search_channel(item, tecleado, ch):
    canal = __import__('channels.' + item.channel, fromlist=[''])

    if hasattr(canal, 'search'):
        ch['itemlist_search'] = canal.search(item, tecleado)
    else:
        logger.error('Search not found in channel %s. Implementar search o quitar searchable!' % item.channel)


def do_search(item, tecleado):
    HTTPTOOLS_DEFAULT_SEARCH_TIMEOUT = config.get_setting('search_timeout', default=5)

    config.set_setting('httptools_timeout_searching', HTTPTOOLS_DEFAULT_SEARCH_TIMEOUT)


    itemlist = []

    channels_new_proxies = []

    pro_cancel = False

    desde_lists = False

    if config.get_setting('search_no_work_proxies', default=False):
        config.set_setting('sin_resp', '')
        sin_results = False
    else:
        config.set_setting('sin_resp', 'no')
        no_results_proxies = True
        sin_results = True

    multithread = config.get_setting('search_multithread', default=True)

    threads = []

    search_limit_by_channel = config.get_setting('search_limit_by_channel', default=2)

    progreso = platformtools.dialog_progress('Buscando ' + '[B][COLOR chartreuse]' + tecleado + '[/B][/COLOR]', '...')

    search_person = False

    if item.search_type == 'person':
        search_person = True
        item.search_type = 'all'

    # ~ status para descartar desactivados por el usuario
    if item.search_special == 'anime' or item.search_special == 'dorama': filtros = {'status': 0 }

    elif item.extra == '+18': filtros = {'categories': 'adults', 'status': 0 }

    elif item.search_special == 'torrent': filtros = {'searchable': True, 'categories': 'torrent', 'status': 0 }

    else:
        if item.only_channels_group:
            if item.group == 'dorama': filtros = {'searchable': True, 'status': 0 }
            elif item.group == 'anime': filtros = {'searchable': True, 'status': 0 }
            else: filtros = {'searchable': True, 'status': 0 }
        else: filtros = {'searchable': True, 'status': 0 }

    if item.search_type != 'all':
        if item.only_channels_group:
            if not item.group == 'docs': filtros['search_types'] = item.search_type
        else:
            if item.search_type == 'documentary': filtros['search_types'] = 'all'
            else: filtros['search_types'] = item.search_type
    else:
        if item.only_channels_group:
            if not item.group == 'tales':
                if not item.group == 'torrents':
                    if not item.group == 'dorama':
                        if not item.group == 'anime':
                            if not item.group == 'adults':
                                filtros['search_types'] = item.search_type

    ch_list = channeltools.get_channels_list(filtros=filtros)

    # ~ descartar from_channel (búsqueda en otros canales)
    if item.from_channel != '':
        ch_list = [ch for ch in ch_list if ch['id'] != item.from_channel]

    if item.search_type == 'all':
        if item.only_channels_group and (item.group == 'docs' or item.group == '3d'): pass
        else: ch_list = [ch for ch in ch_list if 'documentary' not in ch['categories']]

    num_canales = float(len(ch_list))

    only_torrents = ''
    if item.extra == 'only_torrents': only_torrents = item.extra

    only_prefered = config.get_setting('search_only_prefered', default=False)
    only_suggesteds = config.get_setting('search_only_suggesteds', default=False)

    con_torrents = config.get_setting('search_con_torrents', default=False)
    no_torrents = config.get_setting('search_no_torrents', default=False)
    no_exclusively_torrents = config.get_setting('search_no_exclusively_torrents', default=False)

    no_inestables = config.get_setting('search_no_inestables', default=False)
    no_proxies = config.get_setting('search_no_proxies', default=False)

    no_problematicos = config.get_setting('search_no_problematicos', default=False)

    no_clones = config.get_setting('search_no_clones', default=False)

    no_channels = config.get_setting('search_no_channels', default=False)

    only_includes = config.get_setting('search_included_all', default='')

    no_notices = config.get_setting('search_no_notices', default='')

    no_cryptos = config.get_setting('search_no_cryptos', default='')

    if item.search_type == 'movie':
        channels_search_excluded = config.get_setting('search_excludes_movies', default='')

    elif item.search_type == 'tvshow':
        channels_search_excluded = config.get_setting('search_excludes_tvshows', default='')

    elif item.search_type == 'documentary':
        channels_search_excluded = config.get_setting('search_excludes_documentaries', default='')

    elif item.extra == 'only_torrents':
        channels_search_excluded = config.get_setting('search_excludes_torrents', default='')
    else:
        channels_search_excluded = config.get_setting('search_excludes_mixed', default='')
        channels_search_excluded = channels_search_excluded + config.get_setting('search_excludes_all', default='')

    for i, ch in enumerate(ch_list):
        if search_person:
            if 'stars'in ch['clusters']: pass
            elif 'directors'in ch['clusters']: pass

            else:
               num_canales -= 1
               continue

        if 'temporary' in ch['clusters']:
            num_canales -= 1
            continue

        if item.extra == '+18':
            if not 'adults' in ch['categories']:
                num_canales -= 1
                continue
        else:
            if 'adults' in ch['categories']:
               num_canales -= 1
               continue

        if not PY3:
            if 'mismatched' in ch['clusters']:
                num_canales -= 1
                continue

        if item.search_type == 'documentary':
            if 'documentary' in ch['categories']: pass
            else:
               if not 'docs' in ch['clusters']:
                   num_canales -= 1
                   continue

        if item.search_special == 'torrent':
            if not 'torrents' in ch['clusters']:
                num_canales -= 1
                continue

        if item.search_special == 'dorama':
            if 'exclusivamente al dorama' in ch['notes']: pass
            else:
               if not 'dorama' in ch['clusters']:
                   num_canales -= 1
                   continue

        if item.search_special == 'anime':
            if 'exclusivamente al anime' in ch['notes']: pass
            else:
               if not 'anime' in ch['clusters']:
                   num_canales -= 1
                   continue

        if con_torrents:
            if not 'torrents' in ch['clusters']:
                 num_canales -= 1
                 continue

        if no_torrents:
            if 'torrents' in ch['clusters']:
                num_canales -= 1
                continue

        if no_exclusively_torrents:
            if 'enlaces torrent exclusivamente' in ch['notes'].lower():
                 num_canales -= 1
                 continue

        if 'register' in ch['clusters']:
            sesion_login = config.get_setting('channel_%s_%s_login' % (ch['id'], ch['id']), default=False)
            if sesion_login == False:
                num_canales -= 1
                continue

        if no_inestables or config.get_setting('mnu_simple', default=False):
            if 'inestable' in ch['clusters']:
                num_canales -= 1
                continue

        if no_problematicos or config.get_setting('mnu_simple', default=False):
            if 'problematic' in ch['clusters']:
                num_canales -= 1
                continue

        if no_clones or config.get_setting('mnu_simple', default=False):
            if 'clone' in ch['clusters']:
                num_canales -= 1
                continue

        if item.only_channels_group:
            if not ("'" + ch['id'] + "'") in str(item.only_channels_group): continue

        if not search_no_accesibles:
            if no_accesibles:
                if ch['name'] in str(no_accesibles):
                    num_canales -= 1
                    continue

            if con_problemas:
                if ch['name'] in str(con_problemas):
                    found_problema = False

                    for channel_con_problema in channels_con_problemas:
                        channel_con_problema = channel_con_problema.strip()

                        if not channel_con_problema == ch['name']: continue

                        found_problema = True
                        num_canales -= 1
                        break

                    if found_problema: continue

        if not multithread:
            perc = int(i / num_canales * 100)

            progreso.update(perc, 'Acceso al canal [COLOR cyan][B]%s[/B][/COLOR]' % (ch['name']))

        c_item = Item( channel=ch['id'], action='search', search_type=item.search_type, title='Buscar en ' + ch['name'], thumbnail=ch['thumbnail'] )

        if no_proxies:
            if 'proxies' in ch['notes'].lower():
                cfg_proxies_channel = 'channel_' + ch['name'].lower() + '_proxies'
                if config.get_setting(cfg_proxies_channel, default=''):
                    if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por proxies[/COLOR][/B]' % color_adver)

                    num_canales -= 1
                    continue

        if only_includes:
            channels_preselct = str(only_includes).replace('[', '').replace(']', ',')
            if not ("'" + ch['id'] + "'") in str(channels_preselct):
                if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado no está en Incluidos[/COLOR][/B]' % color_exec)

                num_canales -= 1
                continue

        if no_notices:
            if 'notice' in ch['clusters']:
                if only_includes:
                    channels_preselct = str(only_includes).replace('[', '').replace(']', ',')
                    if not ("'" + ch['id'] + "'") in str(channels_preselct):
                        if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado no está en Incluidos[/COLOR][/B]' % color_exec)

                        num_canales -= 1
                        continue
                else:
                    if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por CloudFlare Protection[/COLOR][/B]' % color_exec)
                    num_canales -= 1
                    continue

        if no_cryptos:
            if 'crypto' in ch['clusters']:
                if only_includes:
                    channels_preselct = str(only_includes).replace('[', '').replace(']', ',')
                    if not ("'" + ch['id'] + "'") in str(channels_preselct):
                        if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado no está en Incluidos[/COLOR][/B]' % color_exec)

                        num_canales -= 1
                        continue
                else:
                    if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por Enlaces Cifrados[/COLOR][/B]' % color_exec)
                    num_canales -= 1
                    continue

        if channels_search_excluded:
            channels_preselct = str(channels_search_excluded).replace('[', '').replace(']', ',')
            if ("'" + ch['id'] + "'") in str(channels_preselct):
                if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por Excluido[/COLOR][/B]' % color_exec)

                num_canales -= 1
                continue

        cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'
        if config.get_setting(cfg_searchable_channel, default=False):
            if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por Excluido[/COLOR][/B]' % color_adver)
            num_canales -= 1
            continue

        if item.only_channels_group:
            if not ("'" + ch['id'] + "'") in str(item.only_channels_group):
                num_canales -= 1
                continue
        else:
            if only_prefered:
                cfg_status_channel = 'channel_' + ch['name'].lower() + '_status'
                if not config.get_setting(cfg_status_channel, default=''):
                    num_canales -= 1
                    continue
            elif only_suggesteds:
                if not 'suggested' in ch['clusters']:
                   num_canales -= 1
                   continue
            elif only_torrents:
                if not 'torrents' in ch['clusters']:
                   num_canales -= 1
                   continue

        if multithread:
            t = Thread(target=do_search_channel, args=[c_item, tecleado, ch], name=ch['name'])
            t.setDaemon(True)
            t.start()
            threads.append(t)
        else:
            do_search_channel(c_item, tecleado, ch)

        if progreso.iscanceled():
            pro_cancel = True
            break

    if multithread:
        if PY3:
            pendent = [a for a in threads if a.is_alive()]
        else:
            pendent = [a for a in threads if a.isAlive()]

        while len(pendent) > 0:
            hechos = num_canales - len(pendent)
            perc = int(hechos / num_canales * 100)
            mensaje = ', '.join([a.getName() for a in pendent])

            progreso.update(perc, '[COLOR gold]Buscando[/COLOR] en el %d de %d canales. [COLOR chartreuse]Quedan[/COLOR] %d : %s' % (hechos, num_canales, len(pendent), mensaje))

            if progreso.iscanceled():
                pro_cancel = True
                break

            time.sleep(0.5)

            if PY3:
                pendent = [a for a in threads if a.is_alive()]
            else:
                pendent = [a for a in threads if a.isAlive()]

    nro = 0
    sin = 0
    sip = 0

    config.set_setting('sin_resp', 'si')

    # ~ Buscar desde Filmaffinity/Tmdb y tambien Exacto en los canales de una peli/serie
    if item.from_channel != '':
        desde_lists = True

        tecleado_lower = tecleado.lower()

        from_channel = item.from_channel
        mem_from_channel = from_channel

        text_cab = '[COLOR darkcyan][B]- buscar Exacto:[/COLOR] '

        if item.from_channel == 'filmaffinitylists':
            text_cab = '[COLOR violet]- buscar desde Filmaffinity:[/COLOR] '
            from_channel = 'filmaffinitylists'
        elif item.from_channel == 'tmdblists':
            text_cab = '[COLOR violet]- buscar desde Tmdb:[/COLOR] '
            from_channel = 'tmdb'

        title = '[B][I]' + text_cab + tecleado + '[/I][/B]'

        itemlist.append(item.clone( action='', title=title, context=context_cfg_search, from_channel=from_channel, contentExtra='3', thumbnail=config.get_thumb('search'), text_color='yellow' ))

        for ch in ch_list:
            if 'itemlist_search' in ch and len(ch['itemlist_search']) > 0:
                for it in ch['itemlist_search']:
                    if it.contentType not in ['movie','tvshow','season']: continue
                    if it.infoLabels['tmdb_id'] and item.infoLabels['tmdb_id']:
                        if it.infoLabels['tmdb_id'] != item.infoLabels['tmdb_id']: continue
                    else:
                        if it.contentType == 'movie' and it.contentTitle.lower() != tecleado_lower: continue
                        if it.contentType in ['tvshow','season'] and it.contentSerieName.lower() != tecleado_lower: continue

                    if no_inestables or config.get_setting('mnu_simple', default=False):
                        if 'inestable' in ch['clusters']: continue

                    if no_problematicos or config.get_setting('mnu_simple', default=False):
                        if 'problematic' in ch['clusters']: continue

                    if no_clones or config.get_setting('mnu_simple', default=False):
                        if 'clone' in ch['clusters']: continue

                    color = 'chartreuse'

                    name = ch['name']

                    if ch['status'] == 1: name += '[I][COLOR wheat] (preferido) [/COLOR][/I]'

                    if 'proxies' in ch['notes'].lower():
                        cfg_proxies_channel = 'channel_' + ch['name'].lower() + '_proxies'
                        if config.get_setting(cfg_proxies_channel, default=''): color = color_list_proxies

                    if 'inestable' in ch['clusters']: name += '[I][COLOR plum] (inestable) [/COLOR][/I]'
                    if 'problematic' in ch['clusters']: name += '[I][COLOR darkgoldenrod] (problemático) [/COLOR][/I]'
                    if 'clone' in ch['clusters']: name += '[I][COLOR turquoise] (clon) [/COLOR][/I]'

                    if con_incidencias:
                        if ch['name'] in str(con_incidencias):
                            name += '[I][COLOR tan] (incidencia)[/COLOR][/I]'

                    if search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): name += '[I][COLOR indianred] (no accesible)[/COLOR][/I]'
                            else: continue

                        if con_problemas:
                            if ch['name'] in str(con_problemas):
                                found_problema = False

                                for channel_con_problema in channels_con_problemas:
                                    channel_con_problema = channel_con_problema.strip()

                                    if not channel_con_problema == ch['name']: continue

                                    found_problema = True
                                    name += '[I][COLOR tomato] (con problema)[/COLOR][/I]'
                                    break

                                if not found_problema: continue

                    it.title = '[B][COLOR ' + color + ']' + name + '[/B][/COLOR] ' + it.title

                    it.thumbnail = ch['thumbnail']

                    it.contentExtra = from_channel

                    itemlist.append(it)

        item.from_channel = mem_from_channel

    else:
        # ~ Búsqueda parecida en todos los canales : link para acceder a todas las coincidencias y previsualización de n enlaces por canal
        titulo = ''

        for ch in sorted(ch_list, key=lambda ch: True if 'itemlist_search' not in ch or len(ch['itemlist_search']) == 0 else False):
            action = ''

            cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

            if 'itemlist_search' in ch:
                if not PY3:
                    if 'mismatched' in ch['clusters']:
                        if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por incompatible[/COLOR][/B]' % color_exec)
                        continue

                if len(ch['itemlist_search']) == 0:
                    action = 'mainlist'

                    if config.get_setting(cfg_proxies_channel, default=''):
                        if not config.get_setting('search_no_results_proxies', default=True): continue

                    sin += 1

                    if sin == 1:
                        if not search_person:
                            if not item.extra == '+18':
                                title = '[B][I]- CANALES:  [COLOR red]Sin Resultados[/COLOR][/I][/B]'
                                if len(itemlist) == 0: title = title + ' [COLOR turquoise](compruebe el Texto Buscado)[/COLOR]'

                                itemlist.append(item.clone( action='', title = title, thumbnail=config.get_thumb('search'), text_color='yellow' ))

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): continue

                        if con_problemas:
                            if ch['name'] in str(con_problemas):
                                found_problema = False

                                for channel_con_problema in channels_con_problemas:
                                    channel_con_problema = channel_con_problema.strip()

                                    if not channel_con_problema == ch['name']: continue

                                    found_problema = True

                                if not found_problema: continue

                    if no_results or sin_results:
                        titulo = ch['name']

                        if no_results_proxies:
                            if config.get_setting(cfg_proxies_channel, default=''):
                                if 'notice' in ch['clusters']: titulo = titulo + ' [COLOR goldenrod]Posible cloudflare[/COLOR]'
                                channels_new_proxies.append(ch['id'])
                                titulo = titulo + ' [COLOR red]quizás requiera [I]Nuevos Proxies[/I]'
                            else:
                                if 'proxies' in ch['notes'].lower():
                                    if 'notice' in ch['clusters']: titulo = titulo + ' [COLOR goldenrod]Posible cloudflare[/COLOR]'
                                    channels_new_proxies.append(ch['id'])
                                    titulo = titulo + ' [COLOR darkorange]quizás necesite [I]Configurar Proxies[/I]'

                        if no_results:
                            if sin_results:
                                if titulo == ch['name']:
                                    titulo = titulo + '  [COLOR coral]sin resultados[/COLOR]'
                                else:
                                    if not 'quizás' in titulo: continue
                        else:
                            if sin_results:
                                if not 'quizás' in titulo: continue
                                titulo = titulo + '  [COLOR coral]sin resultados[/COLOR]'

                    else:
                        if config.get_setting(cfg_proxies_channel, default=''):
                            if no_results_proxies:
                                titulo = ch['name']

                                if search_no_accesibles:
                                    if ch['name'] in str(no_accesibles): titulo = titulo + '[I][COLOR indianred] (no accesible) [/COLOR][/I]'
                                    else: continue

                                    if ch['name'] in str(con_problemas):
                                        found_problema = False

                                        for channel_con_problema in channels_con_problemas:
                                            channel_con_problema = channel_con_problema.strip()

                                            if not channel_con_problema == ch['name']: continue

                                            found_problema = True
                                            titulo = titulo + '[I][COLOR tomato] (con problema) [/COLOR][/I]'
                                            break

                                        if not found_problema: continue

                                channels_new_proxies.append(ch['id'])
                                if 'notice' in ch['clusters']: titulo = titulo + ' [COLOR goldenrod]Posible cloudflare[/COLOR]'
                                titulo = titulo + ' [COLOR red]quizás requiera [I]Nuevos Proxies[/I]'
                            else:
                                continue

                        else:
                            if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado sin resultados[/COLOR][/B]' % color_avis)
                            continue
                else:
                    action = 'search'
                    texto = 'resultados'

                    if len(ch['itemlist_search']) == 1: texto = 'resultado'

                    name = ch['name']

                    color = 'chartreuse'

                    if ch['status'] == 1: name += '[I][COLOR wheat] (preferido) [/COLOR][/I]'

                    if 'proxies' in ch['notes'].lower():
                        cfg_proxies_channel = 'channel_' + ch['name'].lower() + '_proxies'
                        if config.get_setting(cfg_proxies_channel, default=''): color = color_list_proxies

                    if 'inestable' in ch['clusters']: name += '[I][COLOR plum] (inestable)[/COLOR][/I]'
                    if 'problematic' in ch['clusters']: name += '[I][COLOR darkgoldenrod] (problemático)[/COLOR][/I]'
                    if 'clone' in ch['clusters']: name += '[I][COLOR turquoise] (clon)[/COLOR][/I]'

                    if con_incidencias:
                        if ch['name'] in str(con_incidencias):
                            name += '[I][COLOR tan] (incidencia)[/COLOR][/I]'

                    if search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): name += '[I][COLOR indianred] (no accesible)[/COLOR][/I]'
                            else: continue

                        if con_problemas:
                            if ch['name'] in str(con_problemas):
                                found_problema = False

                                for channel_con_problema in channels_con_problemas:
                                    channel_con_problema = channel_con_problema.strip()

                                    if not channel_con_problema == ch['name']: continue

                                    found_problema = True
                                    name += '[I][COLOR tomato] (con problema)[/COLOR][/I]'
                                    break

                                if not found_problema: continue

                    titulo = '%s [COLOR %s]- %d %s' % (name, color, len(ch['itemlist_search']), texto)
            else:
                if pro_cancel: titulo = '%s [COLOR cyan]búsqueda cancelada' % ch['name']
                else:
                    if item.only_channels_group:
                        if not ("'" + ch['id'] + "'") in str(item.only_channels_group): continue

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): continue

                        if con_problemas:
                            if ch['name'] in str(con_problemas):
                                found_problema = False

                                for channel_con_problema in channels_con_problemas:
                                    channel_con_problema = channel_con_problema.strip()

                                    if not channel_con_problema == ch['name']: continue

                                    found_problema = True
                                    break

                                if found_problema: continue

                    titulo = '%s [COLOR plum]No se ha buscado' % ch['name']

                    if item.extra == '+18':
                        if not 'adults' in ch['categories']: continue

                    if item.search_special == 'torrent':
                        if not 'torrents' in ch['clusters']: continue

                    if item.search_special == 'dorama':
                        if not 'dorama' in ch['clusters']: continue

                    if item.search_special == 'anime':
                        if not 'anime' in ch['clusters']: continue

                    if not PY3:
                        if 'mismatched' in ch['clusters']:
                            if no_channels: platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por incompatible[/COLOR][/B]' % color_exec)
                            continue

                    if con_torrents:
                        if not 'torrents' in ch['clusters']: continue

                    if no_torrents:
                        if 'torrents' in ch['clusters']: continue

                    if no_exclusively_torrents:
                       if 'enlaces torrent exclusivamente' in ch['notes'].lower(): continue

                    if no_inestables or config.get_setting('mnu_simple', default=False):
                        if 'inestable' in ch['clusters']: continue

                    if no_problematicos or config.get_setting('mnu_simple', default=False):
                        if 'problematic' in ch['clusters']: continue

                    if no_clones or config.get_setting('mnu_simple', default=False):
                        if 'clone' in ch['clusters']: continue

                    if no_proxies:
                        if 'proxies' in ch['notes'].lower():
                            if config.get_setting(cfg_proxies_channel, default=''):
                                if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado por proxies'
                                continue

                    if only_includes:
                        channels_preselct = str(only_includes).replace('[', '').replace(']', ',')
                        if not ("'" + ch['id'] + "'") in str(channels_preselct):
                            if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado no está en Incluidos'
                            continue

                    if no_notices:
                        if 'notice' in ch['clusters']:
                            if only_includes:
                                channels_preselct = str(only_includes).replace('[', '').replace(']', ',')
                                if not ("'" + ch['id'] + "'") in str(channels_preselct):
                                    if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado no está en Incluidos'
                                    continue

                            else:
                                if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado por CloudFlare Protection'
                                continue

                    if no_cryptos:
                        if 'crypto' in ch['clusters']:
                            if only_includes:
                                channels_preselct = str(only_includes).replace('[', '').replace(']', ',')
                                if not ("'" + ch['id'] + "'") in str(channels_preselct):
                                    if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado no está en Incluidos'
                                    continue

                            else:
                                if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado por Enlaces Cifrados'
                                continue

                    if channels_search_excluded:
                        channels_preselct = str(channels_search_excluded).replace('[', '').replace(']', ',')
                        if ("'" + ch['id'] + "'") in str(channels_preselct):
                            if no_channels: titulo = titulo + ' [COLOR cyan]Ignorado por Excluido'
                            continue

                    cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'
                    if config.get_setting(cfg_searchable_channel, default=False):
                        if no_channels: titulo = titulo + ' [COLOR cyan]Ignorado por Excluido'
                        continue
                    else:
                       if only_prefered: continue
                       elif only_suggesteds: continue
                       elif only_torrents: continue

                       elif 'register' in ch['clusters']:
                           username = config.get_setting(ch['id'] + '_username', ch['id'], default='')
                           if not username: titulo = titulo + ' [COLOR teal]faltan [I]Credenciales Cuenta[/I]'
                           else:
                               sesion_login = config.get_setting('channel_%s_%s_login' % (ch['id'], ch['id']), default=False)
                               if sesion_login == False: titulo = titulo + ' [COLOR teal]falta [I]Iniciar Sesion[/I]'
                       elif only_includes:
                           if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado no está en Incluidos'
                       elif no_notices:
                           if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado por CloudFlare Protection'
                       elif no_cryptos:
                           if no_channels: titulo = titulo + ' [COLOR yellow]Ignorado por Enlaces Cifrados'
                       elif 'proxies' in ch['notes'].lower(): titulo = titulo + ' [COLOR red]comprobar si [I]Necesita Proxies[/I]'
                       else:
                           if channels_search_excluded:
                               channels_preselct = str(channels_search_excluded).replace('[', '').replace(']', ',')
                               if ("'" + ch['id'] + "'") in str(channels_preselct):
                                   if no_channels: titulo = titulo + ' [COLOR cyan]Ignorado por Excluido'

                           else:
                              cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'
                              if config.get_setting(cfg_searchable_channel, default=False):
                                  if no_channels: titulo = titulo + ' [COLOR cyan]Ignorado por Excluido'
                              else: titulo = titulo + ' [COLOR yellow]comprobar el canal'

            nro += 1

            if nro == 1:
                text_cab = '[COLOR darkcyan][B]- Buscado:[/COLOR] '

                if item.search_type == 'movie':
                    text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR deepskyblue]Película: [/COLOR]'
                elif item.search_type == 'tvshow':
                    text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR hotpink]Serie: [/COLOR]'
                elif item.search_type == 'all':
                    if item.extra == '+18':
                        text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR orange]Vídeo: [/COLOR]'
                    elif item.search_special == 'anime':
                        text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR springgreen]Anime: [/COLOR]'
                    elif item.search_special == 'dorama':
                        text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR firebrick]Dorama: [/COLOR]'
                    elif item.search_special == 'torrent':
                        text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR blue]Torrent[/COLOR] [COLOR yellow]Película y/ó Serie: [/COLOR]'
                    else:
                        text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR yellow]Película y/ó Serie: [/COLOR]'
                elif item.search_type == 'documentary':
                    text_cab = '[COLOR darkcyan][B]- Buscado [/COLOR][COLOR cyan]Documental: [/COLOR]'

                mem_from_channel = item.from_channel

                if item.similar:
                    text_cab = '[COLOR darkcyan][B]- buscar Parecido:[/COLOR] '
                    item.from_channel = 'search'

                title = '[B][I]' + text_cab + tecleado + '[/I][/B]'

                itemlist.append(item.clone( action='', title=title, context=context_cfg_search, thumbnail=config.get_thumb('search'), text_color='yellow' ))

                if not sip == 0:
                    if config.get_setting('sub_mnu_cfg_prox_search', default=True):
                        itemlist.append(Item( channel='submnuctext', action='submnu_search', title='[B]Personalizar Próximas búsquedas[/B]', context=context_cfg_search, extra = item.search_type, thumbnail=config.get_thumb('help'), fanart=fanart, text_color='moccasin' ))

                    itemlist.append(item.clone( channel='helper', action='show_help_audios', title= '[COLOR green][B]Información[/B][/COLOR] [COLOR cyan][B]Idiomas[/B][/COLOR] en los Audios de los Vídeos', thumbnail=config.get_thumb('news'), fanart=fanart ))

                item.from_channel = mem_from_channel

            if not titulo:
                itemlist.append(Item( action = '', title = tecleado + '[COLOR coral]sin resultados en ningún canal[/COLOR]', fanart=fanart ))
                break

            context = []

            tit = '[COLOR cyan][B]Cambios Próximas Búsquedas[/B][/COLOR]'
            context.append({'title': tit, 'channel': '', 'action': ''})

            if ' Proxies' in titulo:
                tit = '[COLOR darkorange][B]Test Web del canal[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_tests'})

                if 'proxies' in ch['notes'].lower():
                    cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

                    if not config.get_setting(cfg_proxies_channel, default=''):
                        tit = '[COLOR %s]Información Proxies[/COLOR]' % color_infor
                        context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

                    tit = '[COLOR %s][B]Configurar proxies a usar[/B][/COLOR]' % color_list_proxies
                    context.append({'title': tit, 'channel': item.channel, 'action': '_proxies'})
            else:
                if 'proxies' in ch['notes'].lower():
                    cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

                    if config.get_setting(cfg_proxies_channel, default=''):
                        tit = '[COLOR darkorange][B]Test Web del canal[/B][/COLOR]'
                        context.append({'title': tit, 'channel': item.channel, 'action': '_tests'})

                        tit = '[COLOR %s]Información Proxies[/COLOR]' % color_infor
                        context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

                        tit = '[COLOR %s][B]Configurar proxies a usar[/B][/COLOR]' % color_list_proxies
                        context.append({'title': tit, 'channel': item.channel, 'action': '_proxies'})
                else:
                    tit = '[COLOR darkorange][B]Test Web del canal[/B][/COLOR]'
                    context.append({'title': tit, 'channel': item.channel, 'action': '_tests'})

            cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'

            if config.get_setting(cfg_searchable_channel, default=False):
                tit = '[COLOR %s][B]Quitar exclusión en búsquedas[/B][/COLOR]' % color_adver
                context.append({'title': tit, 'channel': item.channel, 'action': '_quitar_no_searchables'})
            else:
                tit = '[COLOR %s][B]Excluir de búsquedas[/B][/COLOR]' % color_adver
                context.append({'title': tit, 'channel': item.channel, 'action': '_poner_no_searchables'})

            if ch['status'] != 1:
                tit = '[COLOR %s][B]Marcar canal como Preferido[/B][/COLOR]' % color_list_prefe
                context.append({'title': tit, 'channel': 'actions', 'action': '_marcar_canales', 'estado': 1, 'canal': ch['id']})

            if ch['status'] != 0:
                if ch['status'] == 1:
                    tit = '[COLOR %s][B]Des-Marcar canal como Preferido[/B][/COLOR]' % color_list_prefe
                    context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})

            if ch['status'] != -1:
                tit = '[COLOR %s][B]Marcar canal como Desactivado[/B][/COLOR]' % color_list_inactive
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': -1})

            cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

            if ' (con problema)' in titulo: pass
            else:
               if not ' resultado' in titulo:
                   if desde_lists: pass
                   else:
                      if item.similar:
                           if not no_results:
                              if not config.get_setting(cfg_proxies_channel, default=''): continue

                           if not no_results_proxies:
                               if not config.get_setting(cfg_proxies_channel, default=''): continue

                      if not no_results:
                           if not config.get_setting(cfg_proxies_channel, default=''): titulo = ''

                      if not no_results_proxies:
                          if not config.get_setting(cfg_proxies_channel, default=''): titulo = ''

            if titulo:
                sip =+ 1

                color = 'chartreuse'

                titulo = '[B][COLOR %s]%s[/COLOR][/B]' % (color, titulo)

                itemlist.append(Item( channel=ch['id'], action=action, buscando=tecleado, title=titulo, module_search= True, context=context, thumbnail=ch['thumbnail'], fanart=fanart, search_type=item.search_type ))

            if 'itemlist_search' in ch:
                for j, it in enumerate(ch['itemlist_search']):
                    if it.contentType not in ['movie', 'tvshow', 'season']: continue
                    if j < search_limit_by_channel: itemlist.append(it)
                    else: break

            if 'búsqueda cancelada' in titulo: break

    if config.get_setting('sub_mnu_cfg_prox_search', default=True):
        if channels_new_proxies:
            if not sip == 0:
                itemlist.append(Item( channel='submnuctext', action='_search_new_proxies', title='[B][COLOR goldenrod]BUSCAR [COLOR red]Proxies[/COLOR] en [/COLOR][COLOR chartreuse]TODOS los Canales [/COLOR][COLOR coral]SIN RESULTADOS[/COLOR][/B]', channels_new_proxies = channels_new_proxies, extra = item.search_type, thumbnail=config.get_thumb('flame'), fanart=fanart ))

    progreso.close()

    if pro_cancel:
        if item.from_channel != '':
            titulo = '[COLOR chartreuse][B]%s [COLOR cyan]búsqueda cancelada[/B][/COLOR]' % ch['name']
            itemlist.append(Item( channel=ch['id'], action='', title=titulo, thumbnail=ch['thumbnail'], fanart=fanart ))

    if len(itemlist) == 0:
        if only_prefered: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda solo en preferidos[/COLOR][/B]' % color_infor)
        elif only_suggesteds: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda solo en sugeridos[/COLOR][/B]' % color_infor)
        elif only_torrents: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda solo en torrents[/COLOR][/B]' % color_infor)
        elif only_includes: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda solo en Incluidos[/COLOR][/B]' % color_infor)
        else: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda sin resultados[/COLOR][/B]' % color_infor)
    else:
        if nro == 0 and sip == 0:
            if not item.from_channel != '':
                platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda sin resultados[/COLOR][/B]' % color_infor)


    config.set_setting('httptools_timeout_searching', '')

    return itemlist


def _tests(item):
    from modules import submnuctext
    submnuctext._test_webs(item)


def _proxies(item):
    if platformtools.dialog_yesno(item.from_channel.capitalize(), '[COLOR yellow][B]Solo se tendrán en cuenta para las próximas búsquedas[/B][/COLOR]','[COLOR red][B]¿ Efectuar una nueva búsqueda de proxies en el canal ?[/B][/COLOR]'):
        from modules import submnuctext

        item.module_search = True
        submnuctext._proxies(item)


def _poner_no_searchables(item):
    from modules import submnuctext

    item.module_search = True
    submnuctext._poner_no_searchable(item)

def _quitar_no_searchables(item):
    from modules import submnuctext

    item.module_search = True
    submnuctext._quitar_no_searchable(item)
