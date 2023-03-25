# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3: PY3 = True
else: PY3 = False

import os, time, json, re, base64
from collections import OrderedDict

from core.item import Item
from core import httptools, scrapertools, channeltools, filetools
from platformcode import config, logger, platformtools


if PY3:
    platformtools.dialog_ok(config.__addon_name, 'NO ESTA PREPARADO PARA VERSIONES CON PYTHON 3')

# PARÁMETROS GENERALES
# ~ httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = 10

# Para descartar algunos canales que no hay que analizar
CHANNEL_DISCARD = [ 'proves', 'provesfym', 'fym' ]


# Agrupaciones de géneros en función de los títulos en los diferentes canales
selected_genres = {
    'Acción': ['Acción', 'Accion', 'Action', 'Accion y Aventura'],
    'Animación': ['Animación', 'Animacion','Animación e Infantil', 'Animación infantil', 'Animación / Infantil', 'DC Comics', 'DC comics'],
    'Animes': ['Animes', 'Anime', 'animes', 'anime'],
    'Aventura': ['Aventura', 'Aventuras', 'Adventure', 'Action & Adventure', 'Action & adventure', 'Acción & Aventuras', 'Acción & Aventura'],
    'Bélica': ['Bélica', 'Bélico', 'Belica', 'Belico', 'Bélicas', 'Guerra', 'Bélico Guerra', 'War & Politics', 'War & politics', 'Segunda G.M.'],
    'Biografía': ['Biografia', 'Biografía', 'Biográfia', 'Biográfica', 'Biográfico', 'Biográficas', 'Bíografia - Biopic', 'Basado en Hechos Reales', 'Basado en hechos reales', 'Basada en Hechos Reales', 'Basada en hechos reales'],
    'Ciencia ficción': ['Ciencia ficción', 'Ciencia Ficción', 'CienciaFiccion', 'Ciencia-ficcion', 'Sci-Fi & Fantasy', 'Science fiction', 'Science Fiction', 'Sci-fi & fantasy', 'Sci-Fi'],
    'Comedia': ['Comedia', 'Comedy', 'Parodias', 'Parodia'],
    'Clásico': ['Cine mudo', 'Cine Mudo', 'Cine clásico', 'Cine Clásico', 'Clásico'],
    'Crimen': ['Crimen', 'Crímen'],
    'Deporte': ['Deporte', 'Deportes', 'Deportivo', 'Deportivas', 'Sport', 'Fútbol', 'Futbol'],
    'Documental': ['Documental', 'Documentales', 'Mockumentary'],
    'Dorama': ['Doramas', 'Dorama'],
    'Drama': ['Drama', 'Melodrama'],
    'Familiar': ['Familiar', 'Familia', 'Família', 'Family', 'Cine familiar', 'Para toda la familia'],
    'Fantasía': ['Fantasía', 'Fantasia', 'Fantasìa', 'Fantástico', 'Fantastico'],
    'Historia': ['Historia', 'Histórico', 'Historico', 'Histórica', 'Historia antigua', 'Historia contemporánea', 'Historias cruzadas'],
    'Infantil': ['Infantil', 'Infantiles', 'Kids', 'Infancia', 'Niños', 'Peliculas infantiles', 'Películas para Niños', 'Cine infantil'],
    'Misterio': ['Misterio', 'Mystery'],
    'Música': ['Música', 'Musical', 'Musica', 'Hip Hop', 'Jazz'],
    'Novela': ['Novela', 'Novelas', 'Soap', 'Soaps'],
    'Romance': ['Romance', 'Romántica', 'Romántico', 'Las mejores peliculas romanticas'],
    'Suspense': ['Suspense', 'Suspenso', 'Intriga'],
    'Terror': ['Terror', 'Horror'],
    'Thriller': ['Thriller'],
    'Western': ['Western', 'Oeste', 'Wester', 'Peliculas del oeste', 'Spaghetti Western'],
    'X (adultos +18)': ['Animación para Adultos', 'Erótica', 'Erótico', 'Erotico', 'Erotica', 'Erotismo', 'Xxx, erotico', 'Adultos +18', 'Eróticas +18', 'Eroticas +18', 'Pornografía', 'xxx / adultos']
}


filename_genres_test = os.path.join(config.get_data_path(), 'genres_test.log')
filename_genres_analyze = os.path.join(config.get_data_path(), 'genres_analyze.log')
filename_generos_py = os.path.join(config.get_runtime_path(), 'modules', 'generos.py')

filename_info_channels_csv = os.path.join(config.get_data_path(), 'info_channels.csv')


# NAVEGACIÓN

def mainlist(item):
    logger.info()
    itemlist = []

    if config.get_setting('developer_mode', default=False):
        itemlist.append(Item(channel=item.channel, action='show_help_generos', title= "Información pasos/recomendaciones actualizar 'generos.py'", folder=False, thumbnail=config.get_thumb('news') ))

        itemlist.append(Item(channel=item.channel, action='info_channels', title='Información canales (creación info_channels.csv)', plot = 'Recorrer todos los canales y generar fichero info_channels.log en userdata', folder=False, thumbnail=config.get_thumb('news') ))

        itemlist.append(Item(channel=item.channel, action='test_channels', title='1 - Testear géneros en los canales', plot = 'Recorrer todos los canales para comprobar sus géneros y generar fichero genres_test.log en userdata', thumbnail=config.get_thumb('stack'), folder=False ))
        itemlist.append(Item(channel=item.channel, action='test_channels_selected', title='2 - Re-Testear uno ó varios canales concretos', plot = 'Actualizar testeo de géneros para canales concretos que puedan haber fallado o cambiado', thumbnail=config.get_thumb('stack'), folder=False ))

        itemlist.append(Item(channel=item.channel, action='analyze_genres', title='3 - Analizar log final de géneros', plot = 'Analizar genres_test.log y generar genres_analyze.log con la selección de la variable selected_genres', thumbnail=config.get_thumb('folder'), folder=False ))
        itemlist.append(Item(channel=item.channel, action='update_generos', title='4 - Actualizar módulo generos.py del addon', plot = 'Modifica la variable all_genres_64 en el módulo público que se incluirá en el addon', thumbnail=config.get_thumb('computer'), folder=False ))

    return itemlist

def acumula_log_text(txt):
    logger.info()

    test_filelog.write(txt + '\n')


def test_channels(item):
    logger.info()

    global test_filelog

    existe = filetools.exists(filename_genres_test)
    if existe == True:
        if not platformtools.dialog_yesno(config.__addon_name, '¿ Confirma sobrescribir el fichero  -->  [COLOR yellow] genres_test.log [/COLOR] ?'): return

    test_filelog = open(filename_genres_test, 'w')

    acumula_log_text('INICIO TEST el %s con versión %s' % (time.strftime("%Y-%m-%d"), config.__settings__.getAddonInfo('version')))

    total_time = 0 
    num_tested = 0

    ch_list = channeltools.get_channels_list()
    for ch in ch_list:
        if ch['id'] in CHANNEL_DISCARD: continue

        if 'documentary' in ch['categories']: continue

        if ch['active'] == False:
            platformtools.dialog_notification(config.__addon_name, ch['name'] + '  inactivo')
            continue

        if ch['searchable'] == False:
           if ch['id'] == 'pepecineco': pass
           else:
              if not ch['id'] == 'cinelibreonline': continue

        platformtools.dialog_notification(config.__addon_name, ch['name'])

        total_time += test_channel(ch['id'])
        num_tested += 1

    acumula_log_text('\nFINAL TEST duración: %d segundos, analizados: %d canales' % (total_time, num_tested))
    test_filelog.close()

    # Verificar incidencias
    incidencias = ''
    with open(filename_genres_test, 'r') as f: data = f.read(); f.close()
    if 'Error en el test' in data:
        incidencias += '[CR]Ha habido algún error en alguno de los canales!'
    if '\n0 géneros' in data:
        incidencias += '[CR]Algún canal no ha devuelto los géneros correctamente!'

    if platformtools.dialog_yesno(config.__addon_name, 'Tests finalizados en %d canales' % num_tested, 'Duración : %d segundos' % total_time, incidencias): 
       show_test_generos(item)

    #platformtools.dialog_ok(config.__addon_name, 'Tests finalizados en %d canales' % num_tested, 'Duración : %d segundos' % total_time, incidencias)

    return False


def test_channels_selected(item):
    logger.info()

    existe = filetools.exists(filename_genres_test)
    if existe == True:
        if not platformtools.dialog_yesno(config.__addon_name, '¿ Confirma sobrescribir el fichero  -->  [COLOR yellow] genres_test.log [/COLOR] ?'): return
    else:
        platformtools.dialog_notification(config.__addon_name, 'No exite genres_analyze.log')
        return

    global test_filelog

    # Tria canals
    lista = []
    ch_list = channeltools.get_channels_list()
    for ch in ch_list:
        if ch['id'] in CHANNEL_DISCARD: continue

        if 'documentary' in ch['categories']: continue

        if ch['active'] == False:
            platformtools.dialog_notification(config.__addon_name, ch['name'] + '  inactivo')
            continue

        if ch['searchable'] == False:
           if ch['id'] == 'pepecineco': pass
           else:
              if not ch['id'] == 'cinelibreonline': continue
 
        lbl = '[COLOR cyan][B]' + ch['name'] + '[/B][/COLOR]'
        lbl += ' [%s]' % ', '.join(ch['language'])
        lbl += ' [%s]' % ', '.join(ch['categories'])
        lista.append({'id': ch['id'], 'label': lbl})

    preselect = []
    ret = platformtools.dialog_multiselect("Escoger canales para testear géneros:", [c['label'] for c in lista], preselect=preselect)
    seleccionados = [] if ret == None else [lista[i]['id'] for i in ret]

    if not seleccionados: return

    # Tests dels canals triats amb filename_genres_test_temp
    filename_genres_test_temp = os.path.join(config.get_data_path(), 'genres_test_temp.log')

    test_filelog = open(filename_genres_test_temp, 'w')
    total_time = 0
    num_tested = 0
    for ch in seleccionados:
        total_time += test_channel(ch)
        num_tested += 1

    acumula_log_text('\nFINAL TEST duración: %d segundos, analizados: %d canales' % (total_time, num_tested))
    test_filelog.close()

    # Actualitzar filename_genres_test
    with open(filename_genres_test_temp, 'r') as f: data_temp = f.read(); f.close()

    with open(filename_genres_test, 'r') as f: data = f.read(); f.close()

    for ch in seleccionados:
        patron = '(\*\) Canal %s.*?)(?:\*\) Canal|FINAL TEST)' % ch
        sel_temp = scrapertools.find_single_match(data_temp, patron)
        sel = scrapertools.find_single_match(data, patron)
        if not sel_temp: continue
        if sel:
            data = data.replace(sel, sel_temp)
        else: # si no existeix afegir al final
            sel = scrapertools.find_single_match(data, '(FINAL TEST)')
            data = data.replace(sel, sel_temp + '\n\nFINAL TEST')

    with open(filename_genres_test, 'wb') as f: f.write(data); f.close()

    # Verificar incidencias
    incidencias = ''
    if 'Error en el test' in data:
        incidencias += '[CR]Ha habido algún error en alguno de los canales!'
    if '\n0 géneros' in data:
        incidencias += '[CR]Algún canal no ha devuelto los géneros correctamente!'

    # ~ platformtools.dialog_ok(config.__addon_name, 'ReTests finalizados en %d canales' % num_tested, 'Duración : %d segundos' % total_time, incidencias)
    platformtools.dialog_ok(config.__addon_name, 'ReTests finalizados')

    return False


def test_channel(channel):
    logger.info()

    t_ini = time.time()

    acumula_log_text('\n\n*) Canal %s' % channel)

    try:
        # ~ py_channel = 'cinefox' if channel == 'gnula_biz' else channel
        data = ''
        py_channel = channel

        try:
           with open(os.path.join(config.get_runtime_path(), 'channels', py_channel + '.py'), 'r') as f: data=f.read(); f.close()
        except:
           channel_py = py_channel + '.py'
           filename_py = os.path.join(config.get_runtime_path(), 'channels', channel_py)

           data = filetools.read(filename_py)

        # Té funció generos ? Pelis i/o series ?
        if 'generos = [' in data or 'genres = [' in data or 'generos = {' in data or 'genres = {' in data or 'generos = (' in data or 'genres = (' in data:
            acumula_log_text('Géneros manualmente.')

        if not 'def generos' in data:
            acumula_log_text('No tiene función géneros.')
            # ~ if channel in ['tvvip', 'pelisipad']:
                # ~ test_canal = __import__('channels.' + channel, fromlist=[''])
                # ~ if channel == 'tvvip':
                # ~     url = 'http://tv-vip.com/json/playlist/peliculas/index.json'
                # ~ else:
                    # ~ url = 'http://pelisipad.com/black_json/list/peliculas/list.js'
                # ~ itemlist = test_canal.list_subcategorias(Item(channel=channel, title=channel, search_type = 'movie', url = url))
                # ~ if channel == 'tvvip':
                    # ~ itemlist.append(Item(channel=channel, title='Documentales', search_type = 'movie', action = 'list_all', url = 'http://tv-vip.com/json/playlist/documentales/index.json'))
                # ~ listar_generos(itemlist, 'movie', channel)
        else:
            test_canal = __import__('channels.' + channel, fromlist=[''])

            te_pelis = 'def mainlist_pelis' in data
            te_series = 'def mainlist_series' in data

            if te_pelis and te_series:
                data_def = scrapertools.find_single_match(data, 'def mainlist_pelis(.*?)return itemlist')
                if "'generos'" in data_def or '"generos"' in data_def:
                    itemlist = test_canal.generos(Item(channel=channel, title=channel, search_type = 'movie'))
                    listar_generos(itemlist, 'movie', channel)

                data_def = scrapertools.find_single_match(data, 'def mainlist_series(.*?)return itemlist')
                if "'generos'" in data_def or '"generos"' in data_def:
                    itemlist = test_canal.generos(Item(channel=channel, title=channel, search_type = 'tvshow'))
                    listar_generos(itemlist, 'tvshow', channel)

            elif te_pelis:
                itemlist = test_canal.generos(Item(channel=channel, title=channel, search_type = 'movie'))
                listar_generos(itemlist, 'movie', channel)

            elif te_series:
                itemlist = test_canal.generos(Item(channel=channel, title=channel, search_type = 'tvshow'))
                listar_generos(itemlist, 'tvshow', channel)

    except:
        acumula_log_text('Error en el test')
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    t_fin = time.time()
    elapsed = (t_fin - t_ini)

    return elapsed


def listar_generos(itemlist, search_type, channel):
    logger.info()

    acumula_log_text('\n%d géneros para %s: ' % (len(itemlist), search_type))

    for it in itemlist:
        title = re.sub('\([0-9.]+\)', '', it.title).strip()
        enlace = OrderedDict([("channel", it.channel), ("search_type", search_type), ("title", title), ("action", it.action), ("url", it.url)])
        for x in it.__dict__:
            if x not in ['action', 'title', 'url', 'search_type', 'infoLabels', 'channel', 'thumbnail']: enlace.update({x: it.__dict__[x]})

        acumula_log_text('    '+json.dumps(enlace, ensure_ascii=False) + ',')


def analyze_genres(item):
    logger.info()

    global test_filelog

    existe = filetools.exists(filename_genres_analyze)
    if existe == True:
        if not platformtools.dialog_yesno(config.__addon_name, '¿ Confirma sobrescribir el fichero  -->  [COLOR cyan] genres_analyze.log [/COLOR] ?'): return
    else:
        platformtools.dialog_notification(config.__addon_name, 'No exite genres_analyze.log')
        return

    all_genres = {}
    not_selected = []

    with open(filename_genres_test, 'r') as f: data = f.read(); f.close()

    # seleccionar
    matches = re.findall("(    \{.*?\},)", data, flags=re.DOTALL)
    for match in matches:
        title = re.findall('"title": "([^"]+)"', match, flags=re.DOTALL)[0]

        if "zoowomaniacos" in match:
            match = str(match).replace('"post": {"searchPanes[a5][0]":', '"repost": "SI"' + ', "searchPanes[a5][0]":').replace('"searchPanes[a3][0]": ""}', '"searchPanes[a3][0]": ""' + ", ")

        notfound = True
        for genero in selected_genres:
            if title in selected_genres[genero]:
                # ~ if genero == 'Erótica' and '"channel": "pedropolis"' in match: continue # descartar porno no erótico
                if genero not in all_genres: all_genres[genero] = []
                all_genres[genero].append(match)
                notfound = False
                break

        if notfound:
            not_selected.append(match)

    # llistar
    test_filelog = open(filename_genres_analyze, 'w')

    xurro = '{\n'
    for key, items in all_genres.items():
        xurro += '  "%s": [\n' % key
        for lin in items:
            xurro += lin + '\n'
        xurro += '  ],\n'
    xurro += '}\n'

    acumula_log_text('TODOS LOS GÉNEROS EN UNA LÍNEA B64ENCODED:')
    acumula_log_text("all_genres_64 = '" + base64.b64encode(xurro) + "'")


    acumula_log_text('')
    acumula_log_text('TOTALES GÉNEROS SELECCIONADOS:')
    n_selected = 0
    for key in sorted(all_genres):
        n_pelis = 0; n_series = 0
        for lin in all_genres[key]: 
            if '"search_type": "movie"' in lin: 
                n_pelis += 1 
            else:
                n_series += 1
        acumula_log_text( '%s : %d (P: %d + S: %d)' % (key, len(all_genres[key]), n_pelis, n_series) )
        n_selected += len(all_genres[key])

    acumula_log_text('')
    acumula_log_text('LISTA DE GÉNEROS SELECCIONADOS: (%d)' % n_selected)
    acumula_log_text(xurro)

    acumula_log_text('')
    acumula_log_text('LISTA DE GÉNEROS NO SELECCIONADOS: (%d)' % len(not_selected))
    for lin in not_selected:
        acumula_log_text(lin)

    platformtools.dialog_ok(config.__addon_name, 'Análisis finalizado. %d enlaces a géneros seleccionados' % n_selected)

    return False


def update_generos(item):
    logger.info()

    existe = filetools.exists(filename_genres_analyze)
    if existe == False:
        platformtools.dialog_notification(config.__addon_name, 'No exite genres_analyze.log')
        return

    existe = filetools.exists(filename_generos_py)
    if existe == True:
        if not platformtools.dialog_yesno(config.__addon_name, '¿ Confirma sobrescribir el fichero  -->  [COLOR red] generos.py [/COLOR] ?'): return
    else:
        platformtools.dialog_notification(config.__addon_name, 'No exite genrros.py')
        return

    with open(filename_genres_analyze, 'r') as f: data = f.read(); f.close()
    b64 = re.findall("all_genres_64 = '([^']+)'", data, flags=re.DOTALL)[0]

    if len(b64) == 0:
        platformtools.dialog_ok(config.__addon_name, 'Línea b64encoded no encontrada!')
        return False

    with open(filename_generos_py, 'r') as f: data = f.read(); f.close()

    data = re.sub("all_genres_64 = '[^']+'", "all_genres_64 = '" + b64 + "'", data)

    with open(filename_generos_py, 'wb') as f: f.write(data); f.close()


    platformtools.dialog_ok(config.__addon_name, 'Módulo generos.py actualizado. Tamaño b64: %d' % len(b64))

    return False


def neteja_csv(txt):
    logger.info()

    return str(txt)[1:-1].replace("'", '')

def info_channels(item):
    logger.info()

    global test_filelog

    csv_file = open(filename_info_channels_csv, 'w')

    txt_csv = 'Channel;categories;language;search_types;proxies;do_downloadpage;use_cache;notes'
    csv_file.write(txt_csv + '\n')

    num_tested = 0
    ch_list = channeltools.get_channels_list()
    for ch in ch_list:
        if ch['id'] in CHANNEL_DISCARD: continue

        with open(os.path.join(config.get_runtime_path(), 'channels', ch['id'] + '.py'), 'r') as f: data=f.read(); f.close()
        if 'def configurar_proxies' in data:
            if '\ndef configurar_proxies' in data:
                txt_proxies = 'Proxies enabled'
            else:
                txt_proxies = 'Proxies disabled'
        else:
            txt_proxies = 'No proxies'

        txt_dodown = 'True' if '\ndef do_downloadpage' in data else 'False'
        txt_cache = 'True' if 'use_cache=True' in data else 'False'

        txt_csv = ch['id'] + ';' + neteja_csv(ch['categories']) + ';' + neteja_csv(ch['language']) + ';' + neteja_csv(ch['search_types'])
        txt_csv += ';' + txt_proxies + ';' + txt_dodown + ';' + txt_cache + ';' + ch['notes']
        csv_file.write(txt_csv + '\n')

        num_tested += 1

    csv_file.close()

    platformtools.dialog_ok(config.__addon_name, 'Infos de %d canales en %s' % (num_tested, filename_info_channels_csv))

    return False


def show_help_generos(item):
    logger.info()

    txt = '*) Previamente es recomedable tener una copia de seguridad de todo los ficheros generados en la ultima'
    txt += '  gestión de´géneros, y ejecutar coorelativamente los paso 1 a 4 (el paso 2 es opcional) en función'
    txt += '  de si el resultato del test no ha sido en su totalidad satisfactorio.'

    txt += '[CR][CR]'
    txt += '*) Archivos que interviene ubicados en addon_data: [CR]'
    txt += '    - Paso 1  creación de  -->  genres_test.log [CR]'
    txt += '    - Paso 2  re-actualizacion si procede de uno ó varios canales sobre  -->  genres_test.log [CR]'
    txt += '    - Paso 3  creación B64  desde  -->  genres_analyze.log[CR]'
    txt += '    - Paso 4  actualización modulo  -->  generos.py  del addon[CR]'

    platformtools.dialog_textviewer('Pasos y recomendaciones actualizacion Generos.py', txt)


def show_test_generos(item):
    logger.info()

    try:
       with open(filename_genres_test, 'r') as f: txt=f.read(); f.close()

       platformtools.dialog_textviewer('Test de Géneros', txt)
    except:
      pass
