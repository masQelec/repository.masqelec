import os
import urllib.request
import urllib.error
import traceback
import xbmc
import time
from . import db_utils
from . import jsonrpc_utils
from . import utils

def fix_movieset_folder():
    """
    Verifica y corrige la configuración de la carpeta de sets de películas
    usando la API JSON-RPC de Kodi.
    """
    # Configuración
    SETTING_ID = "videolibrary.moviesetsfolder"
    CORRECT_VALUE = "/storage/.cache/collection/"

    try:
        current_value = jsonrpc_utils.get_setting(SETTING_ID)
        if current_value != CORRECT_VALUE:
            utils.write_log(f"Valor incorrecto: '{current_value}' -> Corrigiendo a: '{CORRECT_VALUE}'")
            jsonrpc_utils.set_setting(SETTING_ID, CORRECT_VALUE)
            utils.notify_user("Configuración actualizada " + f"{SETTING_ID} corregido a {CORRECT_VALUE}")
            utils.write_log(f"'{SETTING_ID}' corregido: {current_value} -> {CORRECT_VALUE}")
        else:
            utils.write_log(f"'{SETTING_ID}' ya está correcto: {current_value}")
    except Exception as e:
        utils.write_log(f"Error al verificar/corregir guisettings vía JSON-RPC: {e}\n{traceback.format_exc()}", level="ERROR")

def fix_videos_db(db_dir="/storage/.kodi/userdata/Database/"):
    """
    Verifica en todas las bases MyVideos*.db.
    Si alguna no cumple las condiciones, la reemplaza descargándola desde el repositorio remoto.
    Devuelve True si todas las bases de datos están en orden.
    """
    # Las condiciones de la base de datos se definen aquí
    REQUIRED_CONDITIONS = [
        ("/storage/videos/", "movies", "metadata.local"),
        ("/storage/tvshows/1/", "tvshows", "metadata.local"),
        ("/storage/tvshows/2/", "tvshows", "metadata.local"),
    ]
    
    base_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/"
    db_files = [f for f in os.listdir(db_dir) if f.startswith("MyVideos") and f.endswith(".db")]
    
    if not db_files:
        db_file = "MyVideos131.db"
        db_path = os.path.join(db_dir, db_file)
        url = base_url + db_file
        
        utils.write_log(f"No se encontraron bases MyVideos*.db. Descargando {db_file}...")
        try:
            urllib.request.urlretrieve(url, db_path)
            utils.write_log(f"{db_file} descargado y reemplazado correctamente.")
        except Exception as e:
            utils.write_log(f"No se pudo descargar {db_file}: {e}\n{traceback.format_exc()}", level="ERROR")
            return False
        return False
        
    for db_file in db_files:
        db_path = os.path.join(db_dir, db_file)
        
        # Llama a la función de db_utils y se le pasan las condiciones
        if not db_utils.check_db_paths(db_path, REQUIRED_CONDITIONS):
            try:
                utils.write_log(f"Base de datos inválida encontrada: {db_file}. Reemplazando desde el repositorio remoto...")
                url = base_url + db_file
                if os.path.exists(db_path):
                    os.remove(db_path)
                urllib.request.urlretrieve(url, db_path)
                utils.write_log(f"{db_file} descargado y reemplazado correctamente.")
            except Exception as e:
                utils.write_log(f"No se pudo descargar {db_file}: {e}\n{traceback.format_exc()}", level="ERROR")
            # Devuelve False inmediatamente después de encontrar y reemplazar un archivo inválido
            return False

    return True

def update_library():
    """
    Verifica la base de datos de MyVideos.
    Si la verificación falla -> limpia la biblioteca, la actualiza,
    corrige los ajustes y reinicia Kodi.
    """
    # Verificar y corregir carpeta de sets
    fix_movieset_folder()

    # Verificar y corregir bases de datos de video
    if not fix_videos_db():
        # Notificación de inicio
        utils.notify_user("En mantenimiento, verificando base de datos")
        time.sleep(5) # Pausa de 5 segundos

        # Limpiar biblioteca de video
        xbmc.executebuiltin("CleanLibrary(video)")
        
        # Actualizar biblioteca de video
        xbmc.executebuiltin("UpdateLibrary(video)")
        
        utils.write_log("Base de datos inválida -> Biblioteca limpiada, actualizada.")
    else:
        utils.write_log("Base de datos válida -> No se requiere limpiar ni actualizar.")
