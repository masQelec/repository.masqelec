# -*- coding: utf-8 -*-

# Módulo interno para testear canales y servidores.
# Atención si se hacen cambios, si no se limitan los enlaces a rastrear puede hacerse muy largo y pesado.

# Este módulo permite la ejecución de tests para comprobar el funcionamiento de canales y servidores.
# Los resultados de los tests se pueden enviar a una web propia para consultarlos más cómodamente.

# Test del funcionamiento de un canal:
# - Desde el mainlist() del canal, recorre recursivamente todos los enlaces
# - Para cada enlace se apunta en un log lo que devuelve
# - Si se encuentran enlaces parecidos solo se analiza el primero de ellos
#   (Por ejemplo, enlaces a cada género, a cada letra del abecedario)
#   (Parecido equivale a que llama al mismo action pasándole una url diferente)
#   (Los parecidos se descartan en cualquier submenú pero no en el menú principal)
# - La información del test se graba en un fichero de log en .kodi/userdata/addon_data/plugin.video.../test_logs/channels/
# - El proceso para algunos canales con muchos enlaces puede tardar un rato.

# Test del funcionamiento de un servidor:
# - Se buscan enlaces al servidor entre todos los logs de los canales
# - Si se encuentran demasiados (parámetro configurable) se hace un muestreo aleatorio
# - Para cada uno de ellos se intenta resolver con el play del canal o llamando a servertools si no hay play
# - La información del test se graba en un fichero de log en .kodi/userdata/addon_data/plugin.video.../test_logs/servers/


import os, time, random

from core.item import Item
from core import httptools, scrapertools, servertools,  channeltools

from platformcode import config, logger, platformtools


# AJUSTES PARA TODO EL PROCESO

# Desactivar las llamadas a tmdb ya que no son necesarias para los tests
from core import tmdb

def disabled_set_infoLabels(source, seekTmdb=True, idioma_busqueda='es'):
    return 0
def disabled_set_infoLabels_itemlist(item_list, seekTmdb=False, idioma_busqueda='es'):
    return 0
def disabled_set_infoLabels_item(item, seekTmdb=True, idioma_busqueda='es', lock=None):
    return 0

tmdb.set_infoLabels = disabled_set_infoLabels
tmdb.set_infoLabels_itemlist = disabled_set_infoLabels_itemlist
tmdb.set_infoLabels_item = disabled_set_infoLabels_item
tmdb.TEST_IN_PROGRESS = True # Definir variable por si en algún sitio se quiere actuar diferente si se está pasando el test

# Limitar tiempo de descarga y desactivar debug

httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = 10
# ~ logger.log_enable(False)

config.set_setting('autoplay', False) # desactivar autoplay
config.set_setting('autoplay_one_link', False) # desactivar autoplay cuando 1 solo enlace
# ~ config.set_setting('developer_mode', False) # opcionalmente desactivar si no se quieren generar servers_todo.log, qualities_todo.log y developer.sqlite 


# PARÁMETROS GENERALES

# Para descartar algunos action que no hay que analizar en los tests de canales
# (por ejemplo, menús que piden interacción del usuario como las búsquedas, o acciones como añadir a videoteca, abrir la configuración, ...)

ACTION_DISCARD = ['', 'search', 'filtrado', 'modificar_filtro', 'configurar_proxies', 'configurar_dominio']

# Para descartar algunos canales que no hay que analizar en los tests de canales
CHANNEL_DISCARD = [ 'tvvip', 'pelisipad', 'proves' ]

# Para descartar algunos servidores que no hay que analizar en los tests de servidores
SERVER_DISCARD = [
    #'cloudy', 'gvideo', 'userscloud' # pq tardan demasiado en responder o no lo hacen!
]

# Número máximo de enlaces findvideos a comprobar para cada canal en los tests de canales
MAX_MUESTRAS_FINDVIDEOS = 10

# Número máximo de enlaces a comprobar para cada servidor en los tests de servidores
MAX_LINKS_PLAY = 5
MAX_LINKS_PLAY_DIRECTO = 25 # ampliado con server=directo para detectar nuevos servidores a implementar


# Carpetas dónde se guardan los logs

RUTA_TEST_LOGS = os.path.join(config.get_data_path(), 'test_logs')
if not os.path.exists(RUTA_TEST_LOGS): os.mkdir(RUTA_TEST_LOGS)

RUTA_CHANNEL_LOGS = os.path.join(RUTA_TEST_LOGS, 'channels')
if not os.path.exists(RUTA_CHANNEL_LOGS): os.mkdir(RUTA_CHANNEL_LOGS)

RUTA_SERVER_LOGS = os.path.join(RUTA_TEST_LOGS, 'servers')
if not os.path.exists(RUTA_SERVER_LOGS): os.mkdir(RUTA_SERVER_LOGS)


def mainlist(item):
    logger.info()
    itemlist = []

    if config.get_setting('developer_mode', default=False):
        itemlist.append(item.clone(action='show_help_tests', title="Información Test canales y servidores", folder=False, thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone(action='', title="[COLOR moccasin]- Logs de tests en local:[/COLOR]" )) 
        itemlist.append(Item(channel=item.channel, action="clean_local_logs_all", title="1   - Eliminar todos los logs locales", thumbnail=config.get_thumb('keyboard'), text_color='red' ))
        itemlist.append(Item(channel=item.channel, action="clean_local_logs_channels", title="1a - Eliminar logs de canales locales", thumbnail=config.get_thumb('keyboard'), text_color='red' ))
        itemlist.append(Item(channel=item.channel, action="clean_local_logs_servers", title="1b - Eliminar logs de servidores locales", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

        itemlist.append(item.clone(action='', title="[COLOR moccasin]- Ejecución de tests:[/COLOR]" )) 
        itemlist.append(Item(channel=item.channel, action="channel_test_selected", title="2 - Testear canales", thumbnail=config.get_thumb('stack') ))
        itemlist.append(Item(channel=item.channel, action="server_test_selected", title="3 - Testear servidores", thumbnail=config.get_thumb('flame') ))

        itemlist.append(item.clone(action='', title="[COLOR moccasin]- Subir tests a la web:[/COLOR]" )) 
        itemlist.append(Item(channel=item.channel, action="upload_web_tests_all", title="4   - Upload all tests to web", thumbnail=config.get_thumb('cloud') ))
        itemlist.append(Item(channel=item.channel, action="upload_web_tests_channels", title="4a - Upload channel tests to web", thumbnail=config.get_thumb('cloud') ))
        itemlist.append(Item(channel=item.channel, action="upload_web_tests_servers", title="4b - Upload server tests to web", thumbnail=config.get_thumb('cloud') ))

    return itemlist


# Eliminar logs anteriores
def clean_local_logs_all(item):
    logger.info()

    clean_local_logs_channels(item)
    clean_local_logs_servers(item)
    return False

def clean_local_logs_channels(item):
    logger.info()

    map( os.unlink, (os.path.join(RUTA_CHANNEL_LOGS,f) for f in os.listdir(RUTA_CHANNEL_LOGS)) )
    platformtools.dialog_notification('Eliminar tests locales', 'Channel tests deleted')
    return False

def clean_local_logs_servers(item):
    logger.info()

    map( os.unlink, (os.path.join(RUTA_SERVER_LOGS,f) for f in os.listdir(RUTA_SERVER_LOGS)) )
    platformtools.dialog_notification('Eliminar tests locales', 'Server tests deleted')
    return False


# Subir los tests a la web
def upload_web_tests_all(item):
    logger.info()

    upload_web_tests_channels(item)
    upload_web_tests_servers(item)
    return False

def upload_web_tests_channels(item):
    logger.info()

    upload_web_tests(RUTA_CHANNEL_LOGS, 'channels')
    return False

def upload_web_tests_servers(item):
    logger.info()

    upload_web_tests(RUTA_SERVER_LOGS, 'servers')
    return False


# Seleccionar y testear canales/servidores
def channel_test_selected(item):
    logger.info()

    selected = select_items('canales')
    if len(selected) > 0:
        test_selected_channels(selected)
    return False

def server_test_selected(item):
    logger.info()

    selected = select_items('servidores')
    if len(selected) > 0:
        test_selected_servers(selected)
    return False


# Seleccionar los canales/servidores a testear
def select_items(item_type):
    logger.info()

    # Cargar lista de opciones
    lista = []
    if item_type == 'canales':
        ch_list = channeltools.get_channels_list()
        for ch in ch_list:
            lbl = '[B]'+ch['name']+'[/B]'
            lbl += ' [%s]' % ', '.join(ch['language'])
            lbl += ' [%s]' % ', '.join(ch['categories'])
            lista.append({'id': ch['id'], 'label': lbl})

    else:
        sv_list = servertools.get_servers_list()
        sv_list = sorted(sv_list.values(), key=lambda x: x['id'])
        for sv in sv_list:
            # ~ if sv['active']:
            lista.append({'id': sv['id'], 'label': sv['name']})

    # Diálogo para pre-seleccionar (todos, ninguno, cast, lat, categorías, ...)
    preselecciones = ['Ninguno', 'Todos']
    ret = platformtools.dialog_select("Pre-selección de %s" % item_type, preselecciones)
    if ret == -1: return []

    preselect = []
    if preselecciones[ret] == 'Ninguno': preselect = []
    elif preselecciones[ret] == 'Todos': preselect = range(len(lista))

    # Diálogo para seleccionar
    ret = platformtools.dialog_multiselect("Escoger %s a testear:" % item_type, [c['label'] for c in lista], preselect=preselect)
    seleccionados = [] if ret == None else [lista[i]['id'] for i in ret]

    return seleccionados


# Testeos masivos en bucle canales
def test_selected_channels(channels_list):
    logger.info()

    total_time = 0
    for ind, channel in enumerate(channels_list):
        total_time += test_channel(channel, ind+1, len(channels_list))

    platformtools.dialog_ok(config.__addon_name, 'Tests finalizados en %d canales' % len(channels_list), 'Duración : %d segundos' % total_time)


# Test de un canal
def test_channel(channel, ind=1, total=1):
    logger.info()

    global test_filelog, test_canal, muestras_findvideos

    logfilename = os.path.join(RUTA_CHANNEL_LOGS, '%s.txt' % channel)
    test_filelog = open(logfilename, 'w')

    t_ini = time.time()
    acumula_log_text('INICIO TEST %s versión %s' % (time.strftime("%Y-%m-%d"), config.__settings__.getAddonInfo('version')))

    progreso = platformtools.dialog_progress('Testeando %s - [%s/%s] ' % (channel, ind, total), 'Iniciando tests')

    if channel in CHANNEL_DISCARD:
        acumula_log_text('\nEste canal se ha descartado para testear')
    else:
        try:
            muestras_findvideos = [] # para guardar algunos ejemplos de llamadas a findvideos y comprobar si resuelven

            test_canal = __import__('channels.' + channel, fromlist=[''])
            itemlist = test_canal.mainlist(Item(channel=channel, title=channel))

            acumula_log_text('\nSeguimiento desde mainlist:')
            n = len(itemlist)
            for cnt, it in enumerate(itemlist):
                progreso.update(((cnt + 1) * 100) / n, 'Seguimiento desde mainlist...')

                if it.channel == channel and it.action not in ACTION_DISCARD:
                    analyze_item(it, level=0)
                else:
                    acumula_log_item('\n*', '(not analyzed)', it)

            acumula_log_text('\nComprobación de findvideos:')
            n = len(muestras_findvideos)
            done = []
            for cnt, it in enumerate(muestras_findvideos):
                progreso.update(((cnt + 1) * 100) / n, 'Comprobando findvideos...')

                if it.url not in done and len(done) < MAX_MUESTRAS_FINDVIDEOS: # máximo de 10 y sin repetir
                    done.append(it.url)
                    analyze_findvideos(it)

        except:
            acumula_log_text('\nError en el test')

    t_fin = time.time()
    elapsed = (t_fin - t_ini)
    acumula_log_text('\nFINAL TEST duración: %f segundos.' % elapsed)

    test_filelog.close()

    platformtools.dialog_notification('Log generado', '%s.txt' % channel)

    return elapsed


# Seguimiento recursivo de enlaces
def analyze_item(item, level=0):
    logger.info()

    global muestras_findvideos

    hay_findvideos = 0
    actions_done = []
    salto = '\n' if level == 0 else ''

    try:
        func = getattr(test_canal, item.action)
        itemlist = func(item.clone())
        acumula_log_item(salto+'*' * (level + 1), '(%d enlaces)' % len(itemlist), item)
    except:
        itemlist = []
        acumula_log_item(salto+'*' * (level + 1), '(ERROR!)', item)

    descartar_similar = True
    if item.channel == 'newpct1' and item.action in ['mainlist_pelis', 'mainlist_series', 'mainlist_pelis_clon', 'mainlist_series_clon']: 
        descartar_similar = False

    for it in itemlist:
        if it.action == 'findvideos' or it.action == 'play':
            acumula_log_item_ampliado('*' * (level + 2), '', it)
            if hay_findvideos < 2: muestras_findvideos.append(it.clone()) # apuntar los dos primeros para comprobar después
            hay_findvideos += 1

        # hay_findvideos == 0: Si ya hay un findvideos en la lista, no entrar a analizar siguientes items (paginaciones, etc)
        # it.channel == item.channel : solo analizar llamadas al propio canal
        # it.action != item.action : para descartar posibles paginaciones si no se han encontrado findvideos
        elif hay_findvideos == 0 and it.channel == item.channel and it.action not in ACTION_DISCARD and it.action != item.action:
            if descartar_similar and it.action in actions_done: # no repetir mismas actions (ej: por cada letra, por cada género)
                acumula_log_item('*' * (level + 2), '(not analyzed, similar)', it)
            else:
                if level < 10:
                    analyze_item(it, level + 1)
                else:
                    acumula_log_item('*' * (level + 2), '(not analyzed, too far)', it)
                actions_done.append(it.action)

        else:
            acumula_log_item('*' * (level + 2), '(not analyzed)', it)


# Comprobación de muestras findvideos
def analyze_findvideos(item):
    logger.info()

    try:
        itemlist = test_canal.findvideos(item)
    except:
        itemlist = servertools.find_video_items(item)

    acumula_log_item_ampliado('\n*', '(%d enlaces)' % len(itemlist), item)

    for it in itemlist:
        acumula_log_findvideos('**', it)

    platformtools.developer_mode_check_findvideos(itemlist, item)


# Testeos masivos en bucle servidores
def test_selected_servers(servers_list):
    logger.info()

    total_time = 0
    for ind, server in enumerate(servers_list):
        total_time += test_server(server, ind+1, len(servers_list))

    platformtools.dialog_ok (config.__addon_name, 'Tests finalizados en %d servidores' % len(servers_list), 'Duración %d segundos' % total_time)


# Test de un servidor
def test_server(server, ind=1, total=1):
    logger.info()

    global test_filelog

    logfilename = os.path.join(RUTA_SERVER_LOGS, '%s.txt' % server)
    test_filelog = open(logfilename, 'w')

    t_ini = time.time()
    acumula_log_text('INICIO TEST %s versión %s' % (time.strftime("%Y-%m-%d"), config.__settings__.getAddonInfo('version')))

    if server in SERVER_DISCARD:
        acumula_log_text('\nEste servidor se ha descartado para testear')
    else:
        do_test_server(server, ind, total)

    t_fin = time.time()
    elapsed= (t_fin - t_ini)
    acumula_log_text('\nFINAL TEST duración: %f segundos.' % elapsed)

    test_filelog.close()

    platformtools.dialog_notification('Log generado', '%s.txt' % server)

    return elapsed


# Realiza el test del servidor
def do_test_server(server, ind, total):
    logger.info()

    n_ok = 0; n_ko = 0

    itemlist = obtener_plays_a_testear(server)

    progreso = platformtools.dialog_progress('Testeando %s - [%s/%s] ' % (server, ind, total), 'Iniciando tests')
    cnt = 0
    n = len(itemlist)

    for enlace, canal in itemlist:
        cnt += 1
        progreso.update((cnt * 100) / n, 'Comprobando enlaces...')

        acumula_log_text('\nPlay en el canal %s con url %s' % (canal, enlace))
        try:
            test_canal = __import__('channels.' + canal, fromlist=[''])
            itemlist = test_canal.play(Item(channel=canal, server=server, url=enlace, title='Test'))

            # Play should return a list of playable URLS
            if len(itemlist) > 0 and isinstance(itemlist[0], Item):
                vitem = itemlist[0]
            # Permitir varias calidades desde play en el canal
            elif len(itemlist) > 0 and isinstance(itemlist[0], list):
                vitem = Item(channel=canal, server=server, url=enlace, title='Test')
                vitem.video_urls = itemlist
            # If not, shows user an error message
            else:
                vitem = None
        except:
            vitem = Item(channel=canal, server=server, url=enlace, title='Test')

        if vitem == None:
            acumula_log_text('* No hay enlaces a videos!')
            n_ko += 1

        elif vitem.video_urls:
            acumula_log_text('* %d enlaces encontrados:' % len(vitem.video_urls))
            acumula_log_video_urls(vitem.video_urls)
            n_ok += 1

        else:
            video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(vitem.server, vitem.url)
            if puedes:
                acumula_log_text('* %d enlaces resueltos:' % len(video_urls))
                acumula_log_video_urls(video_urls)
                n_ok += 1
            else:
                acumula_log_text('* No se puede, motivo : %s' % limpiar_campo(motivo))
                n_ko += 1

    acumula_log_text('\nTotal de enlaces verificados: %d  OK: %d  FAIL: %d' % (n_ok+n_ko, n_ok, n_ko))


# Busca enlaces a un servidor en los logs de canales
def obtener_plays_a_testear(server):
    logger.info()

    itemlist = []
    canales = []

    cerca = ' ~ play ~ %s ~ (.*?) ~ (.*?) ~ ' % server
    files = [f for f in os.listdir(RUTA_CHANNEL_LOGS) if os.path.isfile(os.path.join(RUTA_CHANNEL_LOGS, f))]
    for f in files:
        with open(os.path.join(RUTA_CHANNEL_LOGS, f), 'r') as fit: data=fit.read(); fit.close()
        canal = f.replace('.txt','')

        matches = scrapertools.find_multiple_matches(data, cerca)
        if len(matches) > 0:
            canales.append(canal)
            for titulo, enlace in matches:
                if '(... continua' in enlace: continue # descartar url no completas
                if enlace not in [it[0] for it in itemlist]:
                    itemlist.append([enlace, canal])
            

    acumula_log_text('\nHay %d canales con enlaces a %s : %s' % (len(canales), server, sorted(canales)))

    max_enlaces = MAX_LINKS_PLAY if server != 'directo' else MAX_LINKS_PLAY_DIRECTO
    if len(itemlist) > max_enlaces: # reducir el número de enlaces aleatoriamente
        acumula_log_text('\nObtenidos %d enlaces a %s. Muestreo de %d aleatorios:' % (len(itemlist), server, max_enlaces))
        random.shuffle(itemlist)
        return itemlist[:max_enlaces]
    else:
        acumula_log_text('\nObtenidos %d enlaces a %s. Muestreo de todos ellos:' % (len(itemlist), server))
        return itemlist


# FUNCIONES AUXILIARES
# Para ir grabando en el fichero de log en curso


# Genérico para canales y servidores
def acumula_log_text(txt):
    logger.info()

    test_filelog.write(txt+'\n')

# Para canales
def acumula_log_item(nivel, notas, it):
    logger.info()

    infos = [nivel, notas, it.channel, it.action, limpiar_campo(it.title), limpiar_campo(it.url)]
    test_filelog.write(' ~ '.join(infos)+'\n')

def acumula_log_item_ampliado(nivel, notas, it):
    logger.info()

    infos = [nivel, notas, it.channel, it.action, limpiar_campo(it.title), limpiar_campo(it.url), limpiar_campo(it.languages), limpiar_campo(it.qualities)]
    test_filelog.write(' ~ '.join(infos)+'\n')

def acumula_log_findvideos(nivel, it):
    logger.info()

    infos = [nivel, it.channel, it.action, it.server, limpiar_campo(it.title), limpiar_campo(it.url), limpiar_campo(it.language), limpiar_campo(it.quality)]
    test_filelog.write(' ~ '.join(infos)+'\n')

# Para servidores
def acumula_log_video_urls(video_urls):
    logger.info()

    ret = ''
    for v in video_urls:
        ret += ' ~ '.join(limpiar_campo(x) for x in v) + '\n'
    test_filelog.write(ret)


# Para corregir titles demasiado largos y urls mal resueltas con html
def limpiar_campo(txt):
    logger.info()

    txt = str(txt).replace('\n', ' ')
    txt = txt.replace(' ~ ', ' - ') # por si el texto contiene el separador de campos usado
    tam = len(txt)
    if tam > 300: txt = txt[:300] + ' (... continua %d caracteres más)' % (tam - 300)
    return txt


# FUNCIONES COMPLEMENTARIAS

# Subir los logs al ftp de la web y procesarlos
def upload_web_tests(ruta, destino):
    logger.info()

    import ftplib

    platformtools.dialog_notification('Web Upload', 'FTP disabled')
    return False

    # Parámetros ftp y update web
    ftp_host = '...'
    ftp_user = '...'
    ftp_pass = '...'
    ftp_folder = '...'

    url_update  = '...'
    url_headers = '...'
    url_post = '...'

    # Subir ficheros por ftp
    session = ftplib.FTP(ftp_host, ftp_user, ftp_pass)

    files = [f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))]
    for f in files:
        fit = open(os.path.join(ruta, f),'rb')
        session.storbinary('STOR '+ftp_folder+f, fit)
        fit.close()

    session.quit()
    
    # Provocar update en la web para procesar los tests
    data = httptools.downloadpage(url_update, headers=url_headers, post=url_post, cookies=False).data


    platformtools.dialog_notification('Web Upload', '%s tests updated' % destino)


def show_help_tests(item):
    logger.info()

    txt = '*) Proceso habitual para un testeo completo'

    txt += '[CR][CR]'
    txt += '*) Procedimientos: [CR]'
    txt += '    - Paso 1  Eliminar todos logs [CR]'
    txt += '    - Paso 2  Testear canales (todos) [CR]'
    txt += '    - Paso 3  Testear servidores (todos) [CR]'
    txt += '    - Paso 4  Subir a la web (todo [CR]'

    txt += '[CR][CR]'
    txt += '*) Observaciones: [CR]'
    txt += '    Al subir los tests a la web, se hace el upload de todos los logs existentes en local. Por esta razón es preferible eliminar los anteriores antes de testear, así sólo se subirán los nuevos que se realizen.'
    txt += '[CR][CR]'
    txt += '    Para poder testear servidores es necesario que antes se haya hecho el testeo de canales ya que es de allí de dónde se extraen ejemplos para comprobar.'

    platformtools.dialog_textviewer('Pasos y recomendaciones test canales y servidores', txt)
