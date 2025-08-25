import sqlite3
import os
import datetime
import xml.etree.ElementTree as ET
from . import utils

KODI_DB_PATH = "/storage/.kodi/userdata/Database/"

def get_kodi_db_path():
    """
    Busca la base de datos de addons de Kodi.
    Devuelve la ruta completa al archivo o None si no se encuentra.
    """
    try:
        db_files = [f for f in os.listdir(KODI_DB_PATH) if f.startswith('Addons') and f.endswith('.db')]
        if db_files:
            utils.write_log(f"Base de datos de addons encontrada: {os.path.join(KODI_DB_PATH, db_files[0])}")
            return os.path.join(KODI_DB_PATH, db_files[0])
        else:
            utils.write_log("No se encontró ninguna base de datos de addons en el directorio de Kodi.", level="ERROR")
    except FileNotFoundError:
        utils.write_log(f"El directorio de bases de datos de Kodi no se encontró en: {KODI_DB_PATH}", level="ERROR")
    except Exception as e:
        utils.write_log(f"Error al buscar la base de datos de addons: {e}", level="ERROR")
    return None

def get_addon_status(addon_id):
    """
    Obtiene el estado de un addon (instalado y habilitado).
    Devuelve una tupla (instalado, habilitado) o (False, False) si hay un error o no se encuentra.
    """
    db_path = get_kodi_db_path()
    if not db_path:
        return False, False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Usar la tabla 'installed' para verificar si el addon está instalado
        cursor.execute("SELECT enabled FROM installed WHERE addonID = ?", (addon_id,))
        result = cursor.fetchone()

        if result:
            enabled = bool(result[0])
            utils.write_log(f"Estado del addon {addon_id}: instalado, habilitado={enabled}")
            return True, enabled
        else:
            utils.write_log(f"Addon {addon_id} no encontrado en la base de datos.")
            return False, False
    except sqlite3.OperationalError as e:
        utils.write_log(f"Error al obtener el estado del addon: {e}", level="ERROR")
        return False, False
    finally:
        if conn:
            conn.close()

def set_addon_status(addon_id, enabled_status):
    """
    Actualiza el estado de un addon en la base de datos.
    """
    db_path = get_kodi_db_path()
    if not db_path:
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE installed SET enabled = ? WHERE addonID = ?", (enabled_status, addon_id))
        conn.commit()
        utils.write_log(f"Estado de {addon_id} actualizado a enabled={enabled_status}.")
        return True
    except sqlite3.Error as e:
        utils.write_log(f"Error al establecer el estado del addon: {e}", level="ERROR")
        return False
    finally:
        if conn:
            conn.close()

def register_addon(addon_id, enabled_status, repository):
    """
    Registra un addon como instalado en la base de datos, incluyendo fecha de instalación y repositorio.
    """
    db_path = get_kodi_db_path()
    if not db_path:
        return False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        install_date = datetime.date.today().strftime("%Y-%m-%d")
        
        cursor.execute(
            "INSERT OR IGNORE INTO installed (addonID, enabled, installDate, origin) VALUES (?, ?, ?, ?)",
            (addon_id, enabled_status, install_date, repository)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        utils.write_log(f"Error al registrar el addon: {e}", level="ERROR")
        return False
    finally:
        if conn:
            conn.close()

def check_db_paths(db_path, required_conditions):
    """
    Verifica si una ruta de base de datos existe y cumple con ciertas condiciones.
    """
    if not os.path.exists(db_path):
        utils.write_log(f"Ruta de la base de datos no encontrada: {db_path}", level="ERROR")
        return False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Iterar a través de las condiciones requeridas y verificar en la tabla 'path'
        for path_check, content_check, scraper_check in required_conditions:
            query = """
                SELECT strPath FROM path
                WHERE strPath = ? AND strContent = ? AND strScraper = ?
            """
            cursor.execute(query, (path_check, content_check, scraper_check))
            result = cursor.fetchone()

            if not result:
                utils.write_log(f"Condición no cumplida en {db_path}: No se encontró la ruta '{path_check}' con contenido '{content_check}' y scraper '{scraper_check}'.", level="WARNING")
                return False
            else:
                utils.write_log(f"Condición cumplida: '{path_check}' con contenido '{content_check}' y scraper '{scraper_check}'.")
                
        utils.write_log("Todas las condiciones de la base de datos han sido verificadas y son correctas.")
        return True
    except sqlite3.OperationalError as e:
        utils.write_log(f"Error de base de datos corrupta en {db_path}: {e}", level="ERROR")
        return False
    finally:
        if conn:
            conn.close()
