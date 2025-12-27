# -*- coding: utf-8 -*-
"""utils.py — fachada estable (solo Py3)

Este módulo mantiene la API histórica `utils.*` para el resto del addon,
pero las implementaciones viven en módulos pequeños (net/fs/system/kodi/...).
"""

import xbmcaddon

from lib import constants

# Identidad del addon
ADDON_ID = constants.ADDON_ID
try:
    addon = xbmcaddon.Addon(id=ADDON_ID)
except Exception:
    # fallback defensivo (Add-on aún no registrado / contexto raro)
    addon = xbmcaddon.Addon()

try:
    ADDON_NAME = addon.getAddonInfo("name") or constants.ADDON_NAME
except Exception:
    ADDON_NAME = constants.ADDON_NAME

# Re-exports: FS / NET / SYSTEM / KODI / DEVICE / STATE+CB / CATALOGO / TELEGRAM / CRYPTO
from lib.fs_utils import (  # noqa: F401
    _read_bytes,
    _sha256,
    _sha256_bytes,
    _cleanup_dir,
    _safe_rmtree,
    atomic_write_bytes,
    atomic_write_text,
)

from lib.net_utils import (  # noqa: F401
    wait_for_dns,
    _has_network,
    _has_internet,
    is_online,
    _net_open,
    download_atomic,
)

from lib.system_utils import (  # noqa: F401
    run_cmd,
)

from lib.kodi_utils import (  # noqa: F401
    kodi_is_idle,
    restart_kodi_with_popup,
)

from lib.device_utils import (  # noqa: F401
    is_master_device,
    get_device_role,
    is_client,
    get_key_from_authorized_keys,
    get_net_info,
    get_zerotier_ids,
)

from lib.reliability_utils import (  # noqa: F401
    cb_should_run,
    cb_note_success,
    cb_note_failure,
    cb_should_log_cooldown,
    metrics_note,
    metrics_get,
)

from lib.catalog_utils import (  # noqa: F401
    load_catalog_github,
)

from lib.telegram_utils import (  # noqa: F401
    telegram_send_log_with_summary_if_problem,
)

from lib.crypto_utils import (  # noqa: F401
    decrypt,
)
