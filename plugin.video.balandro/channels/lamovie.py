# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3:
    import urllib.parse as _urllib

    from urllib.parse import urlencode
else:
    import urllib as _urllib

    from urllib import urlencode


import ast

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

from core.jsontools import json


host = 'https://la.movie/'


# ~ 31/7/25  Los Generos NO se Incluyen en generos.py


def do_downloadapi(type, filter, page, terms, _id, season, order):
    try:
        url_filter = _urllib.urlencode({'filter':"{{{0}}}".format(filter)})
    except:
        url_filter = _urllib.urlencode({'filter':"{}"})

    if terms: url_terms = _urllib.quote(str(terms))

    if type == 'season':
        url = '{0}wp-api/v1/single/episodes/list?_id={1}&season={2}&postsPerPage=15&page={3}'.format(host, _id, season, page)

    elif type == 'links':
        url = '{0}wp-api/v1/player?postId={1}&demo=0'.format(host, _id)

    elif type == 'search':
        url = '{0}wp-api/v1/search?{1}&postType=any&q={2}&postsPerPage=25&page={3}'.format(host, url_filter, url_terms, page)

    else:
        type = '{0}s'.format(type)

        url = '{0}wp-api/v1/listing/{1}?{2}&order=desc&postType={1}&postsPerPage=20&page={3}&orderBy='.format(host, type, url_filter, page)

        if not order: order = 'latest'

        url += order

    headers = {'Referer': host}

    resp = httptools.downloadpage(url, headers = headers)

    if str(resp.code) == '200':
        data = resp.data
        return data
    else:
        return ''


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', text_color='springgreen' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'peliculas/', order='popular', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'peliculas/', order='rated', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'peliculas/', order='views', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'list_filter', grp='genres', group = 'movie', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'list_filter', grp='years', group = 'movie', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'list_filter', grp='countries', group = 'movie', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'list_filter', grp='providers', group = 'movie', search_type = 'movie', text_color='moccasin' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'series/', order='popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'series/', order='rated', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'series/', order='views', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'list_filter', grp='genres', group = 'tvshow', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por año', action = 'list_filter', grp='years', group = 'tvshow', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action = 'list_filter', grp='countries', group = 'tvshow', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'list_filter', grp='providers', group = 'tvshow', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', group = 'animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes/', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'animes/', group = 'animes', order='popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'animes/', group = 'animes', order='rated', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'animes/', group = 'animes', order='views', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'list_filter', grp='genres', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por año', action = 'list_filter', grp='years', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action = 'list_filter', grp='countries', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'list_filter', grp='providers', group = 'animes', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


# ~ Si venimos de Grupos 
def generos(item):
    logger.info()

    item.grp = 'genres'

    if item.search_type == 'movie':
        item.group = 'movie'
    else:
        item.group = 'tvshow'

    return list_filter(item)

def anios(item):
    logger.info()

    item.grp = 'years'

    if item.search_type == 'movie':
        item.group = 'movie'
    else:
        item.group = 'tvshow'

    return list_filter(item)

def paises(item):
    logger.info()

    item.grp = 'countries'

    if item.search_type == 'movie':
        item.group = 'movie'
    else:
        item.group = 'tvshow'

    return list_filter(item)


def list_filter(item):
    logger.info()
    itemlist = []

    grp = item.grp

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       text_color = 'hotpink'
       if item.group == 'animes': text_color = 'springgreen'

    data = httptools.downloadpage(host).data

    siteconfig = scrapertools.find_single_match(data, "siteConfig\s*=\s*([^<]+)")

    if siteconfig:
        siteconfig = siteconfig.replace("\/", "/")
        patron = '{0}:([^\n]+),'.format(grp)

        fdata = scrapertools.find_single_match(siteconfig, patron)

        try:
           data = ast.literal_eval(fdata)

           for filter in data:
               sfilter = "\"{0}\":[{1}]".format(grp, filter)

               title = str(data[filter]['name']).replace('&amp;', '&')

               if grp == 'providers': title = title.capitalize()

               itemlist.append(item.clone ( title = title, action = "list_all", filter = sfilter, grp = grp, text_color = text_color ))
        except:
            pass

    if grp == 'years':
        return sorted(itemlist, key=lambda x: x.title, reverse=True)

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    type = item.search_type

    if item.page: page = item.page
    else: page = 1

    if item.grp: grp = item.grp
    else: grp = ''

    if item.filter: filter = item.filter
    else: filter = ''

    if item.terms: terms = item.terms
    else: terms = ''

    if item.group: group = item.group
    else: group = ''

    if item.busca: busca = item.busca
    else: busca = ''

    if item.order: order = item.order
    else: order = ''

    if busca == 'search':
        data = do_downloadapi('search', filter, page, terms, '', '', '')

        if not data: return itemlist

        jdata = json.loads(data)

        if not jdata: return itemlist

        contents = jdata['data']['posts']
        pagination = jdata['data']['pagination']

    else:

        if group == 'animes': type = 'anime'

        data = do_downloadapi(type, filter, page, terms, '', '', order)

        if not data: return itemlist

        jdata = json.loads(data)

        if not jdata: return itemlist

        contents = jdata['data']['posts']
        pagination = jdata['data']['pagination']

    for content in contents:
        infoLabels = {}

        item_args = {}

        if type in ['tvshow', 'episode', 'anime']:
            if group == 'animes':
                if busca:
                    if not "'type': 'animes'" in str(content): continue

                title = content['title']

                year = '-'

                try:
                    if ' (' in title:
                        year = title.split(' (')[1]
                        year = year.replace(')', '').strip()

                    if not year == '-':
                        if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
                except:
                    pass

                item_args['title'] = title
                item_args['contentSerieName'] = title
                infoLabels['year'] = year
            else:
                title = content['title']

                year = '-'

                try:
                    if ' (' in title:
                        year = title.split(' (')[1]
                        year = year.replace(')', '').strip()

                    if not year == '-':
                        if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
                except:
                    pass

                item_args['title'] = title
                item_args['contentSerieName'] = title
                infoLabels['year'] = year

            if type == 'episode':
                infoLabels['season'] = content['season_number']
                infoLabels['episode'] = content['episode_number']
                item_args['title'] = '{}x{} {}'.format(infoLabels['season'], infoLabels['episode'], item_args['contentSerieName'])
        else:
            title = content['title']

            year = '-'

            try:
                if ' (' in title:
                    year = title.split(' (')[1]
                    year = year.replace(')', '').strip()

                if not year == '-':
                    if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
            except:
                pass

            item_args['title'] = title
            item_args['contentTitle'] = title
            infoLabels['year'] = year

        tipo = 'movie' if type == 'movie' else 'tvshow'
        sufijo = '' if type != 'all' else tipo

        item_args['sufijo'] = sufijo

        item_args['action'] = 'findvideos' if type in ['movie', 'episode'] else 'temporadas'  

        item_args['languages'] = get_lang(content['lang'])
        item_args['search_type'] = type
        item_args['group'] = group

        if sufijo: item_args['contentType'] = sufijo
        else: item_args['contentType'] = 'tvshow' if group == 'animes' else type

        item_args['_id'] = content['_id']
        item_args['infoLabels'] = infoLabels

        new_item = item.clone(**item_args)

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    if pagination:
        try:
            if pagination['next_page_url']:
                itemlist.append(item.clone (action = 'list_all', title = 'Siguientes ...',
                                            type=type, grp=grp, filter=filter, terms=terms, group=group, busca=busca, order=order, page = page + 1, text_color='coral'))  
        except:
            pass

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    if not isinstance(item.contentSeason, int):
        _id = item._id

        data = do_downloadapi('season', '', 1, '', _id, 1, '')

        if not data: return itemlist

        jdata = json.loads(data)

        if not jdata: return itemlist

        if len(jdata['data']['seasons']) == 1:
            if config.get_setting('channels_seasons', default=True):
                title = 'Temporada ' + jdata['data']['seasons'][0]
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item._id = _id
            item.page = 1
            item.contentType = 'season'
            item.contentSeason = jdata['data']['seasons'][0]
            itemlist = episodios(item)
            return itemlist

        for season in jdata['data']['seasons'][::-1]:
            season = int(season or 1)

            title = 'Temporada ' + str(season)

            itemlist.append(item.clone( action = 'episodios', title = title, _id = _id, page = 1,
                                       contentType = 'season', contentSeason = season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    page = item.page

    _id = item._id

    season = item.contentSeason

    data = do_downloadapi('season', '', page, '', _id, season, '')

    if not data: return itemlist

    jdata = json.loads(data)

    if not jdata: return itemlist

    for episode in jdata['data']['posts']:
        titulo = episode['title']

        temp = episode['season_number']
        epis = episode['episode_number']

        if len(str(epis)) == 1:
            epis = '0' + str(epis)

        titulo = str(temp) + 'x' + str(epis)  + ' ' + titulo

        titulo = titulo.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]')

        _id = episode['_id']

        itemlist.append(item.clone (action='findvideos', title=titulo, _id=_id,
                              contentSerieName=item.contentSerieName, contentType='episode', search_type = 'episode',
                              contentSeason = temp, contentEpisodeNumber= epis ))

    tmdb.set_infoLabels(itemlist)

    try:
        pagination = data_json['data']['pagination']

        if pagination['next_page_url']:
            itemlist.append(item.clone (action = 'episodios`', title = 'Siguientes ...',
                                        contentType='season', contentSeason=item.contentSeason, page = page + 1, text_color='coral'))  
    except:
        pass

    return sorted(itemlist, key=lambda x: x.title)


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Latino': 'Lat', 'Castellano': 'Esp', 'Ingles': 'Vo', 'Subtitulado': 'Vose', 'Latino/Inglés': 'Vose', 'Japones': 'Jap', 'Japonés - Subtítulos Latino': 'Jap/Sub Lat'}

    _id = item._id

    data = do_downloadapi('links', '', '', '', _id, '', '')

    if not data: return itemlist

    jdata = json.loads(data)

    if not jdata: return itemlist

    ses = 0

    # ~ Embeds
    try:
        content = jdata['data']['embeds']
    except:
        content = ''

    for video in content:
        ses += 1

        other = ''

        url = video['url']

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if '/vimeos.' in url:
            servidor = 'zures'
            other = 'Vimeos'

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        url = servertools.normalize_url(servidor, url)

        if servidor == 'various': other = servertools.corregir_other(url)

        qlty = video['quality']

        lng = video['lang']

        quality_num = puntuar_calidad(qlty)

        itemlist.append(Item (channel = item.channel, action='play', title='', server=servidor, url=url,
                              quality = qlty, language = IDIOMAS.get(lng, lng), quality_num = quality_num, other=other ))

    # ~ Downloads
    try:
        content = jdata['data']['downloads']
    except:
        content = ''

    for video in content:
        ses += 1

        other = ''

        try:
            url = video['url']
            qlty = video['quality']
        except:
            url = scrapertools.find_single_match(str(content), "'url':.*?'(.*?)'")
            qlty = scrapertools.find_single_match(str(content), "'quality':.*?'(.*?)'")

        if not url: continue

        elif '/1fichier.' in url: continue
        elif '.fireload.' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if '/vimeos.' in url:
            servidor = 'zures'
            other = 'Vimeos'

        if servidor == 'various': other = servertools.corregir_other(url)

        quality_num = puntuar_calidad(qlty)

        itemlist.append(Item (channel = item.channel, action='play', title='', server=servidor, url=url,
                              quality = qlty, language = IDIOMAS.get(lng, lng), quality_num = quality_num, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def puntuar_calidad(txt):
    orden = ['CAMRip', 'Dual 720p', '720', 'HDTV', 'BDRip', 'DVDRip', 'WEBRip', 'Full HD', 'Dual 1080p Ligero', 'Dual 1080p', 'WEB-DL 1080p', '1080', 'HD', 'WEBRip 1080p', 'REMUX 1080p' , 'MicroHD 1080p', 'WEB-DL 4k HDR', 'WEB-DL 4k DV HDR', '4K']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def get_lang(lang_ids):
    langs = []

    lang_list = {"58651": "Lat",
                 "58652": "Ing",
                 "58653": "Esp",
                 "58654": "Jap",
                 "58655": "Vose"}

    for lang_id in lang_ids:
        langs.append(lang_list[str(lang_id)])

    if not langs: langs.append('Lat')
 
    langs = ', '.join(langs)

    return langs


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if url == 'https://la.movie/embed.html?v=1':
        return 'Contenido [COLOR goldenrod]Aún No Disponible[/COLOR]'

    if item.server == 'directo':
        if url == host + 'embed.html?v=1': url = ''

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.busca = 'search'
        item.terms = texto.replace(" ", "+").lower()
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

