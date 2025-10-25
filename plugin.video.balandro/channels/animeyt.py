# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://animeytx.net/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://animeyt.moe/', 'https://animeenlatino.moe/', 'https://aniyt.net/',
             'https://wvw.aniyt.net/', 'https://animeytx.com/']


domain = config.get_setting('dominio', 'animeyt', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'animeyt')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'animeyt')
    else: host = domain


def do_downloadpage(url, post=None, headers=None):
    for ant in ant_hosts:
        url = url.replace(ant, host)

    data = httptools.downloadpage(url, post=post).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'animeyt', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_animeyt', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='animeyt', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_animeyt', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'animeyt', thumbnail=config.get_thumb('animeyt') ))

    platformtools.itemlist_refresh()

    return itemlist


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

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'all', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'tv/?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'tv/?status=&type=&sub=&order=latest&page=1' , search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'last_animes', search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Actualizados', action = 'list_all', url = host + 'tv/?status=&type=&sub=&order=update&page=1', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'tv/?status=ongoing&page=1', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'tv/?status=completed&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'tv/?sub=&order=popular&page=1', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'tv/?status=&type=&order=rating&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Proximamente', action = 'list_all', url = host + 'tv/?status=upcoming&page=1', search_type = 'tvshow', text_color='yellowgreen' ))

    itemlist.append(item.clone( title = 'Series', action = 'list_all', url = host + 'tv/?status=&type=tv&order=update&page=1', search_type = 'tvshow', text_color = 'hotpink' ))
    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'tv/?status=&type=movie&order=update&page=1', search_type = 'movie', text_color='deepskyblue' ))

    itemlist.append(item.clone( title = 'Onas', action = 'list_all', url = host + 'tv/?status=&type=ona&order=update&page=1', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'tv/?type=ova&sub=&order=update&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def last_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_all', url = host + 'tv/?status=&type=&sub=&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos animes en castellano', action = 'list_all',  url = host + 'tv/?sub=cast&order=latest&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos animes en latino', action = 'list_all', url = host + 'tv/?status=&type=&sub=dub&page=1',search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos animes subtitulados', action = 'list_all', url = host + 'tv/?sub=sub&order=&page=1', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'tv/?sub=cast&order=update&page=1', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'tv/?sub=dub&order=update&page=1', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = host + 'tv/?sub=sub&order=update&page=1', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'tv/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '> Género <(.*?)</ul>')

    matches = re.compile('value="(.*?)".*?<label for=.*?">(.*?)</label>').findall(bloque)

    for value, title in matches:
        if title == '144fps': continue
        elif title == '4K': continue

        url = host + 'tv/?genre[]=' + value + '&status=&type=&sub=&order=&page=1'

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Modo Texto<(.*?)</div></div></div>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<h1(.*?)</div></div></div>')

    matches = re.compile('<article(.*?)</article>').findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace('(' + year + ')', '').replace('(' + year + ' )', '').strip()
        else: year = '-'

        title = title.replace('&#8217;', "'").replace('&#8211;', '').replace('&#215;', 'x')

        tipo = 'movie' if '>Pelicula<' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        lang = ''

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            PeliName = corregir_SerieName(title)

            if '[Latino' in title or 'Latino]' in title: lang = 'Lat'
            elif '[Castellano' in title or 'Castellano]' in title: lang = 'Esp'

            title = title.replace('Audio', '[COLOR red]Audio[/COLOR]')

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, lang=lang, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = PeliName, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            season = 1

            if 'Temporada' in title:
                season = scrapertools.find_single_match(url, 'temporada-(.*?)-')

                if not season: season = scrapertools.find_single_match(title, 'Temporada(.*?)Capítulo').strip()
                if not season : season = scrapertools.find_single_match(title, 'Temporada(.*?)$').strip()

                if not season: season = 1

            SerieName = corregir_SerieName(title)

            title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

            title = title.replace('Audio', '[COLOR red]Audio[/COLOR]')

            if '[Latino' in title or 'Latino]' in title: lang = 'Lat'
            elif '[Castellano' in title or 'Castellano]' in title: lang = 'Esp'

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, lang=lang, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, contentSeason = season, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
         if '<div class="pagination">' in data:
             next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?class="page-numbers current">.*?href="(.*?)"')
         else:
             bloque = scrapertools.find_single_match(data, '</article></div>(.*?)</i></a>')

             if 'Previous' in bloque: next_page = scrapertools.find_single_match(bloque, 'Previous.*?<a href="(.*?)"')
             else: next_page = scrapertools.find_single_match(bloque, '<a href="(.*?)"')

         if next_page:
             if 'page=' in next_page: next_page = host + 'tv/' + next_page

             if 'page=' in next_page or '/page/' in next_page:
                 itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="eplister">(.*?)</ul></div></div>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<div class="epl-num">(.*?)</div>.*?<div class="epl-title">(.*?)</div>')

    if not matches:
        if 'Próximamente<' in data:
             platformtools.dialog_notification('AmimeYt', '[COLOR cyan][B]Proximamente[/B][/COLOR]')
             return

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, epis, title in matches[item.page * item.perpage:]:
        if str(item.contentSeason) == 'Final' or str(item.contentSeason) == 'FINAL': item.contentSeason = 1

        title = title.replace('&#8217;', "'").replace('&#8211;', '').replace('&#215;', 'x')

        if '| Final' in epis: epis = epis.replace('| Final', '').strip()
        elif '| FINAL' in epis: epis = epis.replace('| FINAL', '').strip()
        elif '| Fin' in epis: epis = epis.replace('| Fin', '').strip()
        elif '| Estreno' in epis: epis = epis.replace('| Estreno', '').strip()

        if len(str(epis)) >= 4:
            epis = 1
            titulo = title
        else:
            if item.contentSerieName: titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title + ' ' + item.contentSerieName
            else: titulo = item.title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason=item.contentSeason, contentEpisodeNumber=epis ))

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

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    if not item.search_type == 'tvshow':
        data = do_downloadpage(item.url)
        data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

        new_url = scrapertools.find_single_match(data, '<li data-index="0">.*?<a href="(.*?)"')

        if new_url:
            data = do_downloadpage(new_url)
    else:
        data = do_downloadpage(item.url)

    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    lang = 'Vose'

    if item.lang: lang = item.lang

    ses = 0

    if '>Servidores' in data:
        bloque = scrapertools.find_single_match(data, '>Servidores(.*?)</select>')

        matches = re.compile('<option value="(.*?)".*?data-index="(.*?)">(.*?)</option>', re.DOTALL).findall(bloque)

        for url, idx, idio in matches:
            ses += 1

            url = url.replace('\\/' ,'/')

            if url:
                if not url.startswith("http"):
                    b64_decode = base64.b64decode(url)

                    if b64_decode:
                        url = scrapertools.find_single_match(str(b64_decode), '<iframe.*?src="(.*?)"')
                        if not url: url = scrapertools.find_single_match(str(b64_decode), "<iframe.*?src='(.*?)'")
                        if not url: url = scrapertools.find_single_match(str(b64_decode), '<IFRAME.*?SRC="(.*?)"')
                        if not url: url = scrapertools.find_single_match(str(b64_decode), "<IFRAME.*?SRC='(.*?)'")

                        if not url: url = scrapertools.find_single_match(str(b64_decode), '<a href="(.*?)"')
                        if not url: url = scrapertools.find_single_match(str(b64_decode), "<a href='(.*?)'")

                if url.startswith('//'): url = 'https:' + url

                elif url.startswith("/"): url = host[:-1] + url

                if not url.startswith("http"): continue

                if 'player.animeyt' in url: continue
                elif 'jetload.' in url: continue
                elif '.tioanime.' in url: continue
                elif '.fembed.' in url: continue
                elif 'petardas.online' in url: continue

                if '/mytsumi.' in url:
                    id = ''

                    if '/multiplayer/options.php?' in url:
                        id = scrapertools.find_single_match(url, '&value=(.*?)&')

                    if id:
                        datam = do_downloadpage('https://mytsumi.com/multiplayer/contenedor.php?id=' + id)

                        matches1 = re.compile('"tab_name":.*?"url":"(.*?)"', re.DOTALL).findall(datam)
                        matches2 = re.compile('"server_id".*?"download_url":"(.*?)"', re.DOTALL).findall(datam)

                        matchesm = matches1 + matches2

                        for link in matchesm:
                            link = link.replace('\\/' ,'/')

                            link = link.replace('&amp;', '&')

                            if '/ytplay.' in link: continue
                            elif '/short.' in link: continue

                            elif '.fireload.' in link: continue

                            elif 'terabox.' in link: continue

                            url = link

                            servidor = servertools.get_server_from_url(url)
                            servidor = servertools.corregir_servidor(servidor)

                            url = servertools.normalize_url(servidor, url)

                            other = ''
                            if servidor == 'various': other = servertools.corregir_other(url)
                            else:
                               if '/mytsumi.' in url: other = 'Mytsumi'

                            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                                 language = lang, other = other ))

                        continue

                if url.endswith('vipbanner.html'): continue

                elif '/short.' in url: continue
                elif '/animeyt2.' in url: continue
                elif '/aniwen.' in url: continue

                elif '.fireload.' in url: continue

                elif '/new/play/one.php?' in url: continue
                elif '/new/redirector.php?' in url: continue
                elif '/v/descarga.php?' in url: continue

                url = url.replace('/altamina.online/', '/filemoon.sx/')
                url = url.replace('/conlafuerzademilsalchipapas.site/', '/filemoon.sx/')

                url = url.replace('/elbailedeltroleo.site/', '/vgembed.com/')
                url = url.replace('/yosisubogordas.site/', '/vgembed.com/')

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                other = ''
                if servidor == 'various': other = servertools.corregir_other(url)

                if other == '':
                    if servidor == 'directo':
                        if '/ytlinker.' in url:
                            if 'server=moon' in url:
                               servidor = 'filemoon'
                               other = ''
                            elif 'server=tera' in url:
                               other = 'Terabox'
                        elif 'Tera' in idio: other: other = 'Terabox'
                        else:
                            other = scrapertools.find_single_match(str(idio), '(.*?)-').strip()

                if 'Latino' in idio: lang = 'Lat'
                elif 'Castellano' in idio: lang = 'Esp'
                elif 'Catalán' in idio: lang = 'Cat'
                elif 'Subtitulado' in idio: lang = 'Vose'
                elif 'Japonés' in idio: lang = 'Jap'
                elif 'Inglés' in idio: lang = 'Eng'

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                      language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    new_url = ''

    servidor = item.server

    item.url = item.url.replace('&amp;', '&')

    item.url = item.url.replace('//animeyt.pro/', host).replace('//animeyt2.es/', host)

    item.url = item.url.replace(host + 'e/', '/waaw.to/e/')

    if '/waaw.to/' in item.url: servidor = 'waaw'

    item.url = item.url.replace('%5Cr%5Cn', '').strip()

    url = item.url

    if '/ytlinker.' in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, '<a href="(.*?)"')

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            new_url = servertools.normalize_url(servidor, url)

            if new_url: url = ''

    elif '/new/redirector2.php?' in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, "window.location.href.*?'(.*?)'")

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            new_url = servertools.normalize_url(servidor, url)

            if new_url: url = ''

    elif '/new/descarga.php?' in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, '<a target.*?href="(.*?)"')

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            new_url = servertools.normalize_url(servidor, url)

            if new_url: url = ''

    elif '/mytsumiplay/player.php?' in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, '<source.*?src="(.*?)"')

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            new_url = servertools.normalize_url(servidor, url)

            if new_url: url = ''

    if host in url or '/animeytx.' in url: url = ''

    if url:
        if not servidor == 'directo':
            itemlist.append(item.clone(url = item.url, server = servidor))

            return itemlist
        else:
            if item.other == 'Tera'or item.other == 'Terabbox': item.url = item.url.replace('/one.php?', '/two.php?')

            if '.php?' in item.url:
                resp = httptools.downloadpage(item.url, follow_redirects=False)

                new_url = scrapertools.find_single_match(resp.data, '<a href="(.*?)"')
                if 'php?' in new_url:
                    resp = httptools.downloadpage(new_url, follow_redirects=False)

                    url = scrapertools.find_single_match(resp.data, "window.location.href = '(.*?)'")

                    new_url = ''

    if new_url: url = new_url

    if host in url or '/animeytx.' in url or '/play/hytplayer/' in url: url = ''

    if '/mytsumi.' in url: url = ''
    elif '/short.' in url: url = ''
    elif '/repro.' in url: url = ''
    elif '/ytplay.' in url: url = ''

    elif '/animeyt2.' in url: url = ''
    elif '/aniwen.' in url: url = ''

    elif '.fireload.' in url: url = ''

    if url:
        if not url.startswith("http"): url = "https:" + url

        url = url.replace('&amp;', '&').replace("\\/", "/")

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Temporada ' in SerieName: SerieName = SerieName.split("Temporada ")[0]

    if '(OVA)' in SerieName: SerieName = SerieName.split("(OVA)")[0]

    if '[Película' in SerieName: SerieName = SerieName.split("[Película")[0]

    if '[Temporada' in SerieName: SerieName = SerieName.split("[Temporada")[0]

    if '[Latino' in SerieName: SerieName = SerieName.split("[Latino")[0]
    elif 'Latino]' in SerieName: SerieName = SerieName.split("Latino]")[0]
    elif '[Castellano' in SerieName: SerieName = SerieName.split("[Castellano")[0]
    elif 'Castellano]' in SerieName: SerieName = SerieName.split("Castellano]")[0]
    elif '[Subtitulado' in SerieName: SerieName = SerieName.split("[Subtitulado")[0]
    elif 'Subtitulado]' in SerieName: SerieName = SerieName.split("Subtitulado]")[0]

    SerieName = SerieName.strip()

    return SerieName


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

