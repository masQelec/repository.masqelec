# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    PY3 = False
    import urllib2
else:
    PY3 = True
    import urllib.error as urllib2


import os

import traceback

from platformcode import config

if config.get_setting('PY3') == '': config.set_setting('PY3', PY3)


from platformcode import logger, platformtools, updater
from core.item import Item
from core import servertools

from platformcode.config import WebErrorException


txt_pys = '[COLOR yellow]Película y/ó Serie[/COLOR] texto a buscar ...'
txt_pel = '[COLOR deepskyblue]Película[/COLOR] texto a buscar ...'
txt_ser = '[COLOR hotpink]Serie[/COLOR] texto a buscar ...'
txt_doc = '[COLOR cyan]Documental[/COLOR] texto a buscar ...'
txt_tor = '[COLOR blue]Torrent[/COLOR] [COLOR yellow]Película y/ó Serie[/COLOR] texto a buscar ...'
txt_dor = '[COLOR firebrick]Dorama[/COLOR] texto a buscar ...'
txt_ani = '[COLOR springgreen]Anime[/COLOR] texto a buscar ...'
txt_lis = '[COLOR greenyellow]Lista[/COLOR] texto a buscar ...'
txt_per = '[COLOR tan]Persona[/COLOR] texto a buscar ...'
txt_vid = '[COLOR darkorange]+18 Vídeo[/COLOR] texto a buscar ...'
txt_yt  = '[COLOR darksalmon]Youtube[/COLOR] texto a buscar ...'


# ~ Obtener parámetros ejecución
logger.info('[COLOR blue]Starting with %s[/COLOR]' % sys.argv[1])

if sys.argv[2]: item = Item().fromurl(sys.argv[2])
else: item = Item(channel='mainmenu', action='mainlist')


sys.path.append(os.path.join(config.get_runtime_path(), 'lib'))


# ~ Establecer si channel es un canal ó un módulo
tipo_channel = ''

if item.channel == '' or item.action == '': logger.info('Empty channel/action, Nothing to do')
else:
    # ~ channel puede ser un canal ó un módulo
    path = os.path.join(config.get_runtime_path(), 'channels', item.channel + ".py")
    if os.path.exists(path): tipo_channel = 'channels.'
    else:
        path = os.path.join(config.get_runtime_path(), 'modules', item.channel + ".py")
        if os.path.exists(path): tipo_channel = 'modules.'
        else: tipo_channel = 'modules.'


# ~ Ejecutar según parámetros
if tipo_channel != '':
    try:
        canal = __import__(tipo_channel + item.channel, fromlist=[''])

        # ~ findvideos se considera reproducible y debe acabar haciendo play (ó play_fake en su defecto)
        if item.action == 'findvideos':
            if hasattr(canal, item.action): itemlist = canal.findvideos(item)
            else: itemlist = servertools.find_video_items(item)

            platformtools.play_from_itemlist(itemlist, item)
        else:
            # ~ search pide el texto a buscar antes de llamar a la rutina del canal (pasar item.buscando para no mostrar diálogo)
            if item.action == 'search':
                if item.buscando != '': tecleado = item.buscando
                else:
                    last_search = config.get_last_search(item.search_type)

                    txt_search = txt_pys

                    if item.search_type == 'all':
                        if item.search_pop:
                            last_search = config.get_last_search('list')
                            txt_search = txt_lis
                        elif item.search_video:
                            last_search = config.get_last_search('video')
                            txt_search = txt_vid
                        elif item.search_special == 'torrent':
                            last_search = config.get_last_search('torrent')
                            txt_search = txt_tor
                        elif item.search_special == 'dorama':
                            last_search = config.get_last_search('dorama')
                            txt_search = txt_dor
                        elif item.search_special == 'anime':
                            last_search = config.get_last_search('anime')
                            txt_search = txt_ani
                        elif item.search_special == 'youtube':
                            last_search = config.get_last_search('youtube')
                            txt_search = txt_yt
                        else: last_search = config.get_last_search('all')

                    elif item.search_type == 'movie':
                        if item.search_video:
                            last_search = config.get_last_search('video')
                            txt_search = txt_vid
                        else: txt_search = txt_pel

                    elif item.search_type == 'tvshow': txt_search = txt_ser
                    elif item.search_type == 'documentary': txt_search = txt_doc
                    elif item.search_type == 'person': txt_search = txt_per

                    elif item.search_special == 'torrent': txt_search = txt_tor
                    elif item.search_special == 'dorama': txt_search = txt_dor
                    elif item.search_special == 'anime': txt_search = txt_ani
                    elif item.search_special == 'youtube': txt_search = txt_yt

                    else:
                        if item.search_video:
                            last_search = config.get_last_search('video')
                            txt_search = txt_vid

                    tecleado = platformtools.dialog_input(last_search, txt_search)

                if tecleado is not None and tecleado != '':
                    itemlist = canal.search(item, tecleado)

                    if item.buscando == '':
                        last_bus = item.search_type

                        if item.search_type == 'all':
                            if item.search_pop: last_bus = 'list'
                            elif item.search_video: last_bus = 'video'
                            elif item.search_special == 'torrent': last_bus = 'torrent'
                            elif item.search_special == 'dorama': last_bus = 'dorama'
                            elif item.search_special == 'anime': last_bus = 'anime'
                            elif item.search_special == 'youtube': last_bus = 'youtube'
                            else: last_bus = 'all'

                        elif item.search_type == 'movie':
                            if item.search_video: last_bus = 'video'
                            else: last_bus = 'movie'

                        elif item.search_pop: last_bus = 'list'

                        elif item.search_video: last_bus = 'video'

                        elif item.search_type == 'person': last_bus = 'person'

                        elif item.search_special == 'torrent': last_bus = 'torrent'
                        elif item.search_special == 'dorama': last_bus = 'dorama'
                        elif item.search_special == 'anime': last_bus = 'anime'
                        elif item.search_special == 'youtube': last_bus = 'youtube'

                        if last_bus: config.set_last_search(last_bus, tecleado)
                else:
                    itemlist = []
                    # ~ Desactivar si provoca ERROR: GetDirectory en el Log
                    item.folder = False
                    itemlist = False

            # ~ Cualquier otra acción se ejecuta en el canal, y se renderiza si devuelve una lista de items
            else:
                if hasattr(canal, item.action):
                    func = getattr(canal, item.action)
                    itemlist = func(item)
                else:
                    # ~ Si item.folder kodi espera un listado
                    logger.info('Action Not Found in channel')
                    itemlist = [] if item.folder else False

            if type(itemlist) == list:
                logger.info('Renderizar itemlist')
                platformtools.render_items(itemlist, item)

            elif itemlist == None:
                # ~ Si kodi espera un listado (Desactivar si provoca ERROR: GetDirectory en el Log)
                logger.info('Sin renderizar')
                platformtools.render_no_items()

            elif itemlist == True: logger.info('El canal ha ejecutado Correctamente una acción que no devuelve ningún listado.')

            elif itemlist == False:logger.info('El canal ha ejecutado una acción que no devuelve ningún listado.') 

    except urllib2.URLError as e:
        logger.error(traceback.format_exc())

        # ~ Grab inner and third party errors
        if hasattr(e, 'reason'):
            logger.error("Razon del error, codigo: %s | Razon: %s" % (str(e.reason[0]), str(e.reason[1])))
            texto = "No se puede Conectar con el Servidor ó con el sitio Web"
            platformtools.dialog_ok(config.__addon_name, texto)

        # ~ Grab server response errors
        elif hasattr(e, 'code'):
            logger.error("Codigo de error HTTP: %d" % e.code)
            platformtools.dialog_ok(config.__addon_name, "El sitio Web no funciona Correctamente (error http %d)" % e.code)

    except WebErrorException as e:
        logger.error(traceback.format_exc())

        # ~ Ofrecer buscar en otros canales ó en el mismo canal
        if item.contentType in ['movie', 'tvshow', 'season', 'episode'] and config.get_setting('tracking_weberror_dialog', default=True):
            if item.action == 'findvideos': platformtools.play_fake()

            item_search = platformtools.dialogo_busquedas_por_fallo_web(item)
            if item_search is not None: platformtools.itemlist_update(item_search)

        else:
            try: last_ver = updater.check_addon_version()
            except: last_ver = True

            if not last_ver: last_ver = '[I](desfasada)[/I]'
            else: last_ver = ''

            release = '[COLOR goldenrod][B]' + config.get_addon_version().replace('.fix', '-Fix') + str(last_ver) + ' '

            platformtools.dialog_ok(release + '[COLOR red][B]Error en el canal [COLOR yellow]' + item.channel.capitalize() + '[/B][/COLOR]', 
                                    '[COLOR yellowgreen][B]La Web asociada al Canal, parece no estar Disponible[/B][/COLOR], Intentélo de nuevo pasados unos minutos, y si el problema persiste compruebe mediante un Navegador de Internet la Web: [COLOR cyan][B]%s[/B][/COLOR]' % (e) )

    except:
        logger.error(traceback.format_exc())

        try: last_ver = updater.check_addon_version()
        except: last_ver = True

        if not last_ver: last_ver = '[I](desfasada)[/I]'
        else: last_ver = ''

        release = '[COLOR goldenrod][B]' + config.get_addon_version().replace('.fix', '-Fix') + str(last_ver) + ' '

        if item.channel in ['mainmenu', 'actions', 'domains', 'downloads', 'favoritos', 'filmaffinitylists', 'filters', 'generos', 'groups', 'helper', 'proxysearch', 'search', 'submnuctext', 'submnuteam', 'tester', 'tmdblists', 'tracking']:
            platformtools.dialog_ok(release + '[COLOR red][B]Error Inesperado en [COLOR gold]' + item.channel.capitalize() + '[/B][/COLOR]',
                                    '[COLOR moccasin][B]Puede estar Corrupto su Fichero de [COLOR chocolate][B]Ajustes[/COLOR][COLOR goldenrod][B] de [/B][/COLOR][COLOR yellow][B]Balandro[/B][/COLOR], Pruebe a [COLOR cyan][B]Re-Instalar el Add-On[/B][/COLOR][COLOR goldenrod][B] (consulte nuestro Telegram ó Foro)[/B][/COLOR][COLOR moccasin][B], ó [/COLOR][COLOR darkcyan][B]bien hay un Error en el Add-On/Modulo.[/B][/COLOR] [COLOR chartreuse][B]Para más detalles, vea el Fichero Log de su Media Center en la Ayuda.[/B][/COLOR]')
        else:
            platformtools.dialog_ok(release + ' [COLOR red]Error Inesperado en [COLOR yellow]' + item.channel.capitalize() + '[/B][/COLOR]',
                                    '[COLOR moccasin][B]Puede ser a un fallo de Conexión[/B][/COLOR], ó [COLOR cyan][B]la Web asociada al Canal varió su estructura[/B][/COLOR], ó [COLOR goldenrod][B]estar Corrupto su Fichero de [COLOR chocolate][B]Ajustes[/COLOR][COLOR goldenrod][B] de [/B][/COLOR][COLOR yellow][B]Balandro[/B][/COLOR][COLOR moccasin], ó [/COLOR][COLOR darkcyan][B]Hay un Error en el Add-On.[/B][/COLOR] [COLOR chartreuse][B]Para más detalles, vea el Fichero Log de su Media Center en la Ayuda.[/B][/COLOR]')

logger.info('[COLOR blue]Ending with %s[/COLOR]' % sys.argv[1])
