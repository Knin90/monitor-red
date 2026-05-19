#!/usr/bin/env bash
# =============================================================
#  Monitor de Red - Instalador y lanzador (Bash)
#  Revisa las dependencias, las instala si faltan y arranca
#  el programa en Python.
# =============================================================

VERDE='\033[0;32m'
ROJO='\033[0;31m'
AMARILLO='\033[1;33m'
CIAN='\033[0;36m'
RESET='\033[0m'

# Carpeta donde esta este script (para ubicar monitor_red.py)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CIAN}=== Monitor de Red - Preparando el entorno ===${RESET}\n"

# --- 1. Verificar que Python 3 este instalado ---
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${ROJO}[ERROR]${RESET} Python 3 no esta instalado."
    echo -e "Instalalo con: ${AMARILLO}sudo apt install python3${RESET}"
    exit 1
fi
echo -e "${VERDE}[OK]${RESET} Python 3 encontrado: $(python3 --version)"

# --- 2. Revisar herramientas de red recomendadas ---
# Formato:  comando:paquete-apt
HERRAMIENTAS="ping:iputils-ping ip:iproute2 ss:iproute2 dig:dnsutils traceroute:traceroute whois:whois nmcli:network-manager"

FALTANTES=""
for ITEM in $HERRAMIENTAS; do
    CMD="${ITEM%%:*}"
    PKG="${ITEM##*:}"
    if command -v "$CMD" >/dev/null 2>&1; then
        echo -e "${VERDE}[OK]${RESET}    $CMD"
    else
        echo -e "${ROJO}[FALTA]${RESET} $CMD"
        # Evitar paquetes duplicados en la lista
        case " $FALTANTES " in
            *" $PKG "*) ;;
            *) FALTANTES="$FALTANTES $PKG" ;;
        esac
    fi
done

# --- 3. Ofrecer instalar lo que falte ---
if [ -n "$FALTANTES" ]; then
    echo ""
    echo -e "${AMARILLO}Faltan algunas herramientas:${RESET}$FALTANTES"
    read -r -p "Quieres instalarlas ahora con apt? (s/n): " RESP
    if [ "$RESP" = "s" ] || [ "$RESP" = "S" ]; then
        if command -v apt >/dev/null 2>&1; then
            sudo apt update && sudo apt install -y $FALTANTES
        else
            echo -e "${ROJO}[ERROR]${RESET} 'apt' no esta disponible."
            echo "Instala manualmente con tu gestor de paquetes:$FALTANTES"
        fi
    else
        echo -e "${AMARILLO}Continuando sin instalar (algunas opciones no funcionaran).${RESET}"
    fi
fi

# --- 4. Arrancar el programa ---
echo ""
echo -e "${CIAN}Iniciando Monitor de Red...${RESET}"
sleep 1
python3 "$DIR/monitor_red.py"
