# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import config, logger


def host(host, dominios):
    logger.info()

    current_domain = ''

    try:
        data = httptools.downloadpage('https://entrarplaydede.com/').data

        bloque = scrapertools.find_single_match(data, '<main>(.*?)</section>')

        currents_domains = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?</a>')
        if not currents_domains: currents_domains = scrapertools.find_multiple_matches(bloque, 'data-url="(.*?)".*?</a>')

        if currents_domains:
            for current_domain in currents_domains:
                if current_domain:
                    current_domain = current_domain.lower().strip()

                    if not 'playdede.' in current_domain: continue

                    if not 'https' in current_domain: current_domain  = 'https://' + current_domain
                    if not current_domain.endswith('/'): current_domain = current_domain + '/'

                    if current_domain in str(dominios): return host

                    break
    except:
        pass

    if current_domain:
        domain = config.get_setting('dominio', 'playdede', default='')
        if not domain:
            domain = current_domain
            host = domain

        else:
          if not domain == host: host = current_domain

    return host
