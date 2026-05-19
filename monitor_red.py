#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import socket
import struct
import shutil
import subprocess
import urllib.request
import time
import io
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
#  COLORES PARA LA TERMINAL (codigos ANSI)
# ============================================================
class C:
    RESET = "\033[0m"
    NEGRITA = "\033[1m"
    ROJO = "\033[91m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    MAGENTA = "\033[95m"
    CIAN = "\033[96m"
    GRIS = "\033[90m"


# ============================================================
#  UTILIDADES GENERALES
# ============================================================
def limpiar():
    """Limpia la pantalla."""
    os.system("clear" if os.name != "nt" else "cls")


def pausa():
    """Espera a que el usuario presione Enter."""
    input(f"\n{C.GRIS}Presiona ENTER para volver al menu...{C.RESET}")


def titulo(texto):
    """Imprime un titulo de seccion con formato."""
    print(f"\n{C.NEGRITA}{C.CIAN}=== {texto} ==={C.RESET}\n")


def ok(texto):
    print(f"  {C.VERDE}[OK]{C.RESET} {texto}")


def err(texto):
    print(f"  {C.ROJO}[ERROR]{C.RESET} {texto}")


def info(texto):
    print(f"  {C.AZUL}[i]{C.RESET} {texto}")


def hay_herramienta(nombre):
    """Devuelve True si un comando existe en el sistema."""
    return shutil.which(nombre) is not None


def ejecutar(comando, timeout=30):
    """
    Ejecuta un comando del sistema y devuelve (exito, salida).
    'comando' puede ser una lista o un string.
    """
    try:
        resultado = subprocess.run(
            comando,
            shell=isinstance(comando, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        salida = (resultado.stdout or "") + (resultado.stderr or "")
        return resultado.returncode == 0, salida.strip()
    except subprocess.TimeoutExpired:
        return False, "El comando tardo demasiado y se cancelo."
    except FileNotFoundError:
        return False, "Comando no encontrado en el sistema."
    except Exception as e:
        return False, f"Error inesperado: {e}"


# ============================================================
#  SISTEMA DE REGISTRO (LOGS)
# ============================================================
CARPETA_LOGS = "logs"     # carpeta donde se guardan los registros
LOG_ACTIVO = True         # se puede activar/desactivar desde el menu (opcion 17)


_LIMPIAR_COLOR = re.compile(r"\033\[[0-9;]*m")


class Tee:
    """
    Objeto 'tipo archivo' que reenvia todo lo que se imprime a DOS
    destinos a la vez: la terminal (para que el usuario lo vea) y un
    buffer en memoria (para luego guardarlo en el archivo de log).

    El nombre 'Tee' viene del comando 'tee' de Linux, que hace lo mismo.
    """
    def __init__(self, terminal):
        self.terminal = terminal        # la salida real de la terminal
        self.buffer = io.StringIO()     # texto acumulado en memoria

    def write(self, texto):
        self.terminal.write(texto)      # se muestra en pantalla
        self.buffer.write(texto)        # se guarda para el log

    def flush(self):
        self.terminal.flush()

    def contenido(self):
        return self.buffer.getvalue()

_input_original = input


def input(prompt=""):
    """input mejorado: ademas de pedir el dato, anota la respuesta del
    usuario en el log cuando el registro esta capturando la salida."""
    respuesta = _input_original(prompt)
    if isinstance(sys.stdout, Tee):
        # el prompt ya quedo en el buffer; agregamos lo que el usuario tecleo
        sys.stdout.buffer.write(respuesta + "\n")
    return respuesta


def guardar_log(nombre_opcion, texto):
    """
    Anexa 'texto' a un archivo de log del dia, con fecha y hora.
    Cada dia genera su propio archivo: logs/monitor_AAAA-MM-DD.log
    Devuelve la ruta del archivo, o None si no habia nada que guardar.
    """
    if not texto.strip():
        return None
    os.makedirs(CARPETA_LOGS, exist_ok=True)
    ahora = datetime.now()
    archivo = os.path.join(CARPETA_LOGS,
                           f"monitor_{ahora.strftime('%Y-%m-%d')}.log")
    limpio = _LIMPIAR_COLOR.sub("", texto).rstrip()   # texto sin colores
    with open(archivo, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"[{ahora.strftime('%H:%M:%S')}]  {nombre_opcion}\n")
        f.write("=" * 60 + "\n")
        f.write(limpio + "\n")
    return archivo


# ============================================================
#  1. INTERFACES DE RED
# ============================================================
def ver_interfaces():
    titulo("INTERFACES DE RED")
    if hay_herramienta("ip"):
        exito, salida = ejecutar(["ip", "-brief", "addr"])
        if exito and salida:
            for linea in salida.splitlines():
                partes = linea.split()
                nombre = partes[0] if partes else "?"
                estado = partes[1] if len(partes) > 1 else "?"
                ips = " ".join(partes[2:]) if len(partes) > 2 else "(sin IP)"
                color = C.VERDE if estado.upper() == "UP" else C.GRIS
                print(f"  {C.NEGRITA}{nombre:<12}{C.RESET} "
                      f"{color}{estado:<8}{C.RESET} {ips}")
            return
    # Respaldo si no existe 'ip'
    if hay_herramienta("ifconfig"):
        exito, salida = ejecutar(["ifconfig"])
        if exito:
            print(salida)
            return
    err("No se encontro 'ip' ni 'ifconfig'.")


# ============================================================
#  2. IP LOCAL Y PUBLICA
# ============================================================
def obtener_ip_local():
    """Obtiene la IP local 'real' abriendo un socket de prueba."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


def obtener_ip_publica():
    """Consulta la IP publica a un servicio externo."""
    servicios = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]
    for url in servicios:
        try:
            with urllib.request.urlopen(url, timeout=6) as r:
                return r.read().decode().strip()
        except Exception:
            continue
    return None


def ver_ip():
    titulo("DIRECCIONES IP")
    local = obtener_ip_local()
    if local:
        ok(f"IP local:   {C.NEGRITA}{local}{C.RESET}")
    else:
        err("No se pudo determinar la IP local.")

    info("Consultando IP publica...")
    publica = obtener_ip_publica()
    if publica:
        ok(f"IP publica: {C.NEGRITA}{publica}{C.RESET}")
    else:
        err("No se pudo obtener la IP publica (revisa tu conexion).")

    try:
        ok(f"Hostname:   {socket.gethostname()}")
    except Exception:
        pass


# ============================================================
#  3. PING
# ============================================================
def hacer_ping():
    titulo("PING")
    host = input("  Host o IP a probar (ej. google.com): ").strip()
    if not host:
        err("No ingresaste ningun host.")
        return
    try:
        cantidad = int(input("  Cuantos paquetes enviar [4]: ").strip() or "4")
    except ValueError:
        cantidad = 4
    print()
    info(f"Haciendo ping a {host}...\n")
    exito, salida = ejecutar(["ping", "-c", str(cantidad), host], timeout=cantidad * 3 + 10)
    print(salida)
    print()
    if exito:
        ok("El host responde correctamente.")
    else:
        err("El host no respondio o no existe.")


def ping_continuo():
    titulo("PING CONTINUO")
    host = input("  Host o IP (Ctrl+C para detener): ").strip()
    if not host:
        err("No ingresaste ningun host.")
        return
    print()
    try:
        subprocess.run(["ping", host])
    except KeyboardInterrupt:
        print()
        info("Ping continuo detenido.")
    except FileNotFoundError:
        err("El comando 'ping' no esta disponible.")


# ============================================================
#  4. TRACEROUTE
# ============================================================
def traceroute():
    titulo("TRACEROUTE (ruta de los paquetes)")
    host = input("  Host o IP destino: ").strip()
    if not host:
        err("No ingresaste ningun host.")
        return
    herramienta = None
    for t in ("traceroute", "tracepath", "mtr"):
        if hay_herramienta(t):
            herramienta = t
            break
    if not herramienta:
        err("No hay traceroute/tracepath/mtr instalado.")
        info("Instala con: sudo apt install traceroute")
        return
    print()
    info(f"Trazando ruta hacia {host} con '{herramienta}'...\n")
    if herramienta == "mtr":
        subprocess.run(["mtr", "--report", host])
    else:
        exito, salida = ejecutar([herramienta, host], timeout=60)
        print(salida)


# ============================================================
#  5. DNS LOOKUP
# ============================================================
def dns_lookup():
    titulo("CONSULTA DNS")
    dominio = input("  Dominio o IP: ").strip()
    if not dominio:
        err("No ingresaste ningun dominio.")
        return
    print()
    # Resolucion basica con Python (siempre disponible)
    try:
        ip = socket.gethostbyname(dominio)
        ok(f"{dominio} -> {ip}")
    except socket.gaierror:
        err(f"No se pudo resolver '{dominio}'.")

    # DNS inverso
    try:
        nombre, _, _ = socket.gethostbyaddr(dominio)
        ok(f"DNS inverso: {nombre}")
    except Exception:
        pass

    # Registros completos con 'dig' si esta disponible
    if hay_herramienta("dig"):
        print(f"\n{C.GRIS}--- Registros DNS detallados (dig) ---{C.RESET}")
        for tipo in ("A", "AAAA", "MX", "NS", "TXT", "CNAME"):
            exito, salida = ejecutar(["dig", "+short", dominio, tipo])
            if exito and salida:
                print(f"  {C.AMARILLO}{tipo:<6}{C.RESET} {salida.replace(chr(10), ', ')}")
    else:
        info("Instala 'dnsutils' para ver registros MX, NS, TXT, etc.")


# ============================================================
#  6. WHOIS
# ============================================================
def consulta_whois():
    titulo("WHOIS (informacion de dominio)")
    dominio = input("  Dominio a consultar: ").strip()
    if not dominio:
        err("No ingresaste ningun dominio.")
        return
    if not hay_herramienta("whois"):
        err("'whois' no esta instalado.  Instala con: sudo apt install whois")
        return
    print()
    info(f"Consultando WHOIS de {dominio}...\n")
    exito, salida = ejecutar(["whois", dominio], timeout=30)
    # Mostramos solo lo mas util para no saturar la pantalla
    claves = ("domain", "registrar", "creation", "expir", "updated",
              "name server", "status", "registrant", "organization")
    lineas_utiles = [l for l in salida.splitlines()
                     if any(k in l.lower() for k in claves)]
    print("\n".join(lineas_utiles[:25]) if lineas_utiles else salida[:1500])


# ============================================================
#  7. ESCANEO DE PUERTOS  (Python puro, con sockets)
# ============================================================
PUERTOS_COMUNES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
}


def revisar_puerto(host, puerto, timeout=0.6):
    """Devuelve el puerto si esta abierto, o None."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        if s.connect_ex((host, puerto)) == 0:
            return puerto
    except Exception:
        pass
    finally:
        s.close()
    return None


def escanear_puertos():
    titulo("ESCANEO DE PUERTOS")
    host = input("  Host o IP a escanear: ").strip()
    if not host:
        err("No ingresaste ningun host.")
        return
    try:
        host_ip = socket.gethostbyname(host)
    except socket.gaierror:
        err(f"No se pudo resolver '{host}'.")
        return

    print(f"\n  1) Puertos comunes (rapido)")
    print(f"  2) Rango personalizado")
    opcion = input("  Elige [1]: ").strip() or "1"

    if opcion == "2":
        try:
            inicio = int(input("  Puerto inicial: ").strip())
            fin = int(input("  Puerto final: ").strip())
        except ValueError:
            err("Rango invalido.")
            return
        puertos = list(range(inicio, fin + 1))
    else:
        puertos = sorted(PUERTOS_COMUNES.keys())

    print()
    info(f"Escaneando {len(puertos)} puerto(s) en {host_ip}...\n")
    abiertos = []
    with ThreadPoolExecutor(max_workers=100) as pool:
        futuros = {pool.submit(revisar_puerto, host_ip, p): p for p in puertos}
        for f in as_completed(futuros):
            r = f.result()
            if r:
                abiertos.append(r)

    if abiertos:
        for p in sorted(abiertos):
            servicio = PUERTOS_COMUNES.get(p, "desconocido")
            print(f"  {C.VERDE}ABIERTO{C.RESET}  puerto {C.NEGRITA}{p:<6}{C.RESET} "
                  f"{C.GRIS}({servicio}){C.RESET}")
        print()
        ok(f"{len(abiertos)} puerto(s) abierto(s).")
    else:
        info("No se encontraron puertos abiertos.")


# ============================================================
#  8. CONEXIONES ACTIVAS
# ============================================================
def conexiones_activas():
    titulo("CONEXIONES DE RED ACTIVAS")
    if hay_herramienta("ss"):
        exito, salida = ejecutar(["ss", "-tunap"])
    elif hay_herramienta("netstat"):
        exito, salida = ejecutar(["netstat", "-tunap"])
    else:
        err("No hay 'ss' ni 'netstat' disponibles.")
        return
    if exito:
        lineas = salida.splitlines()
        for linea in lineas[:40]:
            print(f"  {linea}")
        if len(lineas) > 40:
            info(f"... y {len(lineas) - 40} conexiones mas.")
    else:
        err("No se pudo obtener la lista de conexiones.")


# ============================================================
#  9. TABLA ARP / DISPOSITIVOS CONOCIDOS
# ============================================================
def tabla_arp():
    titulo("TABLA ARP (dispositivos vistos en la red)")
    if hay_herramienta("ip"):
        exito, salida = ejecutar(["ip", "neigh"])
    elif hay_herramienta("arp"):
        exito, salida = ejecutar(["arp", "-a"])
    else:
        err("No hay 'ip' ni 'arp' disponibles.")
        return
    if exito and salida:
        for linea in salida.splitlines():
            print(f"  {linea}")
    else:
        info("Tabla ARP vacia. Prueba primero el escaneo de red local.")


# ============================================================
#  10. ESCANEO DE LA RED LOCAL  (descubrir dispositivos)
# ============================================================
def ping_host(ip):
    """Hace un ping rapido y devuelve la IP si responde."""
    exito, _ = ejecutar(["ping", "-c", "1", "-W", "1", ip], timeout=3)
    return ip if exito else None


def escanear_red_local():
    titulo("ESCANEO DE LA RED LOCAL")
    local = obtener_ip_local()
    if not local:
        err("No se pudo determinar tu IP local.")
        return
    base = ".".join(local.split(".")[:3])  # ej. 192.168.1
    info(f"Tu IP es {local}.  Escaneando {base}.1 - {base}.254 ...")
    print(f"  {C.GRIS}(esto puede tardar ~30 segundos){C.RESET}\n")

    objetivos = [f"{base}.{i}" for i in range(1, 255)]
    vivos = []
    with ThreadPoolExecutor(max_workers=120) as pool:
        for resultado in pool.map(ping_host, objetivos):
            if resultado:
                vivos.append(resultado)

    if not vivos:
        info("No se encontraron dispositivos (puede requerir permisos de root).")
        return

    # Intentamos resolver nombre y MAC de cada dispositivo
    print(f"  {C.NEGRITA}{'IP':<16}{'MAC':<20}{'NOMBRE'}{C.RESET}")
    print(f"  {C.GRIS}{'-'*52}{C.RESET}")
    for ip in sorted(vivos, key=lambda x: int(x.split('.')[-1])):
        # MAC desde la tabla ARP
        mac = "-"
        exito, salida = ejecutar(["ip", "neigh", "show", ip])
        if exito and "lladdr" in salida:
            try:
                mac = salida.split("lladdr")[1].split()[0]
            except Exception:
                pass
        # Nombre por DNS inverso
        try:
            nombre = socket.gethostbyaddr(ip)[0]
        except Exception:
            nombre = "(desconocido)"
        marca = f" {C.VERDE}<- tu equipo{C.RESET}" if ip == local else ""
        print(f"  {ip:<16}{mac:<20}{nombre}{marca}")
    print()
    ok(f"{len(vivos)} dispositivo(s) activo(s) en la red.")


# ============================================================
#  11. TEST DE VELOCIDAD
# ============================================================
def test_velocidad():
    titulo("TEST DE VELOCIDAD DE INTERNET")
    # Opcion 1: usar speedtest si esta instalado
    for cmd in ("speedtest", "speedtest-cli"):
        if hay_herramienta(cmd):
            info(f"Ejecutando '{cmd}' (esto tarda un poco)...\n")
            subprocess.run([cmd])
            return
    # Opcion 2: descarga de prueba con Python
    info("'speedtest-cli' no esta instalado. Usando prueba de descarga propia...\n")
    url = "https://speed.cloudflare.com/__down?bytes=25000000"  # 25 MB
    try:
        inicio = time.time()
        with urllib.request.urlopen(url, timeout=40) as r:
            descargado = 0
            while True:
                bloque = r.read(65536)
                if not bloque:
                    break
                descargado += len(bloque)
                transcurrido = time.time() - inicio
                if transcurrido > 0:
                    mbps = (descargado * 8) / (transcurrido * 1_000_000)
                    print(f"\r  Descargado: {descargado/1_000_000:5.1f} MB  |  "
                          f"Velocidad: {C.NEGRITA}{mbps:6.2f} Mbps{C.RESET}", end="")
        print()
        total = time.time() - inicio
        mbps = (descargado * 8) / (total * 1_000_000)
        ok(f"Velocidad de bajada estimada: {C.NEGRITA}{mbps:.2f} Mbps{C.RESET}")
    except Exception as e:
        err(f"No se pudo completar la prueba: {e}")
        info("Para una medicion mejor instala: sudo apt install speedtest-cli")


# ============================================================
#  12. ESTADISTICAS DE TRAFICO  (lee /proc/net/dev)
# ============================================================
def leer_trafico():
    """Devuelve un dict {interfaz: (bytes_rx, bytes_tx)}."""
    datos = {}
    try:
        with open("/proc/net/dev") as f:
            for linea in f.readlines()[2:]:
                nombre, valores = linea.split(":")
                campos = valores.split()
                datos[nombre.strip()] = (int(campos[0]), int(campos[8]))
    except Exception:
        pass
    return datos


def formato_bytes(n):
    """Convierte bytes a una unidad legible."""
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unidad}"
        n /= 1024
    return f"{n:.1f} PB"


def estadisticas_trafico():
    titulo("ESTADISTICAS DE TRAFICO POR INTERFAZ")
    datos = leer_trafico()
    if not datos:
        err("No se pudo leer /proc/net/dev (solo funciona en Linux).")
        return
    print(f"  {C.NEGRITA}{'INTERFAZ':<14}{'RECIBIDO':<16}{'ENVIADO'}{C.RESET}")
    print(f"  {C.GRIS}{'-'*40}{C.RESET}")
    for interfaz, (rx, tx) in datos.items():
        print(f"  {interfaz:<14}{formato_bytes(rx):<16}{formato_bytes(tx)}")

    print()
    if input("  Ver velocidad en vivo? (s/n) [n]: ").strip().lower() == "s":
        info("Mostrando velocidad en tiempo real (Ctrl+C para detener)...\n")
        try:
            anterior = leer_trafico()
            while True:
                time.sleep(1)
                actual = leer_trafico()
                lineas = []
                for interfaz in actual:
                    if interfaz in anterior:
                        rx = actual[interfaz][0] - anterior[interfaz][0]
                        tx = actual[interfaz][1] - anterior[interfaz][1]
                        if rx > 0 or tx > 0:
                            lineas.append(
                                f"  {interfaz:<12} "
                                f"{C.VERDE}v {formato_bytes(rx)}/s{C.RESET}   "
                                f"{C.AMARILLO}^ {formato_bytes(tx)}/s{C.RESET}")
                anterior = actual
                limpiar()
                titulo("VELOCIDAD EN VIVO  (Ctrl+C para salir)")
                print("\n".join(lineas) if lineas else "  (sin trafico)")
        except KeyboardInterrupt:
            print()
            info("Monitoreo detenido.")


# ============================================================
#  13. MONITOREO DE LATENCIA
# ============================================================
def monitoreo_latencia():
    titulo("MONITOREO DE LATENCIA")
    host = input("  Host a monitorear [8.8.8.8]: ").strip() or "8.8.8.8"
    info(f"Midiendo latencia hacia {host} (Ctrl+C para detener)...\n")
    tiempos = []
    perdidos = 0
    enviados = 0
    try:
        while True:
            enviados += 1
            exito, salida = ejecutar(["ping", "-c", "1", "-W", "2", host], timeout=4)
            ms = None
            if exito and "time=" in salida:
                try:
                    ms = float(salida.split("time=")[1].split()[0])
                    tiempos.append(ms)
                except Exception:
                    pass
            if ms is None:
                perdidos += 1

            # Barra visual sencilla segun la latencia
            if ms is None:
                barra = f"{C.ROJO}PERDIDO{C.RESET}"
            else:
                largo = min(int(ms / 5), 40)
                color = C.VERDE if ms < 50 else C.AMARILLO if ms < 150 else C.ROJO
                barra = f"{color}{'#' * largo}{C.RESET} {ms:.1f} ms"

            perdida = (perdidos / enviados) * 100
            prom = sum(tiempos) / len(tiempos) if tiempos else 0
            print(f"  #{enviados:<4} {barra}   "
                  f"{C.GRIS}[prom: {prom:.1f}ms | perdida: {perdida:.0f}%]{C.RESET}")
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        titulo("RESUMEN")
        if tiempos:
            ok(f"Minima:   {min(tiempos):.1f} ms")
            ok(f"Maxima:   {max(tiempos):.1f} ms")
            ok(f"Promedio: {sum(tiempos)/len(tiempos):.1f} ms")
        ok(f"Paquetes: {enviados} enviados, {perdidos} perdidos "
           f"({(perdidos/enviados)*100:.0f}% perdida)")


# ============================================================
#  14. INFORMACION WIFI
# ============================================================
def info_wifi():
    titulo("INFORMACION DE WIFI")
    if hay_herramienta("nmcli"):
        info("Redes WiFi detectadas:\n")
        exito, salida = ejecutar(
            ["nmcli", "-f", "SSID,SIGNAL,SECURITY,CHAN", "dev", "wifi"])
        print(salida if exito else "  No se pudo consultar.")
        print()
        info("Conexion activa:")
        exito, salida = ejecutar(["nmcli", "-t", "-f", "NAME,DEVICE,TYPE",
                                  "connection", "show", "--active"])
        print(f"  {salida}" if exito and salida else "  Sin conexion activa.")
    elif hay_herramienta("iwconfig"):
        exito, salida = ejecutar(["iwconfig"])
        print(salida if exito else "  No se pudo consultar.")
    else:
        err("No hay 'nmcli' ni 'iwconfig'.  Es posible que no uses WiFi.")
        info("En la mayoria de equipos: sudo apt install network-manager")


# ============================================================
#  17. REGISTROS GUARDADOS (LOGS)
# ============================================================
def ver_logs():
    global LOG_ACTIVO   # necesario para poder modificar la variable global
    titulo("REGISTROS GUARDADOS (LOGS)")

    estado = (f"{C.VERDE}ACTIVADO{C.RESET}" if LOG_ACTIVO
              else f"{C.ROJO}DESACTIVADO{C.RESET}")
    info(f"Guardado automatico de registros: {estado}")

    # Buscamos los archivos .log dentro de la carpeta de logs
    archivos = []
    if os.path.isdir(CARPETA_LOGS):
        archivos = sorted((a for a in os.listdir(CARPETA_LOGS)
                           if a.endswith(".log")), reverse=True)

    if not archivos:
        info("Todavia no hay registros guardados.")
    else:
        print(f"\n  Archivos en la carpeta '{CARPETA_LOGS}/':\n")
        for i, nombre in enumerate(archivos, 1):
            tam = os.path.getsize(os.path.join(CARPETA_LOGS, nombre))
            print(f"   {C.NEGRITA}{i}{C.RESET}) {nombre}  "
                  f"{C.GRIS}({formato_bytes(tam)}){C.RESET}")

        eleccion = input("\n  Numero del archivo a ver (Enter para omitir): ").strip()
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(archivos):
            ruta = os.path.join(CARPETA_LOGS, archivos[int(eleccion) - 1])
            print(f"\n{C.GRIS}{'-' * 60}{C.RESET}")
            with open(ruta, encoding="utf-8") as f:
                print(f.read().rstrip())
            print(f"{C.GRIS}{'-' * 60}{C.RESET}")

    # Permite activar o desactivar el guardado automatico
    if input("\n  Cambiar el guardado automatico? (s/n): ").strip().lower() == "s":
        LOG_ACTIVO = not LOG_ACTIVO
        ok(f"Guardado automatico {'activado' if LOG_ACTIVO else 'desactivado'}.")


# ============================================================
#  REVISION DE DEPENDENCIAS
# ============================================================
def revisar_dependencias():
    titulo("REVISION DEL SISTEMA")
    herramientas = {
        "ping": "Pruebas de conectividad (esencial)",
        "ip": "Interfaces y rutas (esencial)",
        "ss": "Conexiones activas",
        "dig": "Consultas DNS detalladas (dnsutils)",
        "traceroute": "Ruta de paquetes",
        "whois": "Informacion de dominios",
        "nmcli": "Gestion de WiFi (network-manager)",
        "speedtest-cli": "Test de velocidad preciso",
    }
    faltantes = []
    for cmd, desc in herramientas.items():
        if hay_herramienta(cmd):
            print(f"  {C.VERDE}[OK]{C.RESET}     {cmd:<16}{C.GRIS}{desc}{C.RESET}")
        else:
            print(f"  {C.ROJO}[FALTA]{C.RESET}  {cmd:<16}{C.GRIS}{desc}{C.RESET}")
            faltantes.append(cmd)
    if faltantes:
        print()
        info("Para instalar lo que falta (Debian/Ubuntu):")
        paquetes = {"dig": "dnsutils", "nmcli": "network-manager",
                    "speedtest-cli": "speedtest-cli"}
        lista = sorted({paquetes.get(c, c) for c in faltantes})
        print(f"  {C.AMARILLO}sudo apt install {' '.join(lista)}{C.RESET}")
    else:
        print()
        ok("Todas las herramientas estan instaladas.")


# ============================================================
#  MENU PRINCIPAL
# ============================================================
def banner():
    print(f"""{C.CIAN}{C.NEGRITA}
   __  __             _ _              _      ____           _
  |  \\/  | ___  _ __ (_) |_ ___  _ __ | |    |  _ \\ ___  __| |
  | |\\/| |/ _ \\| '_ \\| | __/ _ \\| '__|| |    | |_) / _ \\/ _` |
  | |  | | (_) | | | | | || (_) | |   |_|    |  _ <  __/ (_| |
  |_|  |_|\\___/|_| |_|_|\\__\\___/|_|   (_)    |_| \\_\\___|\\__,_|
{C.RESET}{C.GRIS}{C.RESET}""")


OPCIONES = {
    "1": ("Ver interfaces de red", ver_interfaces),
    "2": ("Ver IP local y publica", ver_ip),
    "3": ("Hacer ping a un host", hacer_ping),
    "4": ("Ping continuo", ping_continuo),
    "5": ("Traceroute (ruta de paquetes)", traceroute),
    "6": ("Consulta DNS (lookup)", dns_lookup),
    "7": ("WHOIS de un dominio", consulta_whois),
    "8": ("Escaneo de puertos", escanear_puertos),
    "9": ("Conexiones activas", conexiones_activas),
    "10": ("Tabla ARP", tabla_arp),
    "11": ("Escanear dispositivos de la red local", escanear_red_local),
    "12": ("Test de velocidad de internet", test_velocidad),
    "13": ("Estadisticas de trafico", estadisticas_trafico),
    "14": ("Monitoreo de latencia en vivo", monitoreo_latencia),
    "15": ("Informacion de WiFi", info_wifi),
    "16": ("Revisar dependencias del sistema", revisar_dependencias),
    "17": ("Registros guardados (logs)", ver_logs),
}


def mostrar_menu():
    limpiar()
    banner()
    print(f"\n  {C.AMARILLO}-- DIAGNOSTICO --{C.RESET}")
    for k in ("1", "2", "3", "4", "5", "6", "7"):
        print(f"   {C.NEGRITA}{k:>2}{C.RESET}) {OPCIONES[k][0]}")
    print(f"\n  {C.AMARILLO}-- ANALISIS Y MONITOREO --{C.RESET}")
    for k in ("8", "9", "10", "11", "12", "13", "14", "15"):
        print(f"   {C.NEGRITA}{k:>2}{C.RESET}) {OPCIONES[k][0]}")
    print(f"\n  {C.AMARILLO}-- SISTEMA --{C.RESET}")
    for k in ("16", "17"):
        print(f"   {C.NEGRITA}{k:>2}{C.RESET}) {OPCIONES[k][0]}")
    print(f"   {C.NEGRITA} 0{C.RESET}) {C.ROJO}Salir{C.RESET}")


def main():
    if os.name == "nt":
        print("Este programa esta pensado para Linux.")
        return
    try:
        while True:
            mostrar_menu()
            opcion = input(f"\n  {C.CIAN}Elige una opcion:{C.RESET} ").strip()
            if opcion == "0":
                print(f"\n  {C.VERDE}Hasta luego!{C.RESET}\n")
                break
            elif opcion in OPCIONES:
                limpiar()
                banner()
                # Activamos el "Tee": a partir de aqui todo lo que se
                # imprima se mostrara en pantalla Y se guardara en memoria.
                salida_real = sys.stdout
                sys.stdout = Tee(salida_real)
                try:
                    OPCIONES[opcion][1]()
                except KeyboardInterrupt:
                    print(f"\n  {C.GRIS}Operacion cancelada.{C.RESET}")
                except Exception as e:
                    err(f"Ocurrio un error: {e}")
                finally:
                    # Recuperamos lo capturado y restauramos la salida normal
                    capturado = sys.stdout.contenido()
                    sys.stdout = salida_real
                # Guardamos el log (no registramos el visor de logs en si mismo)
                if LOG_ACTIVO and opcion != "17":
                    archivo = guardar_log(OPCIONES[opcion][0], capturado)
                    if archivo:
                        print(f"  {C.GRIS}(registro guardado en {archivo}){C.RESET}")
                pausa()
            else:
                print(f"  {C.ROJO}Opcion no valida.{C.RESET}")
                time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n  {C.VERDE}Programa cerrado. Hasta luego!{C.RESET}\n")


if __name__ == "__main__":
    main()
