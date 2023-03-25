# -*- coding: utf-8 -*-

# ~ Exemples de queries a executar manualment dins la bd developer.sqlite :

# - Llistar links d'un server concret:
# ~ SELECT * FROM playables_links WHERE server = 'netutv'

# - Llistar diferents canals que utilitzen un server concret:
# ~ SELECT DISTINCT(channel) FROM playables_links WHERE server = 'netutv'

# - Llistar diferents servers que s'utilitzen un canal concret:
# ~ SELECT DISTINCT(server) FROM playables_links WHERE channel = 'hdfull'

# - Llistar nombre de links que té cada peli/episodi:
# ~ SELECT COUNT(*) AS num_links FROM playables_links GROUP BY id_playable
# ~ SELECT COUNT(*) AS num_links, p.* FROM playables_links l INNER JOIN playables p ON l.id_playable = p.id_playable GROUP BY l.id_playable


import os, time, base64, sqlite3
from datetime import datetime, timedelta

from core.item import Item
from platformcode import config, logger, platformtools

from core import filetools, jsontools


if not os.path.exists(os.path.join(config.get_data_path(), 'developer.sqlite')):
    platformtools.dialog_ok(config.__addon_name, "Falta el fichero 'developer.sqlite'")

# - Clase para cargar y guardar en la bd de tracking
class TrackingData:
    def __init__(self, filename = 'developer.sqlite'):
        self.filename = filetools.join(config.get_data_path(), filename)

        self.conn = sqlite3.connect(self.filename)
        self.cur = self.conn.cursor()

        # - PRAGMA user_version para identificar versión de las tablas y crear/alterar en consecuencia
        self.cur.execute('PRAGMA user_version')
        db_user_version = self.cur.fetchone()[0]

        if db_user_version == 0:
            self.create_tables()
            self.cur.execute('PRAGMA user_version=1')
            db_user_version = 1

            logger.info('Creada base de datos %s versión %d' % (self.filename, db_user_version))

    def create_tables(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS playables (id_playable INTEGER PRIMARY KEY, channel TEXT, tipo TEXT, title TEXT, season INTEGER, episode INTEGER, url TEXT, infolabels TEXT, updated TEXT, notes TEXT)')

        self.cur.execute('CREATE TABLE IF NOT EXISTS playables_links (channel TEXT, server TEXT, url TEXT, language TEXT, quality TEXT, url_referer TEXT, id_playable INTEGER, updated TEXT, notes TEXT)')

    def close(self, commit=False, rollback=False):
        if commit: self.conn.commit()
        elif rollback: self.conn.rollback()
        self.conn.close()

    # - Funciones
    def get_playable(self, channel='', tipo='', title='', season='', episode=''):
        title = title.decode('utf-8')
        self.cur.execute('SELECT * FROM playables WHERE channel=? AND tipo=? AND title=? AND season=? AND episode=?', (channel,tipo,title,season,episode))
        row = self.cur.fetchone()
        return row

    def save_playable(self, channel='', parent_item=None, commit=False):
        # ~ title = infolabels['title'].decode('utf-8')
        tipo = parent_item.contentType
        if parent_item.contentType == 'movie':
            title = parent_item.contentTitle.decode('utf-8')
            season = 0
            episode = 0
        else:
            title = parent_item.contentSerieName.decode('utf-8')
            season = parent_item.contentSeason
            episode = parent_item.contentEpisodeNumber

        url = parent_item.url
        infolabels = base64.b64encode(jsontools.dump(parent_item.infoLabels))

        self.cur.execute('INSERT OR REPLACE INTO playables (channel, tipo, title, season, episode, url, infolabels, updated, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (channel, tipo, title, season, episode, url, infolabels, datetime.now(), '' ))

        id_last = self.cur.lastrowid

        if commit: self.conn.commit()
        return id_last

    def save_playable_link(self, it=None, id_playable=0, commit=False):
        self.cur.execute('INSERT OR REPLACE INTO playables_links (channel, server, url, language, quality, url_referer, id_playable, updated, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (it.channel, it.server, it.url, it.language, it.quality, it.url_referer, id_playable, datetime.now(), '' ))

        if commit: self.conn.commit()

# - Funciones públicas
def developer_mode_check_findvideos(itemlist, parent_item, num_playables=10, num_dies=7):
    if len(itemlist) == 0: return True

    # - pq parent_item.channel pot ser 'tracking'
    canal = itemlist[0].channel

    db = TrackingData()

    # - Si ja hi ha num_playables pelis/episodis del mateix canal en els últims num_dies dies, no afegir-ne més
    desde = datetime.now() - timedelta(days=num_dies)
    db.cur.execute('SELECT COUNT(*) FROM playables WHERE channel=? AND tipo=? AND updated>?', (canal, parent_item.contentType, desde))
    num = db.cur.fetchone()[0]

    if num >= num_playables:
        logger.info('No apuntado en developertools pq ya hay %d %s para este canal en los últimos %d días' % (num_playables, parent_item.contentType, num_dies))
        db.close()
        return True

    if parent_item.contentType == 'movie':
        row = db.get_playable(canal, parent_item.contentType, parent_item.contentTitle, 0, 0)
    else:
        row = db.get_playable(canal, parent_item.contentType, parent_item.contentSerieName, parent_item.contentSeason, parent_item.contentEpisodeNumber)

    if row is not None:
        logger.info('No apuntado en developertools pq ya lo está')
        db.close()
        return True

        # ~ de moment sense updates
        # ~ update
        # ~ id_playable = row[0]
        # ~ db.update_playable_link(it, id_playable)
    else:
        # ~ alta
        id_playable = db.save_playable(canal, parent_item)

    for it in itemlist:
        if not it.url_referer: it.url_referer = parent_item.url
        db.save_playable_link(it, id_playable)

    db.close(commit=True)
    logger.info('Apuntado en developertools id_playable: %d con %d links' % (id_playable, len(itemlist)))

    return True
