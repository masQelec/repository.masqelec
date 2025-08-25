import xbmc
import xbmcgui
import os
import traceback
import sys
import threading
import shutil
import datetime
import subprocess
from lib import utils
from lib.updater import update_system
from lib.webserver_check import ensure_autostart, is_webserver_enabled
from lib.cloud_storage import start_cloud_storage
from lib.update_library import update_library
from lib.update_pvr import update_pvr

def handle_auto_update():
    """Maneja la actualización automática del sistema."""
    if utils.addon.getSettingBool("auto_update"):
        utils.write_log("Opción de auto update activada. Iniciando la actualización del sistema en segundo plano.")
        auto_update_thread = threading.Thread(target=update_system)
        auto_update_thread.daemon = True
        auto_update_thread.start()
    else:
        utils.write_log("Auto update desactivado")

def updates_library_pvr():
    """
    Función que ejecuta las actualizaciones en el orden correcto.
    Esta será el objetivo del hilo.
    """
    if utils.addon.getSettingBool("update_library"):
        utils.write_log("Opción de actualización de la biblioteca activada. Iniciando la actualización en segundo plano.")
        update_library()
        utils.write_log("Las actualizaciones de la biblioteca han finalizado.")
    else:
        utils.write_log("Actualización de la biblioteca está desactivada.")
        
    if utils.addon.getSettingBool("update_pvr"):
        utils.write_log("Opción de actualización de PVR activada. Iniciando la actualización del PVR en segundo plano.")
        if update_pvr():
            utils.write_log("Las actualizaciones del PVR han finalizado.")
        else:
            utils.write_log("Las actualizacion del PVR no ha sido posible")
    else:
        utils.write_log("Actualización del PVR está desactivada.")
        
def handle_updates_library_pvr():
    """Maneja la ejecución de las actualizaciones en un hilo separado."""
    updates_library_pvr_thread = threading.Thread(target=updates_library_pvr)
    updates_library_pvr_thread.daemon = True
    updates_library_pvr_thread.start()
    updates_library_pvr_thread.join() # Espera a que el hilo de PVR/Library termine

def view_log():
    """Abre el log en un cuadro de texto."""
    LOG_FILE = os.path.join(utils.PROFILE_PATH, "service.log")
    if not os.path.exists(LOG_FILE):
        xbmcgui.Dialog().ok(utils.ADDON_NAME, utils.addon.getLocalizedString(30007), "No hay log disponible")
        return
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            contenido = f.read()[-4000:]
        xbmcgui.Dialog().textviewer(utils.ADDON_NAME, utils.addon.getLocalizedString(30007), contenido)
    except Exception as e:
        xbmcgui.Dialog().ok(utils.ADDON_NAME, f"Error al abrir log: {e}")

def get_zerotier_network_name():
    """Obtiene el nombre de la red de ZeroTier utilizando la ruta específica."""
    
    zerotier_cli_path = "/storage/.opt/bin/zerotier-cli"

    if not os.path.exists(zerotier_cli_path):
        utils.write_log(f"El comando '{zerotier_cli_path}' no se encontró en la ruta especificada.", level="WARNING")
        return "unknown_network"

    try:
        # Ejecuta el comando y captura la salida
        result = subprocess.run(
            [zerotier_cli_path, 'listnetworks'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Procesa la salida para encontrar el nombre de la red
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1: # Asegura que hay al menos una línea de datos
            # La primera línea es la cabecera, la segunda es la de datos
            data_line = lines[1]
            columns = data_line.split()
            if len(columns) >= 3:
                # El tercer elemento (índice 2) es el nombre
                return columns[2]
    except subprocess.CalledProcessError as e:
        utils.write_log(f"Error al ejecutar zerotier-cli: {e.stderr}", level="ERROR")
    except IndexError:
        utils.write_log("La salida de 'zerotier-cli' no tiene el formato esperado.", level="WARNING")
    
    return "unknown_network" # Retorna un valor por defecto si falla

def get_eth0_mac_address():
    """Obtiene la dirección MAC de la interfaz eth0."""
    mac_path = "/sys/class/net/eth0/address"
    if os.path.exists(mac_path):
        try:
            with open(mac_path, 'r') as f:
                mac = f.read().strip().replace(':', '')
                return mac
        except Exception as e:
            utils.write_log(f"Error al leer la dirección MAC de eth0: {e}", level="WARNING")
    else:
        utils.write_log("La interfaz de red 'eth0' no se encontró o no tiene una dirección MAC.", level="WARNING")
    
    return "unknown_mac" # Retorna un valor por defecto si falla

# -------------------------------
# Inicio del Addon
# -------------------------------
try:
    if len(sys.argv) > 1 and sys.argv[1] == "viewlog":
        view_log()
        sys.exit()
        
    # --- Lógica para eliminar el log anterior ---
    log_file_path = os.path.join(utils.PROFILE_PATH, "service.log")
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
        
    utils.write_log("Addon iniciado")
    
    if not is_webserver_enabled():
        utils.write_log("Servidor web no está activo. Iniciando el proceso de corrección para autostart.sh.")
        ensure_autostart()
    else:
        utils.write_log("Servidor web activo. El script de corrección no se iniciará.")
    
    start_cloud_storage()
    
    handle_auto_update()
    
    handle_updates_library_pvr()

    utils.write_log("Operaciones de arranque completadas")

    error_or_warning_found = False
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '[ERROR]' in line or '[WARNING]' in line:
                    error_or_warning_found = True
                    break

    network_name = get_zerotier_network_name()
    mac_address = get_eth0_mac_address()  

    destination_filename = f"{network_name}_{mac_address}_service.log"
    rclone_bin_path = "/storage/.config/rclone/rclone"
           
    if error_or_warning_found:

        utils.write_log(f"Se encontraron errores o advertencias. Copiando log a log:log/{destination_filename} usando rclone.")
        try:
            subprocess.run(
                [rclone_bin_path, "copy", log_file_path, f"log:log/{destination_filename}"],
                check=True
            )
            utils.write_log("Copia del log realizada con éxito a través de rclone.")
        except FileNotFoundError:
            utils.write_log(f"El comando 'rclone' no se encontró en la ruta especificada: {rclone_bin_path}", level="ERROR")
        except subprocess.CalledProcessError as rclone_e:
            utils.write_log(f"Error al ejecutar rclone: {rclone_e.stderr}", level="ERROR")
    else:
        utils.write_log(f"Se envia info. Copiando log a log:log/{destination_filename} usando rclone.")
        try:
            subprocess.run(
                [rclone_bin_path, "copy", log_file_path, f"log:log/{destination_filename}"],
                check=True
            )
            utils.write_log("Copia del log realizada con éxito a través de rclone.")
        except FileNotFoundError:
            utils.write_log(f"El comando 'rclone' no se encontró en la ruta especificada: {rclone_bin_path}", level="ERROR")
        except subprocess.CalledProcessError as rclone_e:
            utils.write_log(f"Error al ejecutar rclone: {rclone_e.stderr}", level="ERROR")
                
except Exception as e:
    utils.write_log(f"Error durante el arranque: {e}\n{traceback.format_exc()}", level="ERROR")
