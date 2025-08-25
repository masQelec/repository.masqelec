import os
import base64
import urllib.request
import urllib.error
import subprocess
import traceback
import io
import difflib # <-- Nueva importación

from . import utils

# ------------------------------
# CIFRADO FEISTEL
# ------------------------------
def feistel_round(left: bytes, right: bytes, key: bytes):
    """
    Realiza una ronda del cifrado Feistel.
    Recibe la mitad izquierda y derecha, más una clave de ronda.
    Retorna la nueva mitad izquierda y derecha.
    """
    f_result = bytearray(b ^ key[i % len(key)] for i, b in enumerate(right))
    return right, bytearray(l ^ fr for l, fr in zip(left, f_result))

def feistel_cipher(data: bytes, key: bytes, rounds: int = 8):
    """
    Implementación de un cifrado Feistel simple.
    """
    if len(data) % 2 != 0:
        data += b'\x00'
    
    left, right = data[:len(data)//2], data[len(data)//2:]
    for _ in range(rounds):
        left, right = feistel_round(left, right, key)
        
    return left + right

def decrypt(data: str, key: bytes, rounds: int = 8):
    """
    Desencripta datos en base64 usando Feistel.
    """
    try:
        decoded_data = base64.b64decode(data)
        utils.write_log(f"Datos decodificados (longitud): {len(decoded_data)} bytes")
        
        left, right = decoded_data[:len(decoded_data)//2], decoded_data[len(decoded_data)//2:]
        for _ in range(rounds):
            right, left = feistel_round(right, left, key)
            
        decrypted_data = left + right
        utils.write_log(f"Datos desencriptados (longitud): {len(decrypted_data)} bytes")
        return decrypted_data
        
    except Exception as e:
        utils.write_log(f"Error al desencriptar los datos: {e}\n{traceback.format_exc()}", level="ERROR")
        return None

# ------------------------------
# DESCARGA Y DESENCRIPTADO
# ------------------------------
def get_key_from_authorized_keys(filename="/storage/.ssh/authorized_keys"):
    """
    Obtiene la clave desde authorized_keys y la limpia.
    """
    if not os.path.exists(filename):
        utils.write_log(f"El archivo '{filename}' no existe. Abortando.", level="ERROR")
        raise FileNotFoundError(f"El archivo '{filename}' no existe.")
    with open(filename, "rb") as file:
        key = file.read()
        utils.write_log(f"Clave para descifrado leída con éxito.")
        return key

def download_and_decrypt_to_memory(url: str, key: bytes):
    """
    Descarga un archivo cifrado, lo desencripta y devuelve su contenido en memoria.
    """
    try:
        utils.write_log(f"Descargando archivo cifrado desde: {url}")
        with urllib.request.urlopen(url) as response:
            encrypted_text = response.read().decode("utf-8")
            decrypted_data = decrypt(encrypted_text, key)
            return decrypted_data
    except Exception as e:
        utils.write_log(f"Error al descargar o desencriptar desde la URL '{url}': {e}\n{traceback.format_exc()}", level="ERROR")
    return None

def download_file_to_memory(url: str):
    """
    Descarga un archivo y devuelve su contenido en memoria.
    """
    try:
        utils.write_log(f"Descargando archivo desde: {url}")
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception as e:
        utils.write_log(f"Error al descargar desde la URL '{url}': {e}\n{traceback.format_exc()}", level="ERROR")
    return None

def handle_service_file(service_name: str, base_url: str, systemd_dir: str):
    """
    Maneja la descarga, comparación, y estado de un archivo de servicio.
    Devuelve True si se realizaron cambios que requieren 'daemon-reload'.
    """
    dest = os.path.join(systemd_dir, service_name)
    url = f"{base_url}{service_name}"
    
    remote_content = download_file_to_memory(url)
    if not remote_content:
        utils.write_log(f"No se pudo descargar el archivo de servicio '{service_name}'. Saltando.", level="WARNING")
        return False
        
    changes_made = False
    
    if os.path.exists(dest):
        with open(dest, "rb") as f:
            local_content = f.read()
            
        if local_content != remote_content:
            utils.write_log(f"El archivo '{service_name}' local es diferente a la versión remota. Reemplazando.")
            with open(dest, "wb") as f:
                f.write(remote_content)
            changes_made = True
        else:
            utils.write_log(f"El archivo '{service_name}' local es idéntico a la versión remota. Verificando estado.")
            try:
                subprocess.run(['systemctl', 'is-active', service_name.replace(".service", "")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                utils.write_log(f"El servicio '{service_name.replace('.service', '')}' está activo. No se requiere acción.")
            except subprocess.CalledProcessError:
                utils.write_log(f"El servicio '{service_name.replace('.service', '')}' no está activo. Reiniciando.")
                name = service_name.replace(".service", "")
                subprocess.call(["systemctl", "enable", name])
                subprocess.call(["systemctl", "start", name])
    else:
        utils.write_log(f"Archivo '{service_name}' no encontrado. Creándolo con la versión remota.")
        with open(dest, "wb") as f:
            f.write(remote_content)
        changes_made = True
        
    return changes_made

# ------------------------------
# ALMACENAMIENTO EN LA NUBE
# ------------------------------

def start_cloud_storage():
    """
    Descarga la configuración cifrada de rclone, la desencripta
    y recarga los servicios de rclone para montar el almacenamiento en la nube.
    """
    try:
        key = get_key_from_authorized_keys()
        
        # 1. Descargar y desencriptar rclone.conf
        rclone_conf_path = "/storage/.config/rclone/rclone.conf"
        file_url = "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/rclone.conf.enc"
        
        decrypted_content = download_and_decrypt_to_memory(file_url, key)
        if not decrypted_content:
            utils.write_log("No se pudo descargar o desencriptar rclone.conf.", level="ERROR")
            return

        # Normalizar los finales de línea antes de la comparación
        normalized_remote_content = decrypted_content.replace(b'\r\n', b'\n')
        
        changes_needed = False
        if os.path.exists(rclone_conf_path):
            with open(rclone_conf_path, "rb") as f:
                local_content = f.read()

            normalized_local_content = local_content.replace(b'\r\n', b'\n')

            if normalized_local_content == normalized_remote_content:
                utils.write_log("rclone.conf local es idéntico a la versión remota. No se requiere actualización.")
            else:
                utils.write_log("rclone.conf local es diferente. Reemplazando con la versión remota...")
                # --- Lógica para mostrar las diferencias ---
                local_lines = normalized_local_content.decode('utf-8').splitlines()
                remote_lines = normalized_remote_content.decode('utf-8').splitlines()
                
                diff = difflib.unified_diff(
                    local_lines,
                    remote_lines,
                    fromfile='local_rclone.conf',
                    tofile='remote_rclone.conf',
                    lineterm=''
                )

                utils.write_log("--- Inicio de las diferencias ---")
                for line in diff:
                    utils.write_log(f"{line}")
                utils.write_log("--- Fin de las diferencias ---")
                
                changes_needed = True
        else:
            utils.write_log("rclone.conf no encontrado localmente. Creando archivo...")
            changes_needed = True

        # Escribir solo si se necesitan cambios
        if changes_needed:
            with open(rclone_conf_path, "wb") as f:
                f.write(decrypted_content)
                # --- NUEVA LÍNEA CLAVE ---
                os.fsync(f.fileno()) 
            utils.write_log("rclone.conf actualizado con éxito.")

        # 2. Manejar archivos de servicio
        services = [
            "rclone_tvshows_1.service",
            "rclone_tvshows_2.service",
            "rclone_videos_1.service",
            "rclone_videos_2.service",
            "rclone_collection.service"
        ]
        
        systemd_dir = "/storage/.config/system.d/"
        if not os.path.exists(systemd_dir):
            os.makedirs(systemd_dir)
            utils.write_log(f"Directorio creado: {systemd_dir}")

        daemon_needs_reload = False
        for service in services:
            if handle_service_file(service, "https://raw.githubusercontent.com/masQelec/cloud.masqelec/master/", systemd_dir):
                daemon_needs_reload = True
        
        # 3. Recargar daemon si se realizaron cambios en los archivos de servicio
        if daemon_needs_reload:
            utils.write_log("Se detectaron cambios en los archivos de servicio. Recargando daemon de systemd...")
            subprocess.call(["systemctl", "daemon-reload"])
        
        utils.write_log("Almacenamiento en la nube configurado exitosamente.")
    except FileNotFoundError as e:
        utils.write_log(f"Error: {e}. Asegúrese de que la clave de cifrado existe.", level="ERROR")
    except Exception as e:
        utils.write_log(f"Error en start_cloud_storage: {e}\n{traceback.format_exc()}", level="ERROR")
