# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ pelis No hay 24/12/2023


host = 'https://enn.ennovelas-tv.com/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://c.ennovelas-tv.com/', 'https://d.ennovelas-tv.com/', 'https://e.ennovelas-tv.com/',
             'https://f.ennovelas-tv.com/', 'https://g.ennovelas-tv.com/', 'https://h.ennovelas-tv.com/',
             'https://i.ennovelas-tv.com/', 'https://j.ennovelas-tv.com/', 'https://k.ennovelas-tv.com/',
             'https://novelashd.ennovelas-tv.com/', 'https://novelass.ennovelas-tv.com/']


domain = config.get_setting('dominio', 'ennovelastv', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'ennovelastv')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'ennovelastv')


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    raise_weberror = True
    if '/years/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    if not data:
        if not '/search/' in url:
            if not '/temp/ajax/iframe.php?id=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'ennovelastv', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_ennovelastv', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='ennovelastv', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_ennovelastv', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'ennovelastv', thumbnail=config.get_thumb('ennovelastv') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_epis', url = host + 'episodes11/', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimas series', action = 'list_last', url = host, search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action='anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action='paises', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
       ('action', 'Acción'),
       ('aventura', 'Aventura'),
       ('comedy', 'Comedia'),
       ('crime', 'Crimen'),
       ('drama', 'Drama'),
       ('mistery', 'Misterio'),
       ('music', 'Música'),
       ('romance', 'Romance'),
       ('thriller', 'Thriller'),
       ('terror', 'Terror'),
       ('western', 'Western')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title=tit, url = host + 'genre/' + opc + '/', action = 'list_all', text_color = 'hotpink' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1989, -1):
        url = host + 'years/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = 'hotpink' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    text_color = 'hotpink'

    itemlist.append(item.clone( title = 'América', action = 'list_all', url = host + 'country/united-states/', text_color= text_color))
    itemlist.append(item.clone( title = 'Argentina', action = 'list_all', url = host + 'country/argentina/', text_color=text_color ))
    itemlist.append(item.clone( title = 'Brasil', action = 'list_all', url = host + 'country/brasil/', text_color=text_color ))
    itemlist.append(item.clone( title = 'Chile', action = 'list_all', url = host + 'country/chile/', text_color= text_color))
    itemlist.append(item.clone( title = 'Colombia', action = 'list_all', url = host + 'country/colombia/', text_color=text_color ))
    itemlist.append(item.clone( title = 'México', action = 'list_all', url = host + 'country/mexico/', text_color=text_color ))
    itemlist.append(item.clone( title = 'Perú', action = 'list_all', url = host + 'country/peru/', text_color=text_color ))
    itemlist.append(item.clone( title = 'Reino unido', action = 'list_all', url = host + 'country/reino-unido/', text_color=text_color ))
    itemlist.append(item.clone( title = 'Turquía', action = 'list_all', url = host + 'country/turkey/', text_color=text_color ))
    itemlist.append(item.clone( title = 'Venezuela', action = 'list_all', url = host + 'country/venezuela/', text_color=text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if '/movies/' in url: continue

        year = scrapertools.find_single_match(match, '(\d{4})')
        if not year: year = '-'
        else:
           title = title.replace(year, '').strip()

        if '/years/' in item.url: year = scrapertools.find_single_match(item.url, "/years/(.*?)/")

        thumb = scrapertools.find_single_match(match, 'data-img="(.*?)"')

        title = title.replace('&#8211;', "").strip()

        SerieName = title

        if " (" in title: SerieName = title.split(" (")[0]
        elif "(En Espanol)" in title: SerieName = title.split("(En Espanol)")[0]
        elif "En Español" in title: SerieName = title.split("En Español")[0]
        elif "[Español Subtitulado]" in title: SerieName = title.split("[Español Subtitulado]")[0]
        elif "[SUB Espanol]" in title: SerieName = title.split("[SUB Espanol]")[0]

        if " Temporada" in title: SerieName = title.split(" Temporada")[0]
        elif " Capitulos" in title: SerieName = title.split(" Capitulos")[0]
        elif " Capítulos" in title: SerieName = title.split(" Capítulos")[0]
        elif " Capitulo" in title: SerieName = title.split(" Capitulo")[0]
        elif " Capítulo" in title: SerieName = title.split(" Capítulo")[0]

        SerieName = SerieName.strip()

        if '/search/' in item.url:
            cap = False
            if 'Capitulos' in title or 'Capítulos' in title: pass
            elif 'Capitulo' in title or 'Capítulo' in title: cap = True

            if cap:
                season = scrapertools.find_single_match(title, 'Temporada(.*?)Capítulo').strip()
                if not season: season = scrapertools.find_single_match(title, 'Temporada(.*?)Capitulo').strip()
                if not season: season = 1

                epis = scrapertools.find_single_match(match, '<span>Cap.*?<span>(.*?)</span>')
                if not epis: epis = 1

                title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

                title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

                itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, infoLabels={'year': year},
                                            contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))
                continue

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<span class="current">.*?a href="(.*?)"')
        if not next_page: next_page = scrapertools.find_single_match(data, "<div class='pagination'>.*?<span class='current'>.*?a href='(.*?)'")

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def list_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Últimos Capitulos<(.*?)>Últimos Series<')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if '/movies/' in url: continue

        thumb = scrapertools.find_single_match(match, 'data-img="(.*?)"')

        season = scrapertools.find_single_match(match, '>Temporada(.*?)</span>').strip()
        if not season: season = 1

        epis = scrapertools.find_single_match(match, '<span>Cap.*?<span>(.*?)</span>')
        if not epis: epis = 1

        title = title.replace('&#8211;', "").strip()

        SerieName = title

        if " (" in title: SerieName = title.split(" (")[0]
        elif "(En Espanol)" in title: SerieName = title.split("(En Espanol)")[0]
        elif "En Español" in title: SerieName = title.split("En Español")[0]
        elif "[Español Subtitulado]" in title: SerieName = title.split("[Español Subtitulado]")[0]
        elif "[SUB Espanol]" in title: SerieName = title.split("[SUB Espanol]")[0]

        if " Temporada" in title: SerieName = title.split(" Temporada")[0]
        elif " Capitulos" in title: SerieName = title.split(" Capitulos")[0]
        elif " Capítulos" in title: SerieName = title.split(" Capítulos")[0]
        elif " Capitulo" in title: SerieName = title.split(" Capitulo")[0]
        elif " Capítulo" in title: SerieName = title.split(" Capítulo")[0]

        SerieName = SerieName.strip()

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, infoLabels={'year': '-'},
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Últimos Series<(.*?)>Últimos Peliculas<')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if '/movies/' in url: continue

        thumb = scrapertools.find_single_match(match, 'data-img="(.*?)"')

        SerieName = title

        if " (" in title: SerieName = title.split(" (")[0]
        elif "(En Espanol)" in title: SerieName = title.split("(En Espanol)")[0]
        elif "En Español" in title: SerieName = title.split("En Español")[0]
        elif "[Español Subtitulado]" in title: SerieName = title.split("[Español Subtitulado]")[0]
        elif "[SUB Espanol]" in title: SerieName = title.split("[SUB Espanol]")[0]

        if " Temporada" in title: SerieName = title.split(" Temporada")[0]
        elif " Capitulos" in title: SerieName = title.split(" Capitulos")[0]
        elif " Capítulos" in title: SerieName = title.split(" Capítulos")[0]
        elif " Capitulo" in title: SerieName = title.split(" Capitulo")[0]
        elif " Capítulo" in title: SerieName = title.split(" Capítulo")[0]

        SerieName = SerieName.strip()

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('data-season=.*?>Season(.*?)</li>', re.DOTALL).findall(data)

    if not matches:
        bloque =  scrapertools.find_single_match(data, '>Temporada & Capitulos<(.*?)<footer>')

        if bloque:
            epis = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)
            if not epis: epis = re.compile('<a class="epNum"(.*?)</a>', re.DOTALL).findall(bloque)

            if epis:
                if config.get_setting('channels_seasons', default=True):
                    platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]Sin temporadas[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = 1
                itemlist = episodios(item)
                return itemlist

        return itemlist

    for numtempo in matches:
        numtempo = numtempo.strip()

        title = 'Temporada ' + numtempo

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = numtempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<ul class="eplist">(.*?)</ul>')

    matches = re.compile('<a class="epNum"(.*?)</a>', re.DOTALL).findall(bloque)

    num_matches = len(matches)

    if item.page == 0 and item.perpage == 50:
        sum_parts = num_matches

        try: tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:

            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('EnNovelasTv', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        epis = scrapertools.find_single_match(match, '<span>(.*?)</span>')
        if not epis: epis = 1

        title = title.replace('EP ', '[COLOR goldenrod]Epis. [/COLOR]').replace('Ep ','[COLOR goldenrod]Epis. [/COLOR]')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,  contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    lang = 'Lat'

    data = do_downloadpage(item.url)

    ses = 0

    # ~ embeds
    matches = scrapertools.find_multiple_matches(data, 'data-title="Opción.*?data-src="(.*?)"')
    if not matches: matches = scrapertools.find_multiple_matches(data, '<iframe.*?data-src="(.*?)"')

    for url in matches:
        ses += 1

        url = url.strip()

        if '/likessb.' in url: continue
        elif '/lylxan.' in url: continue
        elif '/live.demand.' in url: continue

        if url.startswith('//'): url = 'https:' + url

        if 'api.mycdn.moe/uqlink.php?id=' in url: url = url.replace('api.mycdn.moe/uqlink.php?id=', 'uqload.com/embed-')

        elif 'api.mycdn.moe/dourl.php?id=' in url: url = url.replace('api.mycdn.moe/dourl.php?id=', 'dood.to/e/')

        elif 'api.mycdn.moe/dl/?uptobox=' in url: url = url.replace('api.mycdn.moe/dl/?uptobox=', 'uptobox.com/')

        elif url.startswith('http://vidmoly/'): url = url.replace('http://vidmoly/w/', 'https://vidmoly/embed-').replace('http://vidmoly/', 'https://vidmoly/')

        elif url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
        elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

        url = url.replace('&amp;', '&')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item( channel=item.channel, action = 'play', server = servidor, url = url, language = lang, other = other.capitalize() ))

    # ~ links
    data = do_downloadpage(item.url + '?do=watch')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    values = scrapertools.find_multiple_matches(data, '<form method="post".*?action="(.*?)".*?<input type="hidden".*?name="(.*?)".*?value="(.*?)"')

    for link, type, value in values:
        ses += 1

        if not link: continue

        if type == 'watch': post = {'watch': str(value), 'submit': ''}
        else: post = {'download': str(value), 'submit': ''}

        data1 = do_downloadpage(link, post = post, headers = {'Referer': item.url} )

        matches = scrapertools.find_multiple_matches(data1, "<iframe.*?src='(.*?)'")
        if not matches: matches = scrapertools.find_multiple_matches(data1, '<iframe.*?src="(.*?)"')

        if not matches: matches = scrapertools.find_multiple_matches(data1, "<IFRAME.*?SRC='(.*?)'")
        if not matches: matches = scrapertools.find_multiple_matches(data1, '<IFRAME.*?SRC="(.*?)"')

        if not matches: matches = scrapertools.find_multiple_matches(data1, '<td>Server.*?href="(.*?)"')

        for url in matches:
            if '/wp-admin/' in url: continue

            elif '/lylxan.' in url: continue
            elif '/live.demand.' in url: continue

            if url.startswith('//'): url = 'https:' + url

            if 'api.mycdn.moe/uqlink.php?id=' in url: url = url.replace('api.mycdn.moe/uqlink.php?id=', 'uqload.com/embed-')

            elif 'api.mycdn.moe/dourl.php?id=' in url: url = url.replace('api.mycdn.moe/dourl.php?id=', 'dood.to/e/')

            elif 'api.mycdn.moe/dl/?uptobox=' in url: url = url.replace('api.mycdn.moe/dl/?uptobox=', 'uptobox.com/')

            elif url.startswith('http://vidmoly/'): url = url.replace('http://vidmoly/w/', 'https://vidmoly/embed-').replace('http://vidmoly/', 'https://vidmoly/')

            elif url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
            elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
            elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
            elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

            url = url.replace('&amp;', '&')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            if type == 'download':
                if other: other = other + ' D'
                else: other = 'D'

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, other = other ))

    t_link = scrapertools.find_single_match(data, 'var vo_theme_dir = "(.*?)"')
    id_link = scrapertools.find_single_match(data, 'vo_postID = "(.*?)"')

    if t_link and id_link:
        i = 0

        while i <= 5:
           data2 = do_downloadpage(t_link + '/temp/ajax/iframe.php?id=' + id_link + '&video=' + str(i), headers = {'Referer': item.url, 'x-requested-with': 'XMLHttpRequest'} )

           data2 = data2.strip()

           if not data2: break

           ses += 1

           u_link = scrapertools.find_single_match(data2, '<iframe.*?src="(.*?)"')
           if not u_link: u_link = scrapertools.find_single_match(data2, '<IFRAME.*?SRC="(.*?)"')

           if u_link.startswith('//'): u_link = 'https:' + u_link

           if '/wp-admin/' in u_link: u_link = ''

           elif '/lylxan.' in u_link: u_link = ''
           elif '/live.demand.' in u_link: u_link = ''

           if u_link:
               if u_link.startswith('https://sr.ennovelas.net/'): u_link = u_link.replace('/sr.ennovelas.net/', '/waaw.to/')
               elif u_link.startswith('https://sr.ennovelas.watch/'): u_link = u_link.replace('/sr.ennovelas.watch/', '/waaw.to/')
               elif u_link.startswith('https://video.ennovelas.net/'): u_link = u_link.replace('/video.ennovelas.net/', '/waaw.to/')
               elif u_link.startswith('https://reproductor.telenovelas-turcas.com.es/'): u_link = u_link.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
               elif u_link.startswith('https://novelas360.cyou/player/'): u_link = u_link.replace('/novelas360.cyou/player/', '/waaw.to/')
               elif u_link.startswith('https://novelas360.cyou/'): u_link = u_link.replace('/novelas360.cyou/', '/waaw.to/')

               elif u_link.startswith('https://vk.com/'): u_link = u_link.replace('&amp;', '&')

               u_link = u_link.replace('&amp;', '&')

               servidor = servertools.get_server_from_url(u_link)
               servidor = servertools.corregir_servidor(servidor)

               u_link = servertools.normalize_url(servidor, u_link)

               other = ''
               if servidor == 'various': other = servertools.corregir_other(u_link)

               itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = u_link, server = servidor, language = lang, other = other ))

           i += 1

    # ~ Downloads
    data = do_downloadpage(item.url + '?do=downloads', headers = {'Referer': item.url, 'x-requested-with': 'XMLHttpRequest'})

    matches = scrapertools.find_multiple_matches(data, '<td>Server.*?href="(.*?)"')

    for url in matches:
        ses += 1

        if '/wp-admin/' in url: continue

        elif '/lylxan.' in url: continue
        elif '/live.demand.' in url: continue

        if url.startswith('//'): url = 'https:' + url

        if url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
        elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

        url = url.replace('&amp;', '&')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)

        if other: other = other + ' d'
        else: other = 'd'

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, other = other ))

    # ~ Otros
    link_srv = scrapertools.find_single_match(data, '<div id="btnServers">.*?href="(.*?)"')

    if link_srv:
        data = do_downloadpage(link_srv, headers = {'Referer': host})

        enlaces1 = scrapertools.find_multiple_matches(data, "<iframe.*?src='(.*?)'")
        enlaces2 = scrapertools.find_multiple_matches(data, '<iframe.*?src="(.*?)"')

        enlaces3 = scrapertools.find_multiple_matches(data, "<IFRAME.*?SRC='(.*?)'")
        enlaces4 = scrapertools.find_multiple_matches(data, '<IFRAME.*?SRC="(.*?)"')

        enlaces = enlaces1 + enlaces2 + enlaces3 + enlaces4

        for enlace in enlaces:
            ses += 1

            if '/wp-admin/' in enlace: continue

            elif '/lylxan.' in enlace: continue
            elif '/live.demand.' in enlace: continue

            if enlace.startswith('//'): enlace = 'https:' + enlace

            if '/e//' in enlace: enlace = enlace.replace('/e//', '/e/')
            elif '/www.ok.ru/videoembed/video/' in enlace: enlace = enlace.replace('/www.ok.ru/videoembed/video/', '/ok.ru/videoembed/')
            elif '/www.doods.pro/' in enlace: enlace = enlace.replace('/www.doods.pro/', '/doods.pro/')
            elif ':2096/' in enlace: enlace = enlace.replace(':2096/', '/')

            if enlace.startswith('https://sr.ennovelas.net/'): enlace = enlace.replace('/sr.ennovelas.net/', '/waaw.to/')
            elif enlace.startswith('https://sr.ennovelas.watch/'): enlace = enlace.replace('/sr.ennovelas.watch/', '/waaw.to/')
            elif enlace.startswith('https://video.ennovelas.net/'): enlace = enlace.replace('/video.ennovelas.net/', '/waaw.to/')
            elif enlace.startswith('https://reproductor.telenovelas-turcas.com.es/'): enlace = enlace.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
            elif enlace.startswith('https://novelas360.cyou/player/'): enlace = enlace.replace('/novelas360.cyou/player/', '/waaw.to/')
            elif enlace.startswith('https://novelas360.cyou/'): enlace = enlace.replace('/novelas360.cyou/', '/waaw.to/')

            enlace = enlace.replace('&amp;', '&')

            servidor = servertools.get_server_from_url(enlace)
            servidor = servertools.corregir_servidor(servidor)

            enlace = servertools.normalize_url(servidor, enlace)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(enlace)

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = enlace, server = servidor, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone( url=url, server=servidor ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + 'search/' + texto.replace(" ", "+") + '/'
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

