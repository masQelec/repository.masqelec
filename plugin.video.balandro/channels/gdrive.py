# -*- coding: utf-8 -*-

# Canal privado para acceso a GDrive

# Requiere haber añadido manualmente estas claves en settings.xml (copiarlas del settings.xml del addon gdrive habiendo hecho el enroll)
# <setting id="gdrive1_client_id">...</setting>
# <setting id="gdrive1_client_secret">...</setting>
# <setting id="gdrive1_code">...</setting>
# <setting id="gdrive1_username">...</setting>
# <setting id="gdrive1_auth_access_token">...</setting>
# <setting id="gdrive1_auth_refresh_token">...</setting>

# Requerimientos de los contenidos en GDrive:

# - Los vídeos de películas deberían tener esta nomenclatura: Título de la peli (año) [géneros] [calidad]
#   (título y año requeridos para acceder a TMDB. géneros y calidad opcionales)
# - Los vídeos de episodios deberían tener esta nomenclatura: Título de la serie - SnnEnn (o TnnEnn o nnXnn) - título del episodio
#   (título de serie y Nº de temporada y episodio requeridos para acceder a TMDB. título del episodio opcional)
#   Los vídeos de episodios se identifican por tener SnnEnn o TnnEnn o nnXnn (S,E,T,X pueden ser en mayúsculas o minúsculas, nn números con 1 o 2 cifras)
# - Las series deberían estar dentro de ciertas carpetas (ID_FOLDERS_TVSHOWS) y tener subcarpetas tipo Season NN (o Temporada NN o Temp NN)
#   (preferiblemente indicar (año) en las carpetas con el nombre de la serie para detectar mejor en TMDB)
#   Ej: Series/The Big Bang Theory (2007)/Temporada 12/
# - ...

# Ejemplos:
# Cartas a Roxanne (2019) [Comedia, Drama].mp4
# Cartas a Roxanne (2019) [Comedia, Drama] [4K].mp4
# The Big Bang Theory - S12E02 - Penny y Sheldon.mp4
# The Big Bang Theory - S12E03.avi
# The Big Bang Theory - s12e04.mkv
# The Big Bang Theory - T12E05.mkv
# The Big Bang Theory (2007) - T12E06.mkv
# The Big Bang Theory - 12x05.mkv

# Notas:
# - La búsqueda en GD tiene en cuenta los acentos. Ej: Si una peli se titula 101 dálmatas, no se encuentra buscando dalmatas, hay que buscar dálmatas.

# Parámetros configurables:

# - Indicar en ID_FOLDERS_TVSHOWS las carpetas que contienen series con la estructura de carpetas requerida. Asignar [] si no se usa.
#   (ver los ids de las carpetas en Google Drive, e indicar parejas de ('id', 'nombre') para cada carpeta)

# - Indicar en ID_FOLDERS_SHORTCUTS las carpetas a las que se quiere crear un acceso directo. Asignar [] si no se usa.
#   (ver los ids de las carpetas en Google Drive, e indicar parejas de ('id', 'nombre') para cada carpeta)

# - Indicar en TAGS_GENEROS los tags de géneros por los que buscar en los vídeos. Asignar [] si no se usa.
#   (requiere que los nombres de los ficheros tengan esos géneros escritos)

# - Indicar en TAGS_CALIDADES los tags de calidades por los que buscar en los vídeos. Asignar [] si no se usa.
#   (requiere que los nombres de los ficheros tengan esas calidades escritas)

# - Asignar un número en PERPAGE para indicar los elementos por página que se quieren mostrar.
#   (cuanto más alto, más tardará en mostrarse la página por los accesos a TMDB)


ID_FOLDERS_TVSHOWS = [
    ('1kBkzN3gpz4te1qpbqZFha_LwvhP3a6-4', 'Series'),
    ('1EJ8aSCS6GO_Y3ueWhDa8cOUndRH7iihL', 'Series Infantiles'),
]

ID_FOLDERS_SHORTCUTS = [
    ('1rQQSpZo-WXY9UU1IIoxBqUcGBEbVTPxt', 'Anime'),
    ('1rkVSwrdAowfin-8bGREcDqfTPcKPhrRZ', 'Documentales'),
    ('1UvmEGTVeXQXZkk0biANZy_1lIXE2BFDY', 'Infantil'),
    ('1sVT3qPAmY58O2OoIEIcjzNa3PwWn1tun', 'Peliculas'),
    ('1HEbOPEZjTvZ1N_QmYiHaMcokeQzqd23m', '3D'),
    ('1Bms4hlLmEdAQilUw8RY42HY43EiDvtB4', '4K'),
]

TAGS_GENEROS = [
    'Anime',
    'Acción',
    'Animación',
    'Aventura',
    'Bélica',
    'Ciencia ficción',
    'Comedia',
    'Crimen',
    'Documental',
    'Drama',
    'Familia',
    'Fantasía',
    'Guerra',
    'Historia',
    'Infantil',
    'Intriga',
    'Misterio',
    'Música',
    'Romance',
    'Suspense',
    'Terror',
    'Thriller',
    'Western'
    ]

TAGS_CALIDADES = ['4K', '1080p', '720p', '480p', '360p']

PERPAGE = 10 # películas por página (No pasar de 30 por la limitación de llamadas a tmdb)

COLOR_FOLDERS_TVSHOWS = 'yellow'
COLOR_FOLDERS_SHORTCUTS = 'cyan'


import sys

if sys.version_info[0] < 3:
    import urllib
else:
    import urllib.parse as urllib


import re, os, time

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb

from lib.gdrivetools import gdrive


def mainlist(item):
    return mainlist_drives(item)

def mainlist_pelis(item):
    return mainlist_drives(item)

def mainlist_series(item):
    return mainlist_drives(item)


def mainlist_drives(item):
    logger.info()
    itemlist = []

    gdrive1_username = config.get_setting('gdrive1_username', default='')

    color_alert = config.get_setting('notification_alert_color', default='red')
    color_avis  = config.get_setting('notification_avis_color', default='yellow')

    if not gdrive1_username:
        platformtools.dialog_notification('Gdrive', '[B][COLOR %s]Sin credenciales[/B][/COLOR]' % color_alert)
        return

    gd = gdrive('gdrive1')
    drives = gd.getDrives()
    if drives is None:
        platformtools.dialog_notification('Gdrive', '[B][COLOR %s]Error login[/B][/COLOR]' % color_avis)
        return itemlist

    plot = 'Acceso a todo lo que el usuario tiene permiso (propio, compartido y drives), y acceso directo a carpetas predefinidas.'
    itemlist.append(item.clone( title = 'Acceso Global', action = 'list_drive', drive_id = None, drive_name = 'global', plot=plot ))

    plot = 'Acceso sólo a los ficheros/carpetas del propio usuario o que le hayan compartido.'
    itemlist.append(item.clone( title = 'Acceso Usuario', action = 'list_drive', drive_id = 'root', drive_name = 'usuario', plot=plot ))

    plot = 'Acceso sólo a los ficheros/carpetas que hay en este drive.'
    for drive_id, drive_name in drives:
        itemlist.append(item.clone( title = 'Acceso Drive: ' + drive_name, action = 'list_drive', drive_id = drive_id, drive_name = drive_name, plot=plot ))

    return itemlist


def list_drive(item):
    logger.info()
    itemlist = []

    item.category = 'GD_' + item.drive_name

    itemlist.append(item.clone( title = 'Últimos vídeos', action = 'list_all', drive_q = "", nextPageToken=None ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios' ))

    if len(TAGS_GENEROS) > 0:
        itemlist.append(item.clone( title = 'Por género', action = 'generos' ))

    if len(TAGS_CALIDADES) > 0:
        itemlist.append(item.clone( title = 'Por calidad', action = 'calidades' ))

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie' ))

    if not item.drive_id:
        for fid, fname in ID_FOLDERS_SHORTCUTS:
            itemlist.append(item.clone( title = '[COLOR %s]%s[/COLOR]' % (COLOR_FOLDERS_SHORTCUTS, fname), action = 'carpetas', drive_parent = fid ))

        for fid, fname in ID_FOLDERS_TVSHOWS:
            itemlist.append(item.clone( title = '[COLOR %s]%s[/COLOR]' % (COLOR_FOLDERS_TVSHOWS, fname), action = 'carpeta_series', drive_parent = fid ))

        if len(ID_FOLDERS_TVSHOWS) > 0:
            itemlist.append(item.clone( title = 'Buscar series ...', action = 'search', search_type = 'tvshow' ))

    elif item.drive_id == 'root':
        itemlist.append(item.clone( title = 'Carpetas propias del usuario', action = 'carpetas', drive_parent = 'root' ))
        itemlist.append(item.clone( title = 'Carpetas compartidas con el usuario', action = 'carpetas', drive_parent = '' ))

    else:
        itemlist.append(item.clone( title = 'Carpetas del Gdrive ' + item.drive_name, action = 'carpetas', drive_parent = '' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1950, -1):
        itemlist.append(item.clone( title=str(x), action='list_all', drive_q = "name+contains+'(%s)'" % x, nextPageToken=None ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    for x in TAGS_GENEROS:
        itemlist.append(item.clone( title=x, action='list_all', drive_q = "name+contains+'(%s)'" % urllib.quote_plus(x) ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    for x in TAGS_CALIDADES:
        itemlist.append(item.clone( title=x, action='list_all', drive_q = "name+contains+'(%s)'" % urllib.quote_plus(x) ))

    return itemlist


def carpetas(item):
    logger.info()
    itemlist = []

    q = "mimeType+=+'application/vnd.google-apps.folder'+and+trashed%3Dfalse"

    if item.drive_parent: q += "+and+'"+str(item.drive_parent)+"'+in+parents"
    elif item.drive_id == 'root': q += "+and+sharedWithMe%3Dtrue"
    elif item.drive_id: q += "+and+'"+str(item.drive_id)+"'+in+parents"

    gd = gdrive('gdrive1')
    files = gd.getFiles(item.drive_id, q=q, nextPageToken=item.nextPageToken, perpage=50, orden='name')
    if not files or 'files' not in files: return itemlist

    for f in files['files']:
        itemlist.append(item.clone( title=f['name'], action='carpetas', drive_parent = f['id'], nextPageToken=None ))
        logger.info('%s %s' % (f['id'], f['name']))

    if 'nextPageToken' in files and files['nextPageToken']:
        itemlist.append(item.clone( title=">> Siguientes carpetas", nextPageToken=files['nextPageToken'], action='carpetas', text_color='coral' ))

    if item.drive_parent:
        itemlist.extend(list_all(item)) # añadir vídeos de la carpeta

    return itemlist


def carpeta_series(item):
    logger.info()
    itemlist = []
    if not item.drive_parent: return itemlist

    q = "mimeType+=+'application/vnd.google-apps.folder'+and+trashed%3Dfalse"
    q += "+and+'"+str(item.drive_parent)+"'+in+parents"

    gd = gdrive('gdrive1')
    files = gd.getFiles(item.drive_id, q=q, nextPageToken=item.nextPageToken, perpage=PERPAGE, orden='name')
    if not files or 'files' not in files: return itemlist

    for f in files['files']:
        title = f['name']
        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'

        itemlist.append(item.clone( action='carpeta_temporadas', title=title, drive_parent=f['id'], nextPageToken=None, thumbnail=config.get_thumb('dev'),
                                    contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'tvshowtitle': title} ))

    tmdb.set_infoLabels(itemlist)

    if 'nextPageToken' in files and files['nextPageToken']:
        itemlist.append(item.clone( title=">> Página siguiente", nextPageToken=files['nextPageToken'], action='carpeta_series', text_color='coral' ))

    return itemlist


def carpeta_temporadas(item):
    logger.info()
    itemlist = []
    if not item.drive_parent: return itemlist

    q = "mimeType+=+'application/vnd.google-apps.folder'+and+trashed%3Dfalse"
    q += "+and+'"+str(item.drive_parent)+"'+in+parents"

    gd = gdrive('gdrive1')
    files = gd.getFiles(item.drive_id, q=q, perpage=30, orden='name')
    if not files or 'files' not in files: return itemlist

    for f in files['files']:
        season = scrapertools.find_single_match(f['name'], '(\d+)')
        if not season: continue

        itemlist.append(item.clone( action='list_all', title=f['name'], drive_parent=f['id'], thumbnail=config.get_thumb('dev'),
                                    contentType='season', contentSeason = season ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    q = "mimeType+contains+'video'+and+trashed%3Dfalse"

    if item.drive_q: q += "+and+" + item.drive_q
    if item.drive_parent: q += "+and+" + "'"+str(item.drive_parent)+"'+in+parents"

    orden = 'name' if item.drive_parent else 'modifiedTime+desc'

    gd = gdrive('gdrive1')
    files = gd.getFiles(item.drive_id, q=q, nextPageToken=item.nextPageToken, perpage=PERPAGE, orden=orden)

    if not files or 'files' not in files: return itemlist

    for f in files['files']:
        title = f['name']
        title = re.sub('\.\w+$', '', title) # quitar extensión

        s_e = scrapertools.find_single_match(title, '(?i)((?:S|T)(\d+)E(\d+))')
        if not s_e: s_e = scrapertools.find_single_match(title, '(?i)((\d+)x(\d+))')
        if s_e:
            tipo = 'tvshow'
            titulo = title
            if ' -' in title: title = title.split(' -')[0].strip()
            elif '- ' in title: title = title.split('- ')[0].strip()
            if s_e[0] in title: title = title.split(s_e[0])[0].strip()
            if not title: title = titulo

            season = s_e[1]
            episode = s_e[2]
            year = scrapertools.find_single_match(title, '\((\d{4})\)')
            if year:
                title = title.replace('(%s)' % year, '').strip()
                titulo = titulo.replace('(%s)' % year, '').strip()
            else:
                year = '-'
        else:
            tipo = 'movie'
            year = scrapertools.find_single_match(title, '\((\d{4})\)')
            if year:
                aux = title.split('(%s)' % year)
                title = aux[0].strip()
                info = aux[1].replace('...','').strip()
                titulo = '%s [COLOR red]%s[/COLOR]' % (title, info)
            else:
                year = '-'
                titulo = title
        title = title.replace('Copia de ', '')

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', title=titulo, file_id=f['id'], thumbnail=config.get_thumb('dev'),
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            if not episode: continue
            if item.contentSerieName: # viene de listado de series y ya está identificada
                itemlist.append(item.clone( action='findvideos', title=titulo, file_id=f['id'], thumbnail=config.get_thumb('dev'),
                                            contentType='episode', contentSeason = season, contentEpisodeNumber = episode ))
            else:
                itemlist.append(item.clone( action='findvideos', title=titulo, file_id=f['id'], thumbnail=config.get_thumb('dev'),
                                            contentType='episode', contentSerieName=title, contentSeason = season, contentEpisodeNumber = episode ))

    tmdb.set_infoLabels(itemlist)

    if 'nextPageToken' in files and files['nextPageToken']:
        itemlist.append(item.clone( title=">> Página siguiente", nextPageToken=files['nextPageToken'], action='list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    gd = gdrive('gdrive1')

    datos = gd.getFileInfo(item.file_id)
    if datos and 'url_directo' in datos:
        try:
            qlty = '%sx%s' % (datos['videoMediaMetadata']['width'], datos['videoMediaMetadata']['height'])
        except:
            qlty = 'Original'
        try:
            othr = ''
            othr = config.format_bytes(int(datos['size']))
            othr += ', %s' % config.format_seconds_to_duration(int(datos['videoMediaMetadata']['durationMillis'])/1000)
        except:
            pass
        itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = datos['url_directo'],
                                        quality = qlty, other=othr ))

        if datos['extra']:
            for v in datos['extra']:
                itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = v[1], quality = v[0] ))

    return itemlist


def search_series(item):
    logger.info()
    itemlist = []

    q = "mimeType+=+'application/vnd.google-apps.folder'+and+trashed%3Dfalse"

    if len(ID_FOLDERS_TVSHOWS) > 0:
        q += "+and+("
        for i, (fid, fname) in enumerate(ID_FOLDERS_TVSHOWS):
            if i > 0: q += '+or+'
            q += "'%s'+in+parents" % fid
        q += ")"

    if item.drive_q: 
        q += "+and+" + item.drive_q

    gd = gdrive('gdrive1')
    files = gd.getFiles(item.drive_id, q=q, nextPageToken=item.nextPageToken, perpage=PERPAGE, orden='name')
    if not files or 'files' not in files: return itemlist

    for f in files['files']:
        title = f['name']
        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'

        itemlist.append(item.clone( action='carpeta_temporadas', title=title, drive_parent=f['id'], nextPageToken=None, thumbnail=config.get_thumb('dev'),
                                    contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'tvshowtitle': title} ))

    tmdb.set_infoLabels(itemlist)

    if 'nextPageToken' in files and files['nextPageToken']:
        itemlist.append(item.clone( title=">> Página siguiente", nextPageToken=files['nextPageToken'], action='search_series', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.drive_q = "name+contains+'%s'" % urllib.quote_plus(texto.replace("'",''))
        item.nextPageToken = None
        if item.search_type == 'tvshow':
            return search_series(item)
        else:
            return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
