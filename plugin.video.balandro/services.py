# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# WebTV - servicios
# ------------------------------------------------------------

import threading
from platformcode import config

# Lanzar servicio para comprobar nuevos capítulos
# -----------------------------------------------
def comprobar_nuevos_episodios():
    if config.get_setting('addon_tracking_atstart', default=True):
        interval = int(config.get_setting('addon_tracking_interval', default='12')) * 3600 # horas convertidas a segundos

        import xbmc, time
        from core import trackingtools

        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            if config.get_setting('addon_tracking_atstart', default=True): # por si se desactiva con el servicio ejecutándose
                lastscrap = config.get_setting('addon_tracking_lastscrap', default='')
                if lastscrap == '' or float(lastscrap) + interval <= time.time():
                    trackingtools.check_and_scrap_new_episodes(notification=config.get_setting('addon_tracking_verbose', default=False))

            if monitor.waitForAbort(3600):
                break

threading.Thread(target=comprobar_nuevos_episodios).start()
