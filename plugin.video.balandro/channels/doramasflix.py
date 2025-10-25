# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True


from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, jsontools, scrapertools, servertools, tmdb

from core.jsontools import json


host = 'https://doramasflix.co/'


api = 'https://sv7.fluxcedene.net/graphql'


perpage = 20


def do_downloadpage(query):
    post = json.dumps(query)

    headers = {'Referer': host, 'Content-Type': 'application/json'}

    resp = httptools.downloadpage(api, headers=headers, post=post)

    try: return json.loads(resp.data)
    except: return ''


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', _type = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Doramas', action = 'mainlist_doramas', text_color = 'firebrick' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', _type = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host, search_type = 'movie' ))

    # ~ itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))

    # ~ itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    # ~ itemlist.append(item.clone( title = 'Por tema', action = 'temas', search_type = 'movie' ))

    # ~ itemlist.append(item.clone( title = 'Por productora', action = 'productoras', search_type = 'movie', text_color = 'moccasin' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', _type = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'tvshows/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, _type = 'lasts', search_type = 'tvshow', text_color = 'cyan' ))

    # ~ itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Por tema', action = 'temas', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Por productora', action = 'productoras', search_type = 'tvshow', text_color = 'moccasin' ))

    return itemlist


def mainlist_doramas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', _type = 'search', search_type = 'tvshow', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'tvshows/', group = 'doramas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, _type = 'lasts', group = 'doramas', search_type = 'tvshow', text_color = 'cyan' ))

    # ~ itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', group = 'doramas', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'doramas', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Por tema', action = 'temas', group = 'doramas', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Por productora', action = 'productoras', group = 'doramas', search_type = 'tvshow', text_color = 'moccasin' ))

    return itemlist


def last_epis(item):
    logger.info()

    perlast = 180
    if item.group == 'doramas': perlast = 65

    if config.get_setting('channels_charges', default=True):
        platformtools.dialog_notification('DoramasFlix', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')

    query = {
            "operationName":"premiereEpisodes",
            "variables":{"limit": perlast},
            "query": "query premiereEpisodes($limit: Float!) {\n"
            +" premiereEpisodes(limit: $limit) {\n"
            +" _id\n"
            +" air_date\n"
            +" serie_name\n"
            +" serie_name_es\n"
            +" slug\n"
            +" still_path\n"
            +" season_number\n"
            +" episode_number\n"
            +" still_image\n"
            +" __typename\n"
            +" }\n"
            +"}"
            }

    return list_query(item, query, 1)


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       text_color = 'hotpink'
       if item.group == 'doramas': text_color = 'firebrick'

    query = {
            "variables": {},
            "query": "{\n"
            +" listGenres(filter: {platform: \"doramasgo\"}, sort: NAME_DESC) {\n"
            +" name\n"
            +" _id\n"
            +" slug\n"
            +" __typename\n"
            +" }\n"
            +"}\n"
            }

    jdata = do_downloadpage(query)

    if not jdata: return itemlist

    try:
       for genre in jdata['data']['listGenres']:
           itemlist.append(item.clone( title = genre['name'], slug = genre['slug'], action = 'list_all', text_color = text_color ))
    except:
       return itemlist

    return sorted(itemlist, key=(lambda x: x.title))


def temas(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       text_color = 'hotpink'
       if item.group == 'doramas': text_color = 'firebrick'

    query = {
            "variables": {},
            "query": " {\n"
            +" listLabels(filter: {platform: \"doramasgo\"}, sort: NAME_DESC) {\n"
            +" name\n"
            +" slug\n"
            +" platforms {\n"
            +" platform\n"
            +" number\n"
            +" image_default\n"
            +" image_tmdb\n"
            +" image_custom\n"
            +" __typename\n"
            +" }\n"
            +" __typename\n"
            +" }\n"
            +"}",
            "filter_key": "labelId",
            "filter_val": "_id"
            }

    jdata = do_downloadpage(query)

    if not jdata: return itemlist

    try:
       for label in jdata['data']['listLabels']:
           title = label['name'].strip()

           if title == '+18':
               if config.get_setting('descartar_xxx', default=False): continue

           itemlist.append(item.clone( title = title.capitalize(), label_id = label['slug'], action = 'list_all', text_color = text_color ))
    except:
       return itemlist

    return sorted(itemlist, key=(lambda x: x.title))


def productoras(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       text_color = 'hotpink'
       if item.group == 'doramas': text_color = 'firebrick'

    query = {
            "variables": {},
            "query": "{\n"
            +" listNetworks(filter: {platform: \"doramasgo\"}, sort: NAME_DESC) {\n"
            +" name\n"
            +" _id\n"
            +" slug\n"
            +" __typename\n"
            +" }\n"
            +"}\n"
            }

    jdata = do_downloadpage(query)

    if not jdata: return itemlist

    try:
       for network in jdata['data']['listNetworks']:
           title = network['name'].strip()

           itemlist.append(item.clone( title = title, net_slug = network['slug'], action = 'list_all', text_color = text_color ))
    except:
       return itemlist

    return sorted(itemlist, key=(lambda x: x.title))


def idiomas(item):
    logger.info()
    itemlist = []

    languages = get_idiomas()

    for lang in languages:
        itemlist.append(item.clone( title = lang['name'], code_flix = lang['code_flix'], action = 'list_all', text_color = 'moccasin' ))

    return sorted(itemlist, key=(lambda x: x.title))


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    filters = {}

    if item.slug: filters["genres"] = [{'slug': item.slug}]

    elif item.net_slug: filters["networks"] = [{'slug': item.net_slug}]

    elif item.label_id: filters["labelId"] = str(item.label_id)

    if item.code_flix: filters["bylanguages"] = [str(item.code_flix)]

    if item.search_type == 'movie':
        query = {
                "operationName":"PaginationMovie",
                "variables": {"page": item.page, "limit": perpage, "filter": filters},
                "query": "query PaginationMovie($sort: SortMovie, $limit: Int, $filter: FilterMoviesInput, $page: Int) {\n"
                +" paginationMovie(sort: $sort, limit: $limit, filter: $filter, page: $page) {\n"
                +" hasNextPage\n"
                +" items {\n"
                +" _id\n"
                +" name\n"
                +" name_es\n"
                +" slug\n"
                +" languages\n"
                +" poster_path\n"
                +" poster\n"
                +" backdrop_path\n"
                +" backdrop\n"
                +" __typename\n"
                +" }\n"
                +" __typename\n"
                +" }\n"
                +"}"
                }

    if item.search_type == 'tvshow':
        filters["isTVShow"] = False if item.group == 'doramas' else True

        query = {
                "operationName":"PaginationDorama",
                "variables":{"page": item.page, "limit": perpage, "filter": filters},
                "query": "query PaginationDorama($sort: SortDorama, $limit: Int, $filter: FilterDoramasInput, $page: Int) {\n"
                +" paginationDorama(sort: $sort, limit: $limit, filter: $filter, page: $page) {\n"
                +" hasNextPage\n"
                +" items {\n"
                +" _id\n"
                +" name\n"
                +" name_es\n"
                +" slug\n"
                +" languages\n"
                +" isTVShow\n"
                +" poster_path\n"
                +" poster\n"
                +" backdrop_path\n"
                +" backdrop\n"
                +" __typename\n"
                +" }\n"
                +" __typename\n"
                +" }\n"
                +"}"
                }

    return list_query(item, query, item.page)


def seasons(item):
    logger.info()
    itemlist = []

    thumb = 'https://image.tmdb.org/t/p/original{}'

    season = 1 if not item.contentSeason else item.contentSeason

    query = {"operationName": "detailSeasonExtra",
             "variables":{"slug": item.slug, "season_number": season},
             "query":"query detailSeasonExtra($slug: String!, $season_number: Int!) {\n"
             +" listSeasons(sort: NUMBER_ASC, filter: {serie_slug: $slug}) {\n"
             +" slug\n"
             +" season_number\n"
             +" poster_path\n"
             +" serie_backdrop_path\n"
             +" air_date\n"
             +" serie_name\n"
             +" trailer\n"
             +" backdrop\n"
             +" overview\n"
             +" _id\n"
             +" name\n"
             +" emision\n"
             +" pause\n"
             +" uploading\n"
             +" commingSoon\n"
             +" __typename\n"
             +" }\n"
             +" listEpisodes(\n"
			 +" sort: NUMBER_ASC\n"
             +" filter: {serie_slug: $slug, season_number: $season_number}\n"
             +" ) {\n"
             +" _id\n"
             +" name\n"
             +" slug\n"
             +" serie_name\n"
             +" serie_id\n"
             +" still_path\n"
             +" air_date\n"
             +" season_number\n"
             +" episode_number\n"
             +" languages\n"
             +" backdrop\n"
             +" __typename\n"
             +" }\n"
             +"}"}

    jdata = do_downloadpage(query)

    if not jdata: return itemlist

    # ~ Hay series con temporadas duplicadas
    clean_seasons(jdata['data']['listSeasons'])

    if not item.contentSeason and len(jdata['data']['listSeasons']) > 1:
        for season in jdata['data']['listSeasons']:
            item_args = {}

            item_args['channel'] = item.channel
            item_args['group'] = item.group_type
            item_args['search_type'] = item.search_type

            item_args['contentType'] = 'tvshow'
            item_args['contentSerieName'] = season['name']
            item_args['slug'] = season['slug']
            item_args['title'] = season['season_number']
            item_args['action'] = 'seasons'
            img_path = season['poster_path']

            item_args['thumbnail'] = thumb.format(img_path)

            item.args['contentSeason'] = season['season_number']

            new_item = Item(**item_args)

            tmdb.set_infoLabels_item(new_item)

            new_item.infoLabels['year'] = '-'
            new_item.infoLabels['plot'] = season['overview']

            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist)

        return itemlist

    infoLabels = item.infoLabels

    for episode in jdata['data']['listEpisodes']:
        infoLabels['season'] = episode['season_number']
        infoLabels['episode'] = episode['episode_number']

        title = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item.contentSerieName)

        url = episode['_id']

        thumb = thumb.format(episode['still_path'])

        itemlist.append(Item (channel = item.channel, action='findvideos', title=title, url=url, thumbnail=thumb, group=item.group,
                              contentSerieName=item.contentSerieName, contentType='episode',
							  contentSeason=infoLabels['season'], contentEpisodeNumber=infoLabels['episode'],
                              search_type = item.search_type, infoLabels=infoLabels))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def clean_seasons(seasons):
    season_number = set()

    for i in seasons[:]:
        if i['season_number'] in season_number:
            seasons.remove(i)
        else:
            season_number.add(i['season_number'])


def findvideos(item):
    logger.info()
    itemlist = []

    videos = []

    query = {
            "operationName":"listProblemsItem",
            "variables":{"problem_id" :item.url},
            "query": "query listProblemsItem($problem_id: ID!) {\n"
            +" listProblems(\n"
            +" filter: {problem_id: $problem_id}\n"
            +" ) {\n"
            +" server{\n"
            +" link\n"
            +" lang\n"
            +" }\n"
            +" }\n"
            +"}"
            }

    jdata = do_downloadpage(query)

    if not jdata: return itemlist

    ses = 0

    try:
       videos = jdata['data']['listProblems']
    except:
       return itemlist

    if not videos: return itemlist

    for video in videos:
        if str(video) == "{'server': None}": continue

        ses += 1

        lang = scrapertools.find_single_match(str(video), "'lang': '(.*?)'")
        url = scrapertools.find_single_match(str(video), "'link': '(.*?)'")

        if '/pelisplus.' in url: continue
        elif '/fplayer.' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        if not servidor == 'directo':
            lng = get_lang(lang)

            lang = 'Vose'

            if lng == 'subtitulado': pass
            elif lng == 'Castellano':
                lang = 'Esp'
                lng = ''
            elif lng == 'Latino':
                lang = 'Lat'
                lng = ''
            else: lang = 'Vo'

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                  language = lang, quality = 'HD', other = other, age = lng ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def list_query(item, query, page):
    logger.info()
    itemlist = []

    thumb = 'https://image.tmdb.org/t/p/original{}'

    jdata = do_downloadpage(query)

    if not jdata: return itemlist

    pages = []

    try:
       if item._type == 'search':
           datos = jdata['data']['searchDorama']
           datos.extend(jdata['data']['searchMovie'])
       elif item._type == 'lasts':
           datos = jdata['data']['premiereEpisodes']
       else:
           if item.search_type == 'movie':
               datos = jdata['data']['paginationMovie']['items']
               pages = jdata['data']['paginationMovie']['hasNextPage']
           elif item.search_type == 'tvshow':
               datos = jdata['data']['paginationDorama']['items']
               pages = jdata['data']['paginationDorama']['hasNextPage']
    except:
       return itemlist

    if not datos: return itemlist

    for match in datos:
        item_args = {}

        item_args['channel'] = item.channel
        item_args['url'] = match['_id']
        item_args['search_type'] = item.search_type

        if match.get('languages',''):
            item_args['language'] = get_languages(match['languages'])

        if item._type == 'lasts':
            item_args['contentType'] = 'episode'
            item_args['contentSerieName'] = match['serie_name']
            item_args['action'] = 'findvideos'
            item_args['title'] = "{}x{} {}".format(match['season_number'], match['episode_number'], match['serie_name'])
            img_path = match['still_path']
        else:
           if item.search_type == 'movie' or "'__typename': 'Movie'" in match:
               item_args['contentType'] = 'movie'
               item_args['contentTitle'] = match['name']
               item_args['title'] = match['name']
               item_args['action'] = 'findvideos'
               img_path = match['poster_path'] if match.get('poster_path', '') else match['backdrop_path']

           elif item.search_type == 'tvshow' or not  "'__typename': 'Movie'" in match:
               item_args['contentType'] = 'tvshow'
               item_args['contentSerieName'] = match['name']
               item_args['slug'] = match['slug']
               item_args['title'] = match['name']
               item_args['action'] = 'seasons'
               img_path = match['poster_path'] if match.get('poster_path', '') else match['backdrop_path']

        item_args['thumbnail'] = thumb.format(img_path)

        new_item = Item(**item_args)

        tmdb.set_infoLabels_item(new_item)

        if item._type == 'lasts':
            new_item.infoLabels['season'] = match['season_number']
            new_item.infoLabels['episode'] = match['episode_number']

        new_item.infoLabels['year'] = '-'

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    if pages:
        if page:
            page += 1

            itemlist.append(item.clone( action="list_all", title='Siguientes ...', page=page, text_color='coral' ))

    return itemlist


def get_idiomas():
    logger.info()

    idiomas = [
              {"code_flix": "37", "name": "Castellano"},
              {"code_flix": "38", "name": "Latino" },
              {"code_flix": "1327", "name": "Portugués" },
              {"code_flix": "192", "name": "Subtitulado" },
              {"code_flix": "36", "name": "Sub Inglés" },
              {"code_flix": "13109", "name": "Coreano" },
              {"code_flix": "13113", "name": "Filipino" },
              {"code_flix": "13114", "name": "Indonés" },
              {"code_flix": "13110", "name": "Japonés" },
              {"code_flix": "13111", "name": "Mandarín" },
              {"code_flix": "13112", "name": "Tailandés" },
              {"code_flix": "343422", "name": "Vietnamita" }
              ]

    return idiomas


def get_languages(codes):
    logger.info()

    langs = []

    languages = get_idiomas()

    for code in codes:
        try:
            if code == 'en': langs.append('subtitulado')
            else:
               if PY3:
                   langs.append(next(filter(lambda lang: lang['code_flix'] == code, languages))['name'])
               else:
                   langs.append(filter(lambda lang: lang['code_flix'] == code, languages)[0]['name'])
        except:
            pass

    return langs


def get_lang(code):
    logger.info()

    languages = get_idiomas()

    if code == 'en': return 'subtitulado'

    if PY3:
        return next(filter(lambda lang: lang['code_flix'] == code, languages))['name']
    else:
        return filter(lambda lang: lang['code_flix'] == code, languages)[0]['name']


def search(item, texto):
    logger.info()
    try:
       if not item._type: item._type = 'search'

       query = {
               "operationName": "searchAll",
               "variables": {"input": texto},
               "query": "query searchAll($input: String!) {\n"
               +" searchDorama(input: $input, limit: 5) {\n"
               +" _id\n"
               +" slug\n"
               +" languages\n"
               +" name\n"
               +" name_es\n"
               +" poster_path\n"
               +" rating\n"
               +" poster\n"
               +" episode_time\n"
               +" __typename\n"
               +" }\n"
               +" searchMovie(input: $input, limit: 5) {\n"
               +" _id\n"
               +" name\n"
               +" name_es\n"
               +" languages\n"
               +" slug\n"
               +" runtime\n"
               +" rating\n"
               +" poster_path\n"
               +" poster\n"
               +" __typename\n"
               +" }\n"
               +"}"
               }

       return list_query(item, query, 1)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
