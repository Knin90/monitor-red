# 🌐 Monitor de Red

Herramienta de monitoreo y diagnóstico de red para terminal Linux.
Menú interactivo con 17 opciones. Hecha en **Python · Bash · Linux**.

---

## 📋 Tabla de contenidos

1. [¿Qué hace este programa?](#qué-hace-este-programa)
2. [Requisitos](#requisitos)
3. [Instalación](#instalación)
4. [Cómo ejecutarlo](#cómo-ejecutarlo)
5. [Guía de cada opción del menú](#guía-de-cada-opción-del-menú)
6. [Sistema de registros (logs)](#sistema-de-registros-logs)
7. [Estructura del proyecto](#estructura-del-proyecto)
8. [Preguntas frecuentes](#preguntas-frecuentes)

---

## ¿Qué hace este programa?

Un menú en la terminal con 17 herramientas de red organizadas en tres grupos:

```
-- DIAGNÓSTICO --          -- ANÁLISIS Y MONITOREO --     -- SISTEMA --
 1) Interfaces de red       8) Escaneo de puertos         16) Dependencias
 2) IP local y pública      9) Conexiones activas         17) Logs guardados
 3) Ping                   10) Tabla ARP
 4) Ping continuo          11) Escaneo de red local
 5) Traceroute             12) Test de velocidad
 6) DNS lookup             13) Estadísticas de tráfico
 7) WHOIS                  14) Monitoreo de latencia
                           15) Información de WiFi
```

---

## Requisitos

- **Linux** (probado en Ubuntu / Debian)
- **Python 3.6** o superior

Comprueba que los tienes con:

```bash
python3 --version
```

Las herramientas del sistema (`ping`, `dig`, `traceroute`, etc.) son **opcionales**.
El programa funciona sin ellas y te avisa qué instalar cuando las necesita.

---

## Instalación

### Opción A — Clonar desde GitHub (recomendado)

```bash
git clone https://github.com/tu-usuario/monitor-red.git
cd monitor-red
```

### Opción B — Descargar el ZIP

En GitHub haz clic en el botón verde **Code → Download ZIP**.
Luego descomprime y entra a la carpeta:

```bash
unzip monitor-red-main.zip
cd monitor-red-main
```

### Instalar dependencias del sistema (opcional pero recomendado)

El script `instalar.sh` las revisa y ofrece instalarlas automáticamente:

```bash
bash instalar.sh
```

O instálalas manualmente:

```bash
sudo apt update
sudo apt install iproute2 iputils-ping dnsutils traceroute whois network-manager
```

---

## Cómo ejecutarlo

### Forma recomendada (usa el lanzador Bash)

```bash
bash instalar.sh
```

Revisa las dependencias, instala las que falten y arranca el programa.

### Forma directa

```bash
python3 monitor_red.py
```

### Con permisos de administrador

Algunas opciones (escaneo de red local, tabla ARP) muestran más información
ejecutándose como root:

```bash
sudo python3 monitor_red.py
```

---

## Guía de cada opción del menú

---

### 🔵 DIAGNÓSTICO

---

#### 1) Ver interfaces de red

Muestra todas las interfaces del equipo (ethernet, WiFi, loopback) con su
dirección IP y si están activas o no.

```
Cuándo usarla: cuando quieras saber qué interfaces tienes y cuál
está conectada en este momento.
```

Ejemplo de salida:
```
  eth0         UP       192.168.1.10/24
  lo           UNKNOWN  127.0.0.1/8
  wlan0        DOWN
```

---

#### 2) Ver IP local y pública

Muestra dos cosas distintas:

- **IP local:** la dirección dentro de tu red (la que ven tu router y tus
  dispositivos). Suele ser algo como `192.168.1.x`.
- **IP pública:** la que el resto de internet ve cuando te conectas. Sale
  consultando un servicio externo.
- **Hostname:** el nombre de tu equipo en la red.

```
Cuándo usarla: cuando alguien te pida tu IP, o para saber si tu
conexión a internet está funcionando.
```

---

#### 3) Hacer ping a un host

Envía paquetes a un host y mide cuánto tardan en volver. Te dice si el
host responde y en cuánto tiempo.

```
Cuándo usarla: para comprobar si un servidor, página o dispositivo
está alcanzable desde tu red.
```

Pasos:
1. Escribe el host o IP (ej. `google.com` o `192.168.1.1`)
2. Escribe cuántos paquetes enviar (por defecto 4)
3. El resultado muestra el tiempo en milisegundos y si hubo pérdida

Interpretar resultados:
```
< 20 ms    → Excelente (red local o servidor cercano)
20-100 ms  → Normal para internet
> 200 ms   → Lento, puede haber problemas
Perdida    → El host no responde o está bloqueado
```

---

#### 4) Ping continuo

Igual que el ping normal pero sin parar, hasta que presiones `Ctrl+C`.
Útil para monitorear si una conexión es estable o si cae en algún momento.

```
Cuándo usarla: cuando sospeches que la red se cae intermitentemente
y quieras atraparlo en el momento.
```

---

#### 5) Traceroute (ruta de los paquetes)

Muestra todos los "saltos" que da un paquete desde tu equipo hasta el
destino: router, proveedores de internet, servidores intermedios.

```
Cuándo usarla: cuando el ping falla y quieres saber en qué punto
exacto se corta la conexión.
```

Ejemplo de salida:
```
 1  192.168.1.1       1.2 ms   (tu router)
 2  10.0.0.1          8.4 ms   (tu proveedor de internet)
 3  72.14.209.81     12.1 ms
 4  google.com        14.3 ms
```

Requiere `traceroute` instalado:
```bash
sudo apt install traceroute
```

---

#### 6) Consulta DNS

Resuelve un dominio a su dirección IP y muestra todos sus registros DNS.

```
Cuándo usarla: para verificar a qué IP apunta un dominio, o para
revisar su configuración de correo (registros MX).
```

Qué muestra:

| Registro | Significado |
|---|---|
| A | IP del servidor (IPv4) |
| AAAA | IP del servidor (IPv6) |
| MX | Servidores de correo |
| NS | Servidores de nombre |
| TXT | Verificaciones, SPF, DKIM |
| CNAME | Alias de otro dominio |

Requiere `dig` para los registros detallados:
```bash
sudo apt install dnsutils
```

---

#### 7) WHOIS

Muestra información sobre quién registró un dominio: empresa registrante,
fechas de creación y vencimiento, servidores de nombre.

```
Cuándo usarla: para saber cuándo vence un dominio, quién es el dueño
o qué empresa lo registró.
```

Requiere `whois`:
```bash
sudo apt install whois
```

---

### 🟡 ANÁLISIS Y MONITOREO

---

#### 8) Escaneo de puertos

Revisa qué puertos de un host están abiertos y qué servicio suele
correr en cada uno.

```
Cuándo usarla: para ver qué servicios tiene activos un servidor,
o para revisar tu propio equipo.
```

Dos modos:
- **Puertos comunes (rápido):** revisa los ~20 puertos más usados
  (HTTP, SSH, FTP, MySQL, etc.)
- **Rango personalizado:** tú eliges los puertos de inicio y fin

Puertos importantes:
```
22   → SSH (acceso remoto)
80   → HTTP (web sin cifrar)
443  → HTTPS (web cifrada)
3306 → MySQL (base de datos)
3389 → RDP (escritorio remoto Windows)
```

> ⚠️ Solo escanea equipos que son tuyos o para los que tienes permiso.

---

#### 9) Conexiones activas

Lista todas las conexiones de red abiertas en tu equipo en este momento:
qué programa las abrió, a qué IP conecta y en qué puerto.

```
Cuándo usarla: si sospechas que algo se está conectando a internet
sin que tú lo hayas pedido.
```

---

#### 10) Tabla ARP

Muestra los dispositivos que tu equipo conoce en la red local, con su
dirección IP y su dirección MAC (identificador único de red).

```
Cuándo usarla: para identificar qué dispositivos están en tu red
o para encontrar la MAC de un equipo específico.
```

> Si la tabla sale vacía, primero usa la opción 11 para que tu equipo
> descubra los dispositivos cercanos.

---

#### 11) Escanear dispositivos de la red local

Hace un barrido completo de tu red (ej. `192.168.1.1` a `192.168.1.254`)
enviando pings a cada dirección posible. Muestra los dispositivos que
responden, su MAC y su nombre si está disponible.

```
Cuándo usarla: para ver todos los dispositivos conectados a tu red
(computadores, teléfonos, impresoras, smart TVs, etc.)
```

> Puede tardar ~30 segundos. Funciona mejor con `sudo`.

---

#### 12) Test de velocidad de internet

Mide la velocidad de descarga de tu conexión a internet.

```
Cuándo usarla: cuando sientas que internet está lento y quieras
tener un número concreto.
```

Si tienes `speedtest-cli` instalado lo usa (más preciso). Si no, descarga
un archivo de prueba y calcula la velocidad.

```bash
sudo apt install speedtest-cli
```

---

#### 13) Estadísticas de tráfico

Muestra cuántos datos han pasado por cada interfaz de red desde que
arrancó el sistema. Tiene un modo en vivo que actualiza cada segundo.

```
Cuándo usarla: para saber qué interfaz está usando más tráfico,
o para monitorear el consumo de datos en tiempo real.
```

Presiona `Ctrl+C` para detener el modo en vivo.

---

#### 14) Monitoreo de latencia en vivo

Hace pings continuos a un host y muestra una barra visual según la
latencia. Al terminar con `Ctrl+C` muestra resumen con mínima, máxima,
promedio y porcentaje de pérdida.

```
Cuándo usarla: para monitorear la calidad de tu conexión durante
un período de tiempo (mientras juegas, trabajas, etc.)
```

Escala de colores:
```
Verde    → menos de 50 ms   (excelente)
Amarillo → 50 a 150 ms      (aceptable)
Rojo     → más de 150 ms    (lento)
```

---

#### 15) Información de WiFi

Muestra las redes WiFi detectadas con su señal y seguridad, y cuál es
la red a la que estás conectado actualmente.

```
Cuándo usarla: para ver la intensidad de señal de las redes cercanas
o verificar a qué red estás conectado.
```

Requiere `nmcli`:
```bash
sudo apt install network-manager
```

---

### ⚙️ SISTEMA

---

#### 16) Revisar dependencias del sistema

Revisa cuáles herramientas externas están instaladas y cuáles faltan,
con el comando exacto para instalar lo que falta.

```
Cuándo usarla: cuando una opción diga que falta alguna herramienta,
o para revisar el estado general del sistema de un vistazo.
```

---

#### 17) Registros guardados (logs)

Muestra los archivos de log guardados, permite ver el contenido de
cualquiera y activar o desactivar el guardado automático.

```
Cuándo usarla: para revisar resultados de ejecuciones anteriores
o para apagar el registro si no lo necesitas.
```

---

## Sistema de registros (logs)

Cada vez que usas una herramienta del menú, el resultado se guarda
automáticamente en la carpeta `logs/` con la fecha y hora exacta.

Estructura de los archivos:
```
logs/
├── monitor_2026-05-19.log
├── monitor_2026-05-20.log
└── monitor_2026-05-21.log
```

Cada día genera su propio archivo. Dentro, cada ejecución queda así:
```
============================================================
[14:32:01]  Hacer ping a un host
============================================================
Host o IP a probar: google.com
Cuantos paquetes: 4

PING google.com (142.250.x.x) 56 bytes of data.
64 bytes from ... time=12.3 ms

  [OK] El host responde correctamente.
```

> Los archivos de log **no se suben a GitHub**. La carpeta `logs/`
> está en el `.gitignore` del proyecto.

---

## Estructura del proyecto

```
monitor-red/
├── monitor_red.py   ← El programa principal (Python)
├── instalar.sh      ← Lanzador y verificador de dependencias (Bash)
├── README.md        ← Esta guía
├── .gitignore       ← Archivos que Git ignora
└── logs/            ← Registros automáticos (no se sube a GitHub)
    └── monitor_AAAA-MM-DD.log
```

---


*Proyecto desarrollado en Python · Bash · Linux*
