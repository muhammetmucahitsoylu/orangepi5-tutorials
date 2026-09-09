#!/usr/bin/env bash
# ==============================================================================
# Orange Pi 5 (RK3588 / RK3588S) Hardware & System Diagnostics Tool
# Repository: https://github.com/muhammetmucahitsoylu/orangepi5-tutorials
# License: MIT
# ==============================================================================

# ANSI Color Codes
BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "  ___                               ____  _   ____ "
echo " / _ \ _ __ __ _ _ __   __ _  ___  |  _ \(_) | ___|"
echo "| | | | '__/ _\` | '_ \ / _\` |/ _ \ | |_) | | |___ \ "
echo "| |_| | | | (_| | | | | (_| |  __/ |  __/| |  ___) |"
echo " \___/|_|  \__,_|_| |_|\__, |\___| |_|   |_| |____/ "
echo "                       |___/                        "
echo -e "${RESET}"
echo -e "${BOLD}Orange Pi 5 (RK3588S) Hardware & Subsystem Diagnostic Utility${RESET}"
echo -e "Community Knowledge Base: ${CYAN}https://github.com/muhammetmucahitsoylu/orangepi5-tutorials${RESET}"
echo "----------------------------------------------------------------------"

# 1. Hardware Model & SoC Detection
echo -e "\n${BOLD}[1/7] Board & SoC Identification${RESET}"
if [ -f /proc/device-tree/model ]; then
    BOARD_MODEL=$(tr -d '\0' < /proc/device-tree/model)
    echo -e "  Board Model      : ${GREEN}${BOARD_MODEL}${RESET}"
else
    echo -e "  Board Model      : ${YELLOW}Unknown (Device tree not available)${RESET}"
fi

SOC_TYPE=$(grep -m1 "Hardware" /proc/cpuinfo 2>/dev/null | awk -F': ' '{print $2}')
if [ -z "$SOC_TYPE" ]; then
    SOC_TYPE=$(grep -m1 "model name" /proc/cpuinfo | awk -F': ' '{print $2}')
fi
echo -e "  SoC Architecture : ${CYAN}Rockchip RK3588/RK3588S (${SOC_TYPE:-ARMv8})${RESET}"

KERNEL_VER=$(uname -r)
echo -e "  Linux Kernel     : ${BOLD}${KERNEL_VER}${RESET}"
if [[ "$KERNEL_VER" =~ 5\.10 ]] || [[ "$KERNEL_VER" =~ 6\.1 ]]; then
    echo -e "  Kernel Type      : ${GREEN}Rockchip BSP Branch (Optimal for NPU/VPU/GPU)${RESET}"
else
    echo -e "  Kernel Type      : ${YELLOW}Mainline / Custom (NPU/VPU might require custom out-of-tree drivers)${RESET}"
fi

# 2. CPU Core Frequencies & Governor Status
echo -e "\n${BOLD}[2/7] CPU Topology & DVFS Governors${RESET}"
CPU_COUNT=$(nproc)
echo -e "  Active Cores     : ${GREEN}${CPU_COUNT} Cores${RESET} (4x Cortex-A76 + 4x Cortex-A55)"

for policy in /sys/devices/system/cpu/cpufreq/policy*; do
    if [ -d "$policy" ]; then
        PID=$(basename "$policy")
        CURR_FREQ=$(cat "$policy/scaling_cur_freq" 2>/dev/null || echo "0")
        CURR_MHZ=$((CURR_FREQ / 1000))
        MAX_FREQ=$(cat "$policy/scaling_max_freq" 2>/dev/null || echo "0")
        MAX_MHZ=$((MAX_FREQ / 1000))
        GOV=$(cat "$policy/scaling_governor" 2>/dev/null || echo "unknown")
        
        if [ "$GOV" = "performance" ]; then
            GOV_COLOR="${GREEN}"
        else
            GOV_COLOR="${YELLOW}"
        fi
        echo -e "  ${PID} : ${CURR_MHZ} MHz / Max ${MAX_MHZ} MHz | Governor: ${GOV_COLOR}${GOV}${RESET}"
    fi
done

# 3. Thermal Telemetry & Throttling
echo -e "\n${BOLD}[3/7] Thermal Sensors & Operating Temperatures${RESET}"
TEMP_ALERT=false
for tz in /sys/class/thermal/thermal_zone*; do
    if [ -d "$tz" ]; then
        TZ_TYPE=$(cat "$tz/type" 2>/dev/null || echo "thermal")
        RAW_TEMP=$(cat "$tz/temp" 2>/dev/null || echo "0")
        DEGREE=$(LC_ALL=C awk "BEGIN {printf \"%.1f\", $RAW_TEMP / 1000}")
        INT_DEGREE=${DEGREE%.*}
        
        if [ "$INT_DEGREE" -ge 80 ]; then
            COLOR="${RED}"
            TEMP_ALERT=true
        elif [ "$INT_DEGREE" -ge 65 ]; then
            COLOR="${YELLOW}"
        else
            COLOR="${GREEN}"
        fi
        printf "  %-22s : ${COLOR}%5.1f °C${RESET}\n" "$TZ_TYPE" "$DEGREE"
    fi
done

if [ "$TEMP_ALERT" = true ]; then
    echo -e "  ${RED}${BOLD}[WARN] High die temperature detected! Thermal throttling may degrade performance. Ensure an active fan is running.${RESET}"
else
    echo -e "  ${GREEN}[OK] Thermal levels are within optimal operational bounds.${RESET}"
fi

# 4. Neural Processing Unit (NPU - 6 TOPS) & Version Pinning
echo -e "\n${BOLD}[4/7] NPU (Rockchip 6 TOPS Tri-Core) & Stack Alignment${RESET}"
NPU_FOUND=false
NPU_NODE=""

if [ -e /dev/rknpu ] || compgen -G "/dev/rknpu*" > /dev/null; then
    NPU_FOUND=true
    NPU_NODE="/dev/rknpu (Legacy Character Device)"
else
    # Check modern DRM render node for NPU (Rockchip 6.1+ BSP Kernel on Ubuntu 24.04)
    for rnode in /sys/class/drm/renderD*/device/driver; do
        if [ -e "$rnode" ] && grep -qi "rknpu" <<< "$(readlink -f "$rnode")"; then
            DRM_NAME=$(basename "$(dirname "$(dirname "$rnode")")")
            NPU_FOUND=true
            NPU_NODE="/dev/dri/${DRM_NAME} (Modern DRM Render Node)"
            break
        fi
    done
    if [ "$NPU_FOUND" = false ] && [ -d /sys/devices/platform/fdab0000.npu ]; then
        NPU_FOUND=true
        NPU_NODE="/sys/devices/platform/fdab0000.npu (Platform Device)"
    fi
fi

if [ "$NPU_FOUND" = true ]; then
    echo -e "  NPU Device Node    : ${GREEN}[FOUND] ${NPU_NODE}${RESET}"
    
    # Extract driver version via debugfs or dmesg
    NPU_VER=""
    if [ -f /sys/kernel/debug/rknpu/version ] && [ -r /sys/kernel/debug/rknpu/version ]; then
        NPU_VER=$(cat /sys/kernel/debug/rknpu/version 2>/dev/null)
    elif [ -f /sys/kernel/debug/rknpu/version ] && sudo -n true 2>/dev/null; then
        NPU_VER=$(sudo -n cat /sys/kernel/debug/rknpu/version 2>/dev/null)
    fi
    
    if [ -z "$NPU_VER" ] && command -v dmesg >/dev/null 2>&1; then
        NPU_VER=$(dmesg 2>/dev/null | grep -i "Initialized rknpu" | tail -n 1 | sed -n 's/.*Initialized rknpu \([^ ]*\).*/v\1/p')
    fi
    
    if [ -z "$NPU_VER" ] && [ -f /sys/devices/platform/fdab0000.npu/uevent ]; then
        NPU_VER=$(grep "DRIVER=" /sys/devices/platform/fdab0000.npu/uevent 2>/dev/null | cut -d'=' -f2)
    fi

    if [ -n "$NPU_VER" ]; then
        echo -e "  RKNPU Driver Ver   : ${CYAN}${NPU_VER}${RESET}"
    else
        echo -e "  RKNPU Driver Ver   : ${GREEN}Driver active${RESET}"
    fi

    # Check userspace librknnrt.so runtime library or Python RKNN environment
    LIB_PATH=""
    for p in /usr/lib/librknnrt.so /usr/local/lib/librknnrt.so /usr/lib/aarch64-linux-gnu/librknnrt.so; do
        if [ -f "$p" ]; then
            LIB_PATH="$p"
            break
        fi
    done

    if [ -n "$LIB_PATH" ]; then
        RT_VER=$(strings "$LIB_PATH" 2>/dev/null | grep -i "librknnrt version" | head -n 1)
        [ -z "$RT_VER" ] && RT_VER="Detected"
        echo -e "  Board Runtime Lib  : ${GREEN}[OK] ${LIB_PATH} (${RT_VER})${RESET}"
    elif python3 -c "import rknnlite" 2>/dev/null || ([ -f "$HOME/rknn_env/bin/python3" ] && "$HOME/rknn_env/bin/python3" -c "import rknnlite" 2>/dev/null); then
        PY_RKNN_VER=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('rknn-toolkit-lite2'))" 2>/dev/null || echo "2.3.2")
        echo -e "  Board Runtime Lib  : ${GREEN}[OK] Python RKNN-Toolkit-Lite2 v${PY_RKNN_VER} active${RESET}"
    else
        echo -e "  Board Runtime Lib  : ${YELLOW}[NOT FOUND] librknnrt.so not found in system library path${RESET}"
        echo -e "  ${YELLOW}Notice: Run 'scripts/setup_npu.sh' to install librknnrt v2.3.2 runtime.${RESET}"
    fi
    echo -e "  Compatibility Ref  : ${CYAN}See docs/COMPATIBILITY.md for driver & runtime version matrix${RESET}"
else
    echo -e "  NPU Device Node    : ${RED}[NOT FOUND] NPU device node is missing!${RESET}"
    echo -e "  ${YELLOW}Fix: Ensure you are running Rockchip 5.10/6.1 BSP kernel or verify kernel modules with 'lsmod | grep rknpu'.${RESET}"
fi

# 5. Graphics & Video Hardware Acceleration (GPU / VPU)
echo -e "\n${BOLD}[5/7] GPU (Mali-G610) & VPU (MPP / RGA) Drivers${RESET}"
if [ -e /dev/mali0 ]; then
    echo -e "  ARM Mali-G610 GPU  : ${GREEN}[OK] /dev/mali0 detected${RESET}"
else
    echo -e "  ARM Mali-G610 GPU  : ${RED}[FAIL] /dev/mali0 missing${RESET}"
fi

if [ -e /dev/mpp_service ]; then
    echo -e "  Hardware VPU (MPP) : ${GREEN}[OK] /dev/mpp_service detected (8K@60fps HW Decode ready)${RESET}"
else
    echo -e "  Hardware VPU (MPP) : ${YELLOW}[WARN] /dev/mpp_service missing (HW transcoding will fallback to CPU)${RESET}"
fi

if [ -e /dev/rga ]; then
    echo -e "  2D Graphics Engine : ${GREEN}[OK] /dev/rga detected (Hardware Blit & Rotation ready)${RESET}"
else
    echo -e "  2D Graphics Engine : ${YELLOW}[WARN] /dev/rga missing${RESET}"
fi

# 6. Memory & Swap (ZRAM) Topology
echo -e "\n${BOLD}[6/7] Memory & Swap Architecture${RESET}"
TOTAL_RAM=$(free -h | awk '/^Mem:/ {print $2}')
USED_RAM=$(free -h | awk '/^Mem:/ {print $3}')
AVAIL_RAM=$(free -h | awk '/^Mem:/ {print $7}')
echo -e "  Physical RAM       : ${GREEN}${USED_RAM} used / ${TOTAL_RAM} total${RESET} (${AVAIL_RAM} available)"

TOTAL_SWAP=$(free -h | awk '/^Swap:/ {print $2}')
USED_SWAP=$(free -h | awk '/^Swap:/ {print $3}')
if [ "$TOTAL_SWAP" != "0B" ] && [ -n "$TOTAL_SWAP" ]; then
    if grep -q "zram" /proc/swaps 2>/dev/null; then
        echo -e "  Swap Storage       : ${GREEN}${USED_SWAP} used / ${TOTAL_SWAP} total (Active ZRAM Compressed Memory)${RESET}"
    else
        echo -e "  Swap Storage       : ${YELLOW}${USED_SWAP} used / ${TOTAL_SWAP} total (Disk-backed swap)${RESET}"
    fi
else
    echo -e "  Swap Storage       : ${RED}[NONE] No swap space detected! High risk of OOM kills on 4GB/8GB boards.${RESET}"
    echo -e "  ${YELLOW}Recommendation: Enable ZRAM using our Headless Server Guide.${RESET}"
fi

# 7. Storage Medium & Bus Interface
echo -e "\n${BOLD}[7/7] Boot & Root Storage Topology${RESET}"
ROOT_DEV=$(df / | tail -n 1 | awk '{print $1}')
echo -e "  Root Filesystem    : ${BOLD}${ROOT_DEV}${RESET}"

if [[ "$ROOT_DEV" =~ nvme ]]; then
    echo -e "  Storage Interface  : ${GREEN}M.2 PCIe NVMe Solid State Drive (Optimal Throughput & IOPS)${RESET}"
    NVMe_DEV=$(echo "$ROOT_DEV" | grep -o 'nvme[0-9]*' | head -n 1)
    if [ -d "/sys/block/$NVMe_DEV/device" ]; then
        PCIE_WIDTH=$(cat "/sys/block/$NVMe_DEV/device/current_link_width" 2>/dev/null || echo "1")
        PCIE_SPEED=$(cat "/sys/block/$NVMe_DEV/device/current_link_speed" 2>/dev/null || echo "unknown")
        echo -e "  PCIe Link Status   : ${CYAN}Gen ${PCIE_SPEED} x${PCIE_WIDTH} lane(s)${RESET}"
    fi
elif [[ "$ROOT_DEV" =~ mmcblk0 ]]; then
    echo -e "  Storage Interface  : ${YELLOW}MicroSD Card (High I/O latency risk, consider upgrading to M.2 NVMe SSD)${RESET}"
elif [[ "$ROOT_DEV" =~ mmcblk1 ]]; then
    echo -e "  Storage Interface  : ${GREEN}Onboard eMMC Flash (Orange Pi 5B / 5 Plus)${RESET}"
else
    echo -e "  Storage Interface  : ${CYAN}${ROOT_DEV}${RESET}"
fi

echo -e "\n----------------------------------------------------------------------"
echo -e "${GREEN}${BOLD}Diagnostics completed!${RESET}"
echo -e "Need deeper optimization guides or troubleshooting matrices?"
echo -e "Visit: ${CYAN}https://github.com/muhammetmucahitsoylu/orangepi5-tutorials${RESET}\n"
