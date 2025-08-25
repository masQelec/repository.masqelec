import os
import xml.etree.ElementTree as ET
import stat
import time
from . import utils

SETTINGS_FILE = "/storage/.kodi/userdata/guisettings.xml"

# Código bash que queremos asegurar en autostart.sh
BASH_BLOCK = """# --- Fix Kodi Webserver ---
GUISETTINGS="/storage/.kodi/userdata/guisettings.xml"

if [ -f "$GUISETTINGS" ]; then
    echo "✔ Verificando configuración de webserver en $GUISETTINGS"

    # Caso 1: Desactivado → activarlo
    if grep -q '<setting id="services.webserver"[^>]*>false</setting>' "$GUISETTINGS"; then
        sed -i 's#<setting id="services.webserver"[^>]*>false</setting>#<setting id="services.webserver">true</setting>#' "$GUISETTINGS"
        echo "Se corrigió: estaba en false → ahora true"
    fi

    # Caso 2: Con default → eliminar atributo
    if grep -q '<setting id="services.webserver" default="true">true</setting>' "$GUISETTINGS"; then
        sed -i 's#<setting id="services.webserver" default="true">true</setting>#<setting id="services.webserver">true</setting>#' "$GUISETTINGS"
        echo "Se corrigió: eliminado atributo default"
    fi

    # Caso 3: No existe → agregarlo
    if ! grep -q '<setting id="services.webserver">true</setting>' "$GUISETTINGS"; then
        sed -i 's#</settings>#<setting id="services.webserver">true</setting>\\n</settings>#' "$GUISETTINGS"
        echo "Parámetro agregado."
    fi
else
    echo "No se encontró $GUISETTINGS"
fi
# --- End Fix Kodi Webserver ---
"""
AUTOSTART_PATH = "/storage/.config/autostart.sh"


def is_webserver_enabled():
    """Verifica si el servidor web está activado en guisettings.xml."""
    if not os.path.exists(SETTINGS_FILE):
        utils.write_log(f"No se encontró el archivo: {SETTINGS_FILE}", level="WARNING")
        return False

    try:
        tree = ET.parse(SETTINGS_FILE)
    except ET.ParseError as e:
        utils.write_log(f"Error al leer XML: {e}", level="ERROR")
        return False

    root = tree.getroot()
    elem = root.find(".//setting[@id='services.webserver']")
    if elem is None:
        utils.write_log("No se encontró la entrada 'services.webserver' en el archivo.", level="INFO")
        return False
        
    return elem.text == "true"


def ensure_autostart():
    """Asegura que el bloque de código para arreglar el webserver esté en autostart.sh."""
    needs_reboot = False

    # Caso 1: No existe autostart.sh → crearlo con bloque completo
    if not os.path.exists(AUTOSTART_PATH):   
        utils.write_log(f"⚠ No existe {AUTOSTART_PATH}, creando...", level="WARNING")
        with open(AUTOSTART_PATH, "w") as f:
            f.write("#!/bin/bash\n" + BASH_BLOCK + "\n")
        os.chmod(AUTOSTART_PATH, os.stat(AUTOSTART_PATH).st_mode | stat.S_IEXEC)
        utils.write_log("autostart.sh creado con permisos de ejecución.")
        needs_reboot = True
    else:
        # Caso 2: Existe → leer contenido
        with open(AUTOSTART_PATH, "r") as f:
            content = f.read()

        # Verificar si comienza con #!/bin/bash
        if not content.startswith("#!/bin/bash"):
            utils.write_log("⚠ El archivo no comienza con #!/bin/bash → reescribiendo con bloque completo.", level="WARNING")
            with open(AUTOSTART_PATH, "w") as f:
                f.write("#!/bin/bash\n" + BASH_BLOCK + "\n")
            needs_reboot = True
        else:
            # Si ya existe el bloque, no hacer nada
            if "Fix Kodi Webserver" in content:
                utils.write_log("El bloque ya existe en autostart.sh, no se modifica.")
            else:
                utils.write_log("⚠ El bloque no está en autostart.sh, agregando al final...", level="WARNING")
                with open(AUTOSTART_PATH, "a") as f:
                    f.write("\n" + BASH_BLOCK + "\n")
                needs_reboot = True

    # Asegurar permisos de ejecución
    os.chmod(AUTOSTART_PATH, os.stat(AUTOSTART_PATH).st_mode | stat.S_IEXEC)
    utils.write_log("autostart.sh actualizado y con permisos de ejecución.")

    # Reiniciar solo si se realizaron cambios
    if needs_reboot:
        utils.notify_user("Configuración actualizada, se va a reiniciar el sistema")
        time.sleep(5) # Pausa de 3 segundos
        os.system('reboot')
