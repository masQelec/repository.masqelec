# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://zeroanime20.wordpress.com/'


perpage = 20


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_oll', url = host, scroll = 1,
                                post = {"action": "infinite_scroll", "page": 1, "order": "DESC", "query_args[comments_per_page]": "20"}, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'en-emision/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Especiales, ovas y películas ', action = 'list_all', url = host + 'ovas-especiales/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados Web', action = 'list_all', url = host + 'finalizados-web/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados BD', action = 'list_all', url = host + 'finalizados-bd/', search_type = 'tvshow' ))

    return itemlist


def list_oll(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url, item.post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('\\/', '/')

    matches = re.compile('<article id="post-(.*?)</article>').findall(data)
    if not matches: matches = re.compile('<article(.*?)</article>').findall(str(data))

    for match in matches:
        match = match.replace('=\\', '=').replace('\\"', '/"')

        url = scrapertools.find_single_match(match, '<a class="post-thumbnail".*?href="(.*?)"')
        if not url: url = scrapertools.find_single_match(str(match), '<span class="comments-link.*?<a href="(.*?)"')

        url = url.replace('#comments/', '').strip()

        title = scrapertools.find_single_match(match, '<h1 class="entry-title">.*?rel="bookmark">(.*?)</a>')
        if not title: title = scrapertools.find_single_match(str(match), '<span class="cat-links.*?</a>.*?rel="category tag/">(.*?)</a>')

        title = title.replace('-', '').strip()

        title = clean_title(title)

        if title == 'En Emision':
            title = scrapertools.find_single_match(str(match), '<span class="cat-links.*?rel="category tag/">(.*?)</a>')
            title = clean_title(title)

        if not url or not title: continue

        title = title.capitalize()

        title = title.replace('&#8211;', '').replace('/', '').strip()

        thumb = scrapertools.find_single_match(match, 'data-orig-file="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'data-large-file="(.*?)"')

        SerieName = corregir_SerieName(title)

        if ' 2nd ' in match: season = 2
        elif ' 3rd ' in match: season = 3
        elif ' 4th ' in match: season = 4
        elif ' 5th ' in match: season = 5
        elif ' 6th ' in match: season = 6
        elif ' 7th ' in match: season = 7
        elif ' 8th ' in match: season = 8
        elif ' 9th ' in match: season = 9

        elif ' S2 ' in match: season = 2
        elif ' S3 ' in match: season = 3
        elif ' S4 ' in match: season = 4
        elif ' S5 ' in match: season = 5
        elif ' S6 ' in match: season = 6
        elif ' S7 ' in match: season = 7
        elif ' S8 ' in match: season = 8
        elif ' S9 ' in match: season = 9

        elif '-s2' in match: season = 2
        elif '-s3' in match: season = 3
        elif '-s4' in match: season = 4
        elif '-s5' in match: season = 5
        elif '-s6' in match: season = 6
        elif '-s7' in match: season = 7
        elif '-s8' in match: season = 8
        elif '-s9' in match: season = 9

        else: season = 1

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        title = title.replace(' s1 ', '[COLOR tan] Temp. 1 [/COLOR]').replace(' s2 ', '[COLOR tan] Temp. 2 [/COLOR]').replace(' s3 ', '[COLOR tan] Temp. 3 [/COLOR]').replace(' s4 ', '[COLOR tan] Temp. 4 [/COLOR]').replace(' s5 ', '[COLOR tan] Temp. 5 [/COLOR]').replace(' s6 ', '[COLOR tan] Temp. 6 [/COLOR]').replace(' s7 ', '[COLOR tan] Temp. 7 [/COLOR]').replace(' s8 ', '[COLOR tan] Temp. 8 [/COLOR]').replace(' s9 ', '[COLOR tan] Temp. 9 [/COLOR]')

        if 'Episodio' in match:
            other = scrapertools.find_single_match(str(match), 'Episodio(.*?)de').strip()

            title = title + ' [COLOR goldenrod]Epis. [/COLOR]' + other

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='tvshow', contentSerieName=SerieName, contentSeason=season, infoLabels={'year':'-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<nav class="navigation posts-navigation"' in data:
            next_page = scrapertools.find_single_match(data, '<nav class="navigation posts-navigation".*?<a href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    scroll = item.scroll + 1
                    post = {"action": "infinite_scroll","page": scroll, "order": "DESC", "query_args[comments_per_page]": "20"}

                    itemlist.append(item.clone( title = 'Siguientes ...', url = host + '?infinity=scrolling', post = post, scroll = scroll,
                                    action = 'list_oll', text_color = 'coral' ))

        else:
            scroll = item.scroll + 1
            post = {"action": "infinite_scroll","page": scroll, "order": "DESC", "query_args[comments_per_page]": "20"}

            itemlist.append(item.clone( title = 'Siguientes ...', url = host + '?infinity=scrolling', post = post, scroll = scroll,
                            action = 'list_oll', text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '>Resultados de la búsqueda para' in data:
        bloque = scrapertools.find_single_match(data, '>Resultados de la búsqueda para(.*?)</section>')

        matches = re.compile('<article(.*?)</article>').findall(bloque)

    else:
        matches = re.compile('<div class="wp-block-column is-layout-flow wp-block-column-is-layout-flow"><div class="wp-block-image">(.*?)</div></div>').findall(data)

        if not matches: 
            bloque = scrapertools.find_single_match(data, '<div class="wp-block-group is-layout-grid wp-container-core-group-is-layout-dc624358 wp-block-group-is-layout-grid">(.*?)</div>')

            matches = re.compile('<figure(.*?)</figure>').findall(bloque)

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        if '>Resultados de la búsqueda para' in data:
            url = scrapertools.find_single_match(match, '<a class="post-thumbnail".*?href="(.*?)"')

            title = scrapertools.find_single_match(match, '<h1 class="entry-title">.*?rel="bookmark">(.*?)</a>')
        else:
            url = scrapertools.find_single_match(match, '<a href="(.*?)"')

            title = url.replace(host, '').replace('-web', '').replace('-bd', '').replace('-', ' ')

        if not url or not title: continue

        title = title.capitalize()

        title = title.replace('&#8211;', '').replace('/', '').strip()

        thumb = scrapertools.find_single_match(match, 'data-orig-file="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'data-large-file="(.*?)"')

        SerieName = corregir_SerieName(title)

        if ' 2nd ' in match: season = 2
        elif ' 3rd ' in match: season = 3
        elif ' 4th ' in match: season = 4
        elif ' 5th ' in match: season = 5
        elif ' 6th ' in match: season = 6
        elif ' 7th ' in match: season = 7
        elif ' 8th ' in match: season = 8
        elif ' 9th ' in match: season = 9

        elif ' S2 ' in match: season = 2
        elif ' S3 ' in match: season = 3
        elif ' S4 ' in match: season = 4
        elif ' S5 ' in match: season = 5
        elif ' S6 ' in match: season = 6
        elif ' S7 ' in match: season = 7
        elif ' S8 ' in match: season = 8
        elif ' S9 ' in match: season = 9

        elif '-s2' in match: season = 2
        elif '-s3' in match: season = 3
        elif '-s4' in match: season = 4
        elif '-s5' in match: season = 5
        elif '-s6' in match: season = 6
        elif '-s7' in match: season = 7
        elif '-s8' in match: season = 8
        elif '-s9' in match: season = 9

        else: season = 1

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        title = title.replace(' s1 ', '[COLOR tan] Temp. 1 [/COLOR]').replace(' s2 ', '[COLOR tan] Temp. 2 [/COLOR]').replace(' s3 ', '[COLOR tan] Temp. 3 [/COLOR]').replace(' s4 ', '[COLOR tan] Temp. 4 [/COLOR]').replace(' s5 ', '[COLOR tan] Temp. 5 [/COLOR]').replace(' s6 ', '[COLOR tan] Temp. 6 [/COLOR]').replace(' s7 ', '[COLOR tan] Temp. 7 [/COLOR]').replace(' s8 ', '[COLOR tan] Temp. 8 [/COLOR]').replace(' s9 ', '[COLOR tan] Temp. 9 [/COLOR]')

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='tvshow', contentSerieName=SerieName, contentSeason=season, infoLabels={'year':'-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, pagina = item.pagina, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            if '<nav class="navigation posts-navigation"' in data:
                next_page = scrapertools.find_single_match(data, '<nav class="navigation posts-navigation".*?<a href="(.*?)"')

                if next_page:
                    if '/page/' in next_page:
                        itemlist.append(item.clone( title = 'Siguientes ...', url = next_page,
                                        page = 0, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<article(.*?)</article>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<span class="posted-on"><a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h1 class="entry-title">.*?rel="bookmark">(.*?)</a>')

        if not url or not title: continue

        title = title.replace('&#8211;', '').replace('/', '').strip()

        title = title.capitalize()

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        thumb = thumb.replace('&amp;', '&').strip()

        SerieName = corregir_SerieName(title)

        if ' 2nd ' in match: season = 2
        elif ' 3rd ' in match: season = 3
        elif ' 4th ' in match: season = 4
        elif ' 5th ' in match: season = 5
        elif ' 6th ' in match: season = 6
        elif ' 7th ' in match: season = 7
        elif ' 8th ' in match: season = 8
        elif ' 9th ' in match: season = 9

        elif ' S2 ' in match: season = 2
        elif ' S3 ' in match: season = 3
        elif ' S4 ' in match: season = 4
        elif ' S5 ' in match: season = 5
        elif ' S6 ' in match: season = 6
        elif ' S7 ' in match: season = 7
        elif ' S8 ' in match: season = 8
        elif ' S9 ' in match: season = 9

        elif '-s2' in match: season = 2
        elif '-s3' in match: season = 3
        elif '-s4' in match: season = 4
        elif '-s5' in match: season = 5
        elif '-s6' in match: season = 6
        elif '-s7' in match: season = 7
        elif '-s8' in match: season = 8
        elif '-s9' in match: season = 9

        else: season = 1

        epis = scrapertools.find_single_match(title, '  (.*?)$').strip()
        if not epis: epis = scrapertools.find_single_match(title, ' – (.*?)$').strip()

        if not epis: epis = 1

        SerieName = corregir_SerieName(title)

        titulo = '[COLOR goldenrod]Epis. [/COLOR]' + str(epis) + ' ' + title.replace(' ' + str(epis), '').strip()

        titulo = titulo.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        titulo = titulo.replace(' s1 ', '[COLOR tan] Temp. 1 [/COLOR]').replace(' s2 ', '[COLOR tan] Temp. 2 [/COLOR]').replace(' s3 ', '[COLOR tan] Temp. 3 [/COLOR]').replace(' s4 ', '[COLOR tan] Temp. 4 [/COLOR]').replace(' s5 ', '[COLOR tan] Temp. 5 [/COLOR]').replace(' s6 ', '[COLOR tan] Temp. 6 [/COLOR]').replace(' s7 ', '[COLOR tan] Temp. 7 [/COLOR]').replace(' s8 ', '[COLOR tan] Temp. 8 [/COLOR]').replace(' s9 ', '[COLOR tan] Temp. 9 [/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb,
                                    contentSerieName=SerieName, contentType='episode', contentSeason=season, contentEpisodeNumber=epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<p></p>(.*?)</div></div>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<strong>Sinopsis</strong>(.*?)</script>')
    if not bloque: bloque = scrapertools.find_single_match(data, '</div></div>(.*?)</script>')

    bloque = bloque.replace('<strong>|', '<strongs>|').replace('| </strong>', '<strongs>|').strip()

    matches = re.compile('<strongs>.*?<a href="(.*?)"', re.DOTALL).findall(bloque)

    ses = 0

    for url in matches:
        ses += 1

        if url:
            if '/z-a.pages.dev/' in url: continue
            elif '/ddl-za.' in url: continue

            url = url.replace('&amp;', '&').strip()

            servidor = 'directo'

            other = ''
            age = ''

            if '/view/' in url:
                data1 = do_downloadpage(url)
                data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data1)

                match1 = scrapertools.find_single_match(data, '>Download Torrent<.*?<a href="(.*?)"')

                if match1:
                    if not 'http' in match1: continue

                    age = ''

                    if match1.endswith('.torrent'): servidor = 'torrent'
                    elif 'magnet:' in match1:
                        servidor = 'torrent'
                        age = 'Magnet'

                    else: other = '?'

                    if servidor:
                        match1 = match1.replace('&amp;', '&').strip()

                        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = match1,
                                              language='Vose', other = other, age = age )) 

                continue

            elif '/user/' in url:
                data2 = do_downloadpage(url)
                data2 = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data2)

                matches2 = re.compile('<td colspan=".*?title="(.*?)</a>.*?</a>.*?<a href="(.*?)"', re.DOTALL).findall(data2)

                for title, link in matches2:
                    if not 'http' in link:
                       if '/download/' in link: link = 'https://nyaa.si' + link

                    age = ''

                    if link.endswith('.torrent'): servidor = 'torrent'
                    elif 'magnet:' in link:
                        servidor = 'torrent'
                        age = 'Magnet'

                    else: other = '?'

                    if servidor:
                        link = link.replace('&amp;', '&').strip()

                        other = scrapertools.find_single_match(title, ' - (.*?)WEB').strip()
                        other = other.replace('(' ,'').replace('[' ,'').strip()

                        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = link,
                                              language='Vose', other = other, age = age )) 

                continue

            if url.endswith('.torrent'): servidor = 'torrent'

            elif url.endswith('.mp4') or url.endswith('%20MP4'): other = 'Mp4'
            elif url.endswith('.mkv') or url.endswith('%20MKV'): other = 'Mkv'

            elif 'magnet:' in url:
                  servidor = 'torrent'
                  age = 'Magnet'

            else: other = '?'

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                  language='Vose', other = other, age = age )) 

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if ' S1 ' in SerieName: SerieName = SerieName.split(" S1 ")[0]
    elif ' S2 ' in SerieName: SerieName = SerieName.split(" S2 ")[0]
    elif ' S3 ' in SerieName: SerieName = SerieName.split(" S3 ")[0]
    elif ' S4 ' in SerieName: SerieName = SerieName.split(" S4 ")[0]
    elif ' S5 ' in SerieName: SerieName = SerieName.split(" S5 ")[0]
    elif ' S6 ' in SerieName: SerieName = SerieName.split(" S6 ")[0]
    elif ' S7 ' in SerieName: SerieName = SerieName.split(" S7 ")[0]
    elif ' S8 ' in SerieName: SerieName = SerieName.split(" S8 ")[0]
    elif ' S9 ' in SerieName: SerieName = SerieName.split(" S9 ")[0]

    if ' s1 ' in SerieName: SerieName = SerieName.split(" s1 ")[0]
    elif ' s2 ' in SerieName: SerieName = SerieName.split(" s2 ")[0]
    elif ' s3 ' in SerieName: SerieName = SerieName.split(" s3 ")[0]
    elif ' s4 ' in SerieName: SerieName = SerieName.split(" s4 ")[0]
    elif ' s5 ' in SerieName: SerieName = SerieName.split(" s5 ")[0]
    elif ' s6 ' in SerieName: SerieName = SerieName.split(" s6 ")[0]
    elif ' s7 ' in SerieName: SerieName = SerieName.split(" s7 ")[0]
    elif ' s8 ' in SerieName: SerieName = SerieName.split(" s8 ")[0]
    elif ' s9 ' in SerieName: SerieName = SerieName.split(" s9 ")[0]

    if '-s1' in SerieName: SerieName = SerieName.split("-s1")[0]
    elif '-s2' in SerieName: SerieName = SerieName.split("-s2")[0]
    elif '-s3' in SerieName: SerieName = SerieName.split("-s3")[0]
    elif '-s4' in SerieName: SerieName = SerieName.split("-s4")[0]
    elif '-s5' in SerieName: SerieName = SerieName.split("-s5")[0]
    elif '-s6' in SerieName: SerieName = SerieName.split("-s6")[0]
    elif '-s7' in SerieName: SerieName = SerieName.split("-s7")[0]
    elif '-s8' in SerieName: SerieName = SerieName.split("-s8")[0]
    elif '-s9' in SerieName: SerieName = SerieName.split("-s9")[0]

    if ' T1 ' in SerieName: SerieName = SerieName.split(" T1 ")[0]
    elif ' T2 ' in SerieName: SerieName = SerieName.split(" T2 ")[0]
    elif ' T3 ' in SerieName: SerieName = SerieName.split(" T3 ")[0]
    elif ' T4 ' in SerieName: SerieName = SerieName.split(" T4 ")[0]
    elif ' T5 ' in SerieName: SerieName = SerieName.split(" T5 ")[0]
    elif ' T6 ' in SerieName: SerieName = SerieName.split(" T6 ")[0]
    elif ' T7 ' in SerieName: SerieName = SerieName.split(" T7 ")[0]
    elif ' T8 ' in SerieName: SerieName = SerieName.split(" T8 ")[0]
    elif ' T9 ' in SerieName: SerieName = SerieName.split(" T9 ")[0]

    if '2nd' in SerieName: SerieName = SerieName.split("2nd")[0]
    if '3rd' in SerieName: SerieName = SerieName.split("3rd")[0]
    if '4th' in SerieName: SerieName = SerieName.split("4th")[0]
    if '5th' in SerieName: SerieName = SerieName.split("5th")[0]
    if '6th' in SerieName: SerieName = SerieName.split("6th")[0]
    if '7th' in SerieName: SerieName = SerieName.split("7th")[0]
    if '8th' in SerieName: SerieName = SerieName.split("8th")[0]
    if '9th' in SerieName: SerieName = SerieName.split("9th")[0]

    SerieName = SerieName.strip()

    return SerieName


def clean_title(title):
    logger.info()

    title = title.replace('\\u00e1', 'a').replace('\\u00c1', 'a').replace('\\u00e9', 'e').replace('\\u00ed', 'i').replace('\\u00f3', 'o').replace('\\u00fa', 'u')
    title = title.replace('\\u00f1', 'ñ').replace('\\u00bf', '¿').replace('\\u00a1', '¡').replace('\\u00ba', 'º')
    title = title.replace('\\u00eda', 'a').replace('\\u00f3n', 'o').replace('\\u00fal', 'u').replace('\\u00e0', 'a')

    title = title.replace('\\u2019', "'")

    title = title.replace('\\u00c0', "A").replace('\\u010c0', "C")

    return title


def search(item, texto):
    logger.info()
    try:
        item.url = host + '/?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

