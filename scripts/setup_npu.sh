#!/usr/bin/env bash
# ==============================================================================
# Orange Pi 5 (RK3588S) One-Step NPU Runtime & Python Environment Initializer
# Repository: https://github.com/muhammetmucahitsoylu/orangepi5-tutorials
# License: CC BY-NC-ND 4.0
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
if [ ! -e /dev/rknpu ] && ! compgen -G "/dev/rknpu*" > /dev/null; then
    echo -e "${RED}[FAIL] /dev/rknpu device node not found!${RESET}"
    echo -e "Your current kernel ($(uname -r)) does not have active Rockchip NPU drivers."
    echo -e "Please ensure you run a Rockchip BSP kernel (5.10.x or 6.1.x)."
    exit 1
fi
echo -e "${GREEN}[OK] /dev/rknpu kernel driver detected.${RESET}"

# 3. Check / Install System Dependencies
echo -e "\n${BOLD}[2/4] Verifying System Libraries (Python3, venv, gcc)...${RESET}"
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential \
                    libxslt1-dev zlib1g-dev libgl1 libglib2.0-0 libgomp1

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
echo -e "\n${BOLD}[4/4] Installing RKNN-Toolkit-Lite2 for Python ${PY_VER}...${RESET}"

pip install --upgrade pip setuptools wheel
pip install numpy opencv-python-headless

# Clone and install official RKNN-Toolkit-Lite2 wheel
TEMP_CLONE=$(mktemp -d)
echo "Cloning official Rockchip RKNPU2 repository (shallow clone)..."
git clone --depth 1 https://github.com/airockchip/rknpu2.git "$TEMP_CLONE/rknpu2"

WHEEL_PATH=$(find "$TEMP_CLONE/rknpu2/rknn-toolkit-lite2/packages" -name "*cp${PY_VER/./}*linux_aarch64.whl" | head -n 1)

if [ -n "$WHEEL_PATH" ] && [ -f "$WHEEL_PATH" ]; then
    echo -e "Found matching wheel: ${CYAN}$(basename "$WHEEL_PATH")${RESET}"
    pip install "$WHEEL_PATH"
    echo -e "${GREEN}[SUCCESS] RKNN-Toolkit-Lite2 installed successfully!${RESET}"
else
    echo -e "${YELLOW}[WARN] Exact wheel for Python ${PY_VER} not bundled. Installing latest generic or building from repo...${RESET}"
    pip install "$TEMP_CLONE/rknpu2/rknn-toolkit-lite2/packages/"*linux_aarch64.whl || true
fi

# Clean up temporary git clone
rm -rf "$TEMP_CLONE"

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
