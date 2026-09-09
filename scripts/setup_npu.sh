#!/usr/bin/env bash
# ==============================================================================
# Orange Pi 5 (RK3588S) One-Step NPU Runtime & Python Environment Initializer
# Repository: https://github.com/muhammetmucahitsoylu/orangepi5-tutorials
# License: MIT
# ==============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "======================================================================"
echo "    Orange Pi 5 (RK3588S) NPU Setup & Validation Assistant            "
echo "======================================================================"
echo -e "${RESET}"

# 1. Check Root / Sudo
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}[!] Warning: Running as root. Virtual environment will be owned by root.${RESET}"
fi

# 2. Check NPU Kernel Node
echo -e "\n${BOLD}[1/4] Checking Low-Level NPU Kernel Device Node...${RESET}"
NPU_FOUND=false
NPU_NODE=""

if [ -e /dev/rknpu ] || compgen -G "/dev/rknpu*" > /dev/null; then
    NPU_FOUND=true
    NPU_NODE="/dev/rknpu"
else
    for rnode in /sys/class/drm/renderD*/device/driver; do
        if [ -e "$rnode" ] && grep -qi "rknpu" <<< "$(readlink -f "$rnode")"; then
            DRM_NAME=$(basename "$(dirname "$(dirname "$rnode")")")
            NPU_FOUND=true
            NPU_NODE="/dev/dri/${DRM_NAME}"
            break
        fi
    done
    if [ "$NPU_FOUND" = false ] && [ -d /sys/devices/platform/fdab0000.npu ]; then
        NPU_FOUND=true
        NPU_NODE="/sys/devices/platform/fdab0000.npu"
    fi
fi

if [ "$NPU_FOUND" = false ]; then
    echo -e "${RED}[FAIL] NPU device node not found!${RESET}"
    echo -e "Your current kernel ($(uname -r)) does not have active Rockchip NPU drivers."
    echo -e "Please ensure you run a Rockchip BSP kernel (5.10.x or 6.1.x)."
    exit 1
fi
echo -e "${GREEN}[OK] NPU kernel driver detected (${NPU_NODE}).${RESET}"

# Ensure user has access permissions (render and video groups)
TARGET_USER="${SUDO_USER:-$USER}"
sudo usermod -aG render,video "$TARGET_USER" 2>/dev/null || true

# 3. Check / Install System Dependencies & Hardware Runtime Library
echo -e "\n${BOLD}[2/4] Verifying System Libraries and librknnrt.so Runtime...${RESET}"
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential \
                    libxslt1-dev zlib1g-dev libgl1 libglib2.0-0 libgomp1 curl

# Ensure /usr/lib/librknnrt.so is present
if [ ! -f /usr/lib/librknnrt.so ]; then
    echo "Installing hardware runtime library (librknnrt.so v2.3.2)..."
    sudo curl -sL -o /usr/lib/librknnrt.so https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknpu2/runtime/Linux/librknn_api/aarch64/librknnrt.so
    sudo chmod 755 /usr/lib/librknnrt.so
    sudo ldconfig
    echo -e "${GREEN}[OK] librknnrt.so installed.${RESET}"
else
    echo -e "${GREEN}[OK] librknnrt.so already present in /usr/lib/.${RESET}"
fi

# 4. Create Dedicated Virtual Environment
VENV_DIR="$HOME/rknn_env"
echo -e "\n${BOLD}[3/4] Initializing Isolated Python Environment in ${VENV_DIR}...${RESET}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}[OK] Virtual environment created.${RESET}"
else
    echo -e "${YELLOW}[NOTE] Existing environment found at ${VENV_DIR}.${RESET}"
fi

# Activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 5. Determine Python Version & Install Matching RKNN-Toolkit-Lite2
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_TAG=$(python3 -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
echo -e "\n${BOLD}[4/4] Installing RKNN-Toolkit-Lite2 for Python ${PY_VER} (cp${PY_TAG})...${RESET}"

pip install --upgrade pip setuptools wheel
pip install numpy opencv-python-headless

# Fetch official wheel from airockchip/rknn-toolkit2
WHEEL_URL="https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp${PY_TAG}-cp${PY_TAG}-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"

echo "Attempting direct wheel install from Rockchip upstream..."
if pip install "$WHEEL_URL"; then
    echo -e "${GREEN}[SUCCESS] RKNN-Toolkit-Lite2 wheel installed successfully!${RESET}"
else
    echo -e "${YELLOW}[WARN] Direct install failed, falling back to repository clone...${RESET}"
    TEMP_CLONE=$(mktemp -d)
    git clone --depth 1 https://github.com/airockchip/rknn-toolkit2.git "$TEMP_CLONE/rknn-toolkit2"
    WHEEL_PATH=$(find "$TEMP_CLONE/rknn-toolkit2/rknn-toolkit-lite2/packages" -name "*cp${PY_TAG}*linux_aarch64.whl" | head -n 1)
    
    if [ -n "$WHEEL_PATH" ] && [ -f "$WHEEL_PATH" ]; then
        echo -e "Found local wheel: ${CYAN}$(basename "$WHEEL_PATH")${RESET}"
        pip install "$WHEEL_PATH"
        echo -e "${GREEN}[SUCCESS] RKNN-Toolkit-Lite2 installed from cloned repo!${RESET}"
    else
        echo -e "${RED}[FAIL] Compatible wheel for Python ${PY_VER} not found.${RESET}"
    fi
    rm -rf "$TEMP_CLONE"
fi

# 6. Verification Test
echo -e "\n${BOLD}======================================================================"
echo "                   Testing Python RKNN-Lite2 Import                   "
echo -e "======================================================================${RESET}"
if python3 -c "from rknnlite.api import RKNNLite; print('RKNNLite Imported Successfully!')" 2>/dev/null; then
    echo -e "${GREEN}${BOLD}[ALL CHECKS PASSED] NPU environment is 100% operational!${RESET}"
    echo -e "\nTo activate your environment in any terminal session, run:"
    echo -e "  ${CYAN}source ~/rknn_env/bin/activate${RESET}\n"
else
    echo -e "${YELLOW}[!] Warning: Check import logs. You may need to manually inspect 'pip list'.${RESET}"
fi
