# -*- coding: utf-8 -*-

import os

from platformcode import config, logger, platformtools
from core import channeltools, scrapertools
from core.item import Item


PY3 = False
if config.get_setting('PY3', default=''): PY3 = True


fanart = os.path.join(config.get_runtime_path(), 'fanart.jpg')


color_list_prefe = config.get_setting('channels_list_prefe_color', default='gold')
color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')
color_list_inactive = config.get_setting('channels_list_inactive_color', default='gray')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')


con_incidencias = ''
no_accesibles = ''
con_problemas = ''

try:
    with open(os.path.join(config.get_runtime_path(), 'dominios.txt'), 'r') as f: txt_status=f.read(); f.close()
except:
    try: txt_status = open(os.path.join(config.get_runtime_path(), 'dominios.txt'), encoding="utf8").read()
    except: txt_status = ''

if txt_status:
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


def mainlist(item):
    logger.info()
    itemlist = []

    if item.extra == 'doramas' or item.extra == 'animes':
        filtros = {'status': 0 }
    else:
        filtros = {'searchable': True, 'status': 0 }

    channels_list_status = config.get_setting('channels_list_status', default=0)
    if channels_list_status > 0:
        filtros['status'] = 0 if channels_list_status == 1 else 1

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if item.extra == 'movies':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR deepskyblue]Películas:[/I][/COLOR][/B]', thumbnail=config.get_thumb('movie'), fanart=fanart, text_color='darksalmon' ))

    elif item.extra == 'tvshows':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR hotpink]Series:[/I][/COLOR][/B]', thumbnail=config.get_thumb('tvshow'), fanart=fanart, text_color='darksalmon' ))

    elif item.extra == 'documentaries':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR cyan]Documentales:[/I][/COLOR][/B]', thumbnail=config.get_thumb('documentary'), fanart=fanart, text_color='darksalmon' ))

    elif item.extra == 'infantiles':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR lightyellow]Infantiles:[/I][/COLOR][/B]', thumbnail=config.get_thumb('booklet'), fanart=fanart, text_color='darksalmon' ))

    elif item.extra == 'torrents':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR blue]Torrents:[/I][/COLOR][/B]', thumbnail=config.get_thumb('booklet'), fanart=fanart, text_color='darksalmon' ))

    elif item.extra == 'doramas':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR firebrick]Episodios Doramas:[/I][/B][/COLOR]', thumbnail=config.get_thumb('computer'), fanart=fanart, text_color='darksalmon' ))

    elif item.extra == 'animes':
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR springgreen]Episodios Animes:[/I][/B][/COLOR]', thumbnail=config.get_thumb('tvshow'), fanart=fanart, text_color='darksalmon' ))

    else:
        itemlist.append(item.clone( action='', title='[B]- Recomendaciones [I][COLOR hotpink]Episodios Series:[/I][/B][/COLOR]', thumbnail=config.get_thumb('tvshow'), fanart=fanart, text_color='darksalmon' ))

    for ch in ch_list:
        if '+18' in ch['notes']: continue

        cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

        context = []

        if 'proxies' in ch['notes'].lower():
            if config.get_setting(cfg_proxies_channel, default=''):
                tit = '[COLOR %s]Quitar Proxies del Canal[/COLOR]' % color_list_proxies
                context.append({'title': tit, 'channel': item.channel, 'action': '_quitar_proxies'})

        if ch['status'] != 1:
            tit = '[COLOR %s][B]Marcar Canal como Preferido[/B][/COLOR]' % color_list_prefe
            context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 1})

        if ch['status'] != 0:
            if ch['status'] == 1:
                tit = '[COLOR %s][B]Des-Marcar Canal Preferido[/B][/COLOR]' % color_list_prefe
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})
            elif ch['status'] == -1:
                tit = '[COLOR %s][B]Re-Activar Canal Desactivado[/B][/COLOR]' % color_list_inactive
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})
            else:
                tit = '[COLOR white][B]Marcar Canal como Activo[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})

        if ch['status'] != -1:
            tit = '[COLOR %s][B]Marcar Canal como Desactivado[/B][/COLOR]' % color_list_inactive
            context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': -1})

        cfg_domains = False

        if 'current' in ch['clusters']:
            cfg_domains = True

            tit = '[COLOR bisque]Gestión Dominios[/COLOR]'
            context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_domains'})

        tit = '[COLOR %s][B]Últimos Cambios Dominios[/B][/COLOR]' % color_exec
        context.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

        if cfg_domains:
            tit = '[COLOR yellowgreen][B]Dominio Vigente[/B][/COLOR]'
            context.append({'title': tit, 'channel': item.channel, 'action': '_dominio_vigente'})

            if 'Dispone de varios posibles dominios' in ch['notes']:
                tit = '[COLOR powderblue][B]Configurar Dominio a usar[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_dominios'})

            tit = '[COLOR orange][B]Modificar Dominio Memorizado[/B][/COLOR]'
            context.append({'title': tit, 'channel': item.channel, 'action': '_dominio_memorizado'})

        if 'register' in ch['clusters']:
            cfg_user_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_username'
            cfg_pass_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_password'

            if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
                tit = '[COLOR green][B]Información Registrarse[/B][/COLOR]'
                context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_register'})

                tit = '[COLOR teal][B]Credenciales Cuenta[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_credenciales'})
            else:
                cfg_login_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_login'

                presentar = True
                if 'dominios' in ch['notes'].lower():
                    cfg_dominio_channel = 'channel_' + ch['id'] + '_dominio'
                    if not config.get_setting(cfg_dominio_channel, default=''): presentar = False

                if presentar:
                    if config.get_setting(cfg_login_channel, default=False):
                        tit = '[COLOR teal][B]Cerrar Sesión[/B][/COLOR]'
                        context.append({'title': tit, 'channel': item.channel, 'action': '_credenciales'})

        if 'proxies' in ch['notes'].lower():
            if not config.get_setting(cfg_proxies_channel, default=''):
                tit = '[COLOR %s][B]Información Proxies[/B][/COLOR]' % color_infor
                context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

            tit = '[COLOR %s][B]Configurar Proxies a usar[/B][/COLOR]' % color_list_proxies
            context.append({'title': tit, 'channel': item.channel, 'action': '_proxies'})

        if 'notice' in ch['clusters']:
            tit = '[COLOR tan][B]Aviso Canal[/B][/COLOR]'
            context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_' + ch['id']})

        if 'register' in ch['clusters']:
            cfg_user_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_username'
            cfg_pass_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_password'

            if config.get_setting(cfg_user_channel, default='') and config.get_setting(cfg_pass_channel, default=''):
               cfg_login_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_login'

               if config.get_setting(cfg_login_channel, default=False):
                   cfg_dominio_channel = 'channel_' + ch['id'] + '_dominio'
                   tit = '[COLOR springgreen][B]Test Login Cuenta[/B][/COLOR]'
                   context.append({'title': tit, 'channel': 'submnuctext', 'action': '_credenciales_' + ch['id']})

        if 'clons' in ch['clusters']:
            tit = '[COLOR turquoise][B]Clones[/B][/COLOR]'
            context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_prales'})

        if 'clone' in ch['clusters']:
            tit = '[COLOR paleturquoise][B]Principal[/B][/COLOR]'
            context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_principal'})

        tit = '[COLOR darkorange][B]Test Web Canal[/B][/COLOR]'
        context.append({'title': tit, 'channel': item.channel, 'action': '_tests'})

        if cfg_domains:
            tit = '[COLOR %s]Ajustes categoría Dominios[/COLOR]' % color_exec
            context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

        color = color_list_prefe if ch['status'] == 1 else 'white' if ch['status'] == 0 else color_list_inactive

        plot = ''
        plot += '[' + ', '.join([config.get_localized_category(ct) for ct in ch['categories']]) + '][CR]'
        plot += '[' + ', '.join([idioma_canal(lg) for lg in ch['language']]) + ']'
        if ch['notes'] != '': plot += '[CR][CR]' + ch['notes']

        titulo = ch['name']

        if ch['status'] == -1:
            titulo += '[I][B][COLOR %s] (desactivado)[/COLOR][/I][/B]' % color_list_inactive
            if config.get_setting(cfg_proxies_channel, default=''): titulo += '[I][B][COLOR %s] (proxies)[/COLOR][/I][/B]' % color_list_proxies
        else:
            if ch['status'] == 1:
               titulo += '[I][B][COLOR wheat] (preferido)[/COLOR][/I][/B]'

            if 'suggested' in ch['clusters']: titulo += '[I][B][COLOR olivedrab] (sugerido)[/COLOR][/I][/B]'

            if config.get_setting(cfg_proxies_channel, default=''):
                if ch['status'] == 1: titulo += '[I][B][COLOR %s] (proxies)[/COLOR][/I][/B]' % color_list_proxies
                else: color = color_list_proxies

        if 'register' in ch['clusters']:
            cfg_user_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_username'
            cfg_pass_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_password'

            if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
               titulo += '[I][B][COLOR teal] (cuenta)[/COLOR][/I][/B]'
            else:
               cfg_login_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_login'

               if config.get_setting(cfg_login_channel, default=False):
                   presentar = True
                   if 'dominios' in ch['notes'].lower():
                       cfg_dominio_channel = 'channel_' + ch['id'] + '_dominio'

                   if presentar: titulo += '[I][B][COLOR teal] (sesión)[/COLOR][/I][/B]'
               else: titulo += '[I][COLOR teal] (login)[/COLOR][/I]'

        if 'current' in ch['clusters']:
            cfg_current_channel = 'channel_' + ch['id'] + '_dominio'

            if config.get_setting(cfg_current_channel, default=False): titulo += '[I][B][COLOR green] (dominio)[/COLOR][/I][/B]'

        if not PY3:
            if 'mismatched' in ch['clusters']: continue

        if 'inestable' in ch['clusters']: continue

        elif 'problematic' in ch['clusters']: continue

        elif 'clone' in ch['clusters']:
            titulo += '[I][B][COLOR turquoise] (clon)[/COLOR][/I][/B]'

        elif 'clons' in ch['clusters']:
            titulo += '[I][B][COLOR paleturquoise] (pral)[/COLOR][/I][/B]'

        if config.get_setting('mnu_simple', default=False):
            if 'movie' in ch['categories']:
                if 'torrent' in ch['categories']:
                    if not 'Canal con enlaces Streaming y Torrent' in ch['notes']: titulo += '[B][I][COLOR blue] torrents[/COLOR][/I][/B]'

                    if 'movie' in ch['categories']: titulo += '[B][I][COLOR deepskyblue] películas[/COLOR][/I][/B]'
                    if 'tvshow' in ch['categories']: titulo += '[B][I][COLOR hotpink] series[/COLOR][/I][/B]'

                    if 'Canal con enlaces Streaming y Torrent' in ch['notes']: titulo += '[B][I][COLOR magenta] streaming/torrent[/COLOR][/I][/B]'

                elif 'tvshow' in ch['categories']:
                    titulo += '[B][I][COLOR deepskyblue] películas[/COLOR] [COLOR hotpink]series[/COLOR][/I][/B]'
                    if 'infantil' in ch['clusters']: titulo += '[B][I][COLOR lightyellow] infantiles[/COLOR][/I][/B]'
                    if 'tales' in ch['clusters']: titulo += '[B][I][COLOR limegreen] novelas[/COLOR][/I][/B]'
                    if 'dorama' in ch['clusters']: titulo += '[B][I][COLOR firebrick] doramas[/COLOR][/I][/B]'
                    if 'anime' in ch['clusters']: titulo += '[B][I][COLOR springgreen] animes[/COLOR][/I][/B]'

                else:
                    titulo += '[B][I][COLOR deepskyblue] películas[/COLOR][/I][/B]'
            else:
                if 'torrent' in ch['categories']:
                    if not 'Canal con enlaces Streaming y Torrent' in ch['notes']: titulo += '[B][I][COLOR blue] torrents[/COLOR][/I][/B]'

                    titulo += '[B][I][COLOR hotpink] series[/COLOR][/I][/B]'

                    if 'Canal con enlaces Streaming y Torrent' in ch['notes']: titulo += '[B][I][COLOR magenta] streaming/torrent[/COLOR][/I][/B]'

                elif 'tvshow' in ch['categories']:
                    titulo += '[B][I][COLOR hotpink] series[/COLOR][/I][/B]'
                    if 'infantil' in ch['clusters']: titulo += '[B][I][COLOR lightyellow] infantiles[/COLOR][/I][/B]'
                    if 'tales' in ch['clusters']: titulo += '[B][I][COLOR limegreen] novelas[/COLOR][/I][/B]'
                    if 'dorama' in ch['clusters']: titulo += '[B][I][COLOR firebrick] doramas[/COLOR][/I][/B]'
                    if 'anime' in ch['clusters']: titulo += '[B][I][COLOR springgreen] animes[/COLOR][/I][/B]'

                elif "documentary" in ch['categories']: titulo += '[B][I][COLOR cyan] documentales[/COLOR][/I][/B]'

        if con_incidencias:
            if ch['name'] in str(con_incidencias): titulo += '[I][B][COLOR tan] (incidencia)[/COLOR][/I][/B]'

        if no_accesibles:
            if ch['name'] in str(no_accesibles): titulo += '[I][B][COLOR indianred] (no accesible)[/COLOR][/I][/B]'

        if con_problemas:
            if ch['name'] in str(con_problemas):
                hay_problemas = str(con_problemas).replace('[B][COLOR moccasin]', 'CHANNEL').replace('[COLOR lime]', '/CHANNEL')
                channels_con_problemas = scrapertools.find_multiple_matches(hay_problemas, "CHANNEL(.*?)/CHANNEL")

                for channel_con_problema in channels_con_problemas:
                     channel_con_problema = channel_con_problema.strip()

                     if not channel_con_problema == ch['name']: continue

                     titulo += '[I][B][COLOR tomato] (con problema)[/COLOR][/I][/B]'
                     break

        if item.extra == 'movies':
            if not 'movie' in ch['categories']: continue

            elif ch['id'] == 'gnula24h': continue
            elif ch['id'] == 'seriesretro': continue
            elif ch['id'] == 'cuevana3pro': continue
            elif ch['id'] == 'cuevana3run': continue
            elif ch['id'] == 'onlinetv': continue
            elif ch['id'] == 'retrotv': continue
            elif ch['id'] == 'cinemundo': continue
            elif ch['id'] == 'cineplay': continue
            elif ch['id'] == 'cineteca': continue
            elif ch['id'] == 'creyente': continue
            elif ch['id'] == 'flizzmovies': continue
            elif ch['id'] == 'genteclic': continue
            elif ch['id'] == 'hdcinema': continue
            elif ch['id'] == 'legalmentegratis': continue
            elif ch['id'] == 'megaserie': continue
            elif ch['id'] == 'pelis182': continue
            elif ch['id'] == 'pelis28re': continue
            elif ch['id'] == 'pelisforte': continue
            elif ch['id'] == 'pelismart': continue
            elif ch['id'] == 'pelispediaws': continue
            elif ch['id'] == 'pelisplayhd': continue
            elif ch['id'] == 'seriespapayato': continue
            elif ch['id'] == 'streamgratis': continue
            elif ch['id'] == 'tubeonline': continue
            elif ch['id'] == 'verflix': continue
            elif ch['id'] == 'zonaleros': continue

        elif item.extra == 'tvshows':
            if not 'tvshow' in ch['categories']: continue

            elif ch['id'] == 'cinecalidad': continue
            elif ch['id'] == 'cuevana3pro': continue
            elif ch['id'] == 'cuevana3run': continue
            elif ch['id'] == 'gnula24': continue
            elif ch['id'] == 'gnula24h': continue
            elif ch['id'] == 'gnulacenter': continue

            elif ch['id'] == 'onlinetv': continue
            elif ch['id'] == 'retrotv': continue
            elif ch['id'] == 'series24': continue
            elif ch['id'] == 'seriesonline': continue
            elif ch['id'] == 'seriesplus': continue
            elif ch['id'] == 'star': continue
            elif ch['id'] == 'seriesretro': continue
            elif ch['id'] == 'sololatino': continue
            elif ch['id'] == 'verflix': continue
            elif ch['id'] == 'vernovelas': continue
            elif ch['id'] == 'veronline': continue
            elif ch['id'] == 'veronlinelatino': continue
            elif ch['id'] == 'verserieonline': continue

        elif item.extra == 'documentaries':
            if not 'documentary' in ch['categories']: continue

            if ch['id'] == 'verdocumentalesonline': pass
            else: continue

        elif item.extra == 'infantiles':
            if not 'kids' in ch['clusters']: continue

            if ch['id'] == 'osjonosu': pass
            else: continue

        elif item.extra == 'torrents':
            if not 'torrent' in ch['categories']: continue

            if ch['id'] == 'divxatope': pass
            elif ch['id'] == 'divxtotal': pass
            elif ch['id'] == 'dontorrents': pass
            elif ch['id'] == 'dontorrentsin': pass
            elif ch['id'] == 'elitedivx': pass
            elif ch['id'] == 'lilatorrent': pass
            elif ch['id'] == 'mejortorrentapp': pass
            elif ch['id'] == 'mejortorrentnz': pass
            elif ch['id'] == 'naranjatorrent': pass
            elif ch['id'] == 'reinventorrent': pass
            elif ch['id'] == 'rojotorrent': pass
            elif ch['id'] == 'subtorrents': pass
            elif ch['id'] == 'todotorrents': pass
            elif ch['id'] == 'tomadivx': pass
            elif ch['id'] == 'verdetorrent': pass
            elif ch['id'] == 'vivatorrents': pass

            else: continue

        elif item.extra == 'doramas':
            if not 'exclusivamente al dorama' in ch['notes'].lower(): continue

            if ch['id'] == 'doramaexpress': pass
            elif ch['id'] == 'doramasflix': pass
            elif ch['id'] == 'doramasflixin': pass
            elif ch['id'] == 'doramasflixio': pass
            elif ch['id'] == 'doramasorg': pass
            elif ch['id'] == 'doramasmp4dev': pass
            elif ch['id'] == 'doramasqueenin': pass
            elif ch['id'] == 'doramasyt': pass
            elif ch['id'] == 'pandramaio': pass
            elif ch['id'] == 'yandispoiler': pass

            else: continue

        elif item.extra == 'animes':
            if not 'exclusivamente al anime' in ch['notes'].lower(): continue

            if ch['id'] == 'animeclub': pass
            elif ch['id'] == 'animeflv': pass
            elif ch['id'] == 'animejl': pass
            elif ch['id'] == 'animeonline': pass
            elif ch['id'] == 'animeyt': pass
            elif ch['id'] == 'estrenosanime': pass
            elif ch['id'] == 'jkanime': pass
            elif ch['id'] == 'henaojara': pass
            elif ch['id'] == 'henaojaran': pass
            elif ch['id'] == 'latanime': pass
            elif ch['id'] == 'monoschinos': pass
            elif ch['id'] == 'mundodonghua': pass
            elif ch['id'] == 'mundodonghuaxyz': pass
            elif ch['id'] == 'tioanime': pass
            elif ch['id'] == 'tiodonghua': pass
            elif ch['id'] == 'veranime': pass
            elif ch['id'] == 'villaanimex': pass
            elif ch['id'] == 'zerowpanime': pass

            else: continue

        else:
            if not 'tvshow' in ch['categories']: continue

            elif ch['id'] == 'cinecalidad': continue
            elif ch['id'] == 'cineplay': continue
            elif ch['id'] == 'creyente': continue
            elif ch['id'] == 'gnula': continue
            elif ch['id'] == 'gnulacenter': continue
            elif ch['id'] == 'hdcinema': continue
            elif ch['id'] == 'osjonosu': continue
            elif ch['id'] == 'peliculaspro': continue
            elif ch['id'] == 'pelis28re': continue
            elif ch['id'] == 'pelisflix': continue
            elif ch['id'] == 'pelismart': continue
            elif ch['id'] == 'pelisplayhd': continue
            elif ch['id'] == 'pelisplushd': continue
            elif ch['id'] == 'pelisplushdlat': continue
            elif ch['id'] == 'zonaleros': continue

        if not 'suggested' in ch['clusters']:
            if 'torrent' in ch['categories']:
                if ch['id'] == 'zerowpanime': pass

                elif not item.extra == 'torrents': continue

            elif item.extra == 'movies':
                if ch['id'] == 'gnulatv': pass

            elif item.extra == 'episodes':
                if ch['id'] == 'veronlinelatino': pass

            elif item.extra == 'doramas': pass
            elif item.extra == 'animes': pass

            elif 'clons' in ch['clusters']: pass
            elif 'clone' in ch['clusters']: pass

            else: continue

        if ch['id'] == 'allpeliculasse': continue
        elif ch['id'] == 'areshd': continue
        elif ch['id'] == 'cine24h': continue
        elif ch['id'] == 'cinehdplus': continue
        elif ch['id'] == 'cinemitas': continue
        elif ch['id'] == 'cineplus': continue
        elif ch['id'] == 'cuevana3re': continue
        elif ch['id'] == 'estrenoscinesaa': continue
        elif ch['id'] == 'entrepeliculasyseries': continue
        elif ch['id'] == 'lacartoons': continue
        elif ch['id'] == 'lamovie': continue
        elif ch['id'] == 'megadedeoficial': continue
        elif ch['id'] == 'peliculasflix': continue
        elif ch['id'] == 'pelisgratishd': continue
        elif ch['id'] == 'pelispediais': continue
        elif ch['id'] == 'pelisplushdnz': continue
        elif ch['id'] == 'plushd': continue
        elif ch['id'] == 'repelishd': continue
        elif ch['id'] == 'serieskao': continue
        elif ch['id'] == 'tucineclasico': continue
        elif ch['id'] == 'ultrapelis': continue
        elif ch['id'] == 'verpelis': continue
        elif ch['id'] == 'zoowomaniacos': continue

        accion = '_' + item.news

        itemlist.append(Item( channel=ch['id'], action=accion, title=titulo, context=context,
                              search_type=item.search_type, text_color=color, thumbnail=ch['thumbnail'], fanart=fanart ))

    return itemlist


def idioma_canal(lang):
    idiomas = { 'cast': 'Castellano', 'lat': 'Latino', 'eng': 'Inglés', 'pt': 'Portugués', 'vo': 'VO', 'vose': 'Vose', 'vos': 'Vos', 'cat': 'Català' }
    return idiomas[lang] if lang in idiomas else lang


def _marcar_canal(item):
    from modules import submnuctext
    submnuctext._marcar_canal(item)


def _quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)


def _dominio_vigente(item):
    from modules import submnuctext
    submnuctext._dominio_vigente(item)


def _dominio_memorizado(item):
    from modules import submnuctext
    submnuctext._dominio_memorizado(item)


def _dominios(item):
    from modules import submnuctext
    submnuctext._dominios(item)


def _credenciales(item):
    from modules import submnuctext
    submnuctext._credenciales(item)


def _proxies(item):
    from modules import submnuctext
    submnuctext._proxies(item)


def _tests(item):
    from modules import submnuctext
    submnuctext._test_webs(item)
