#!/usr/bin/env bash
# ==============================================================================
# Orange Pi 5 (RK3588 / RK3588S) Interactive Control Center & Benchmark Suite
# Repository: https://github.com/muhammetmucahitsoylu/orangepi5-tutorials
# License: MIT
# ==============================================================================

set -u

# ANSI Styling Definitions
BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RESET="\033[0m"

# Resilient Input Reader (Supports pipe, stdin, and /dev/tty fallback)
read_input() {
    local var_name="${1:-_DUMMY}"
    eval "$var_name=''"
    if [ -t 0 ]; then
        read -r "$var_name" || true
    elif ( < /dev/tty ) 2>/dev/null; then
        read -r "$var_name" < /dev/tty 2>/dev/null || true
    else
        read -r "$var_name" || true
    fi
}

# Print Header Banner
print_header() {
    clear 2>/dev/null || true
    echo -e "${CYAN}${BOLD}"
    echo "  ___                               ____  _   ____ "
    echo " / _ \ _ __ __ _ _ __   __ _  ___  |  _ \(_) | ___|"
    echo "| | | | '__/ _\` | '_ \ / _\` |/ _ \ | |_) | | |___ \ "
    echo "| |_| | | | (_| | | | | (_| |  __/ |  __/| |  ___) |"
    echo " \___/|_|  \__,_|_| |_|\__, |\___| |_|   |_| |____/ "
    echo "                       |___/                        "
    echo -e "${RESET}"
    echo -e "${BOLD}Orange Pi 5 (RK3588S) Control Center & Benchmark Suite${RESET}"
    echo -e "Community Knowledge Base: ${CYAN}https://github.com/muhammetmucahitsoylu/orangepi5-tutorials${RESET}"
    echo "======================================================================"
}

# 1. Quick Subsystem Diagnostics
run_diagnostics() {
    echo -e "\n${BOLD}${CYAN}=== [1] Hardware & Subsystem Telemetry ===${RESET}\n"
    
    # Board detection
    if [ -f /proc/device-tree/model ]; then
        BOARD_MODEL=$(tr -d '\0' < /proc/device-tree/model)
    else
        BOARD_MODEL="Orange Pi 5 (RK3588S Generic)"
    fi
    echo -e "  Hardware Model   : ${GREEN}${BOARD_MODEL}${RESET}"
    echo -e "  Linux Kernel     : ${BOLD}$(uname -r)${RESET}"
    echo -e "  CPU Architecture : ${CYAN}ARMv8 Cortex-A76 (x4) + Cortex-A55 (x4)${RESET}"
    
    # Thermal Readout
    echo -e "\n  ${BOLD}Thermal Sensors:${RESET}"
    for tz in /sys/class/thermal/thermal_zone*; do
        if [ -d "$tz" ]; then
            TYPE=$(cat "$tz/type" 2>/dev/null || echo "thermal")
            RAW=$(cat "$tz/temp" 2>/dev/null || echo "0")
            DEG=$(awk "BEGIN {printf \"%.1f\", $RAW / 1000}")
            INT_DEG=${DEG%.*}
            if [ "$INT_DEG" -ge 80 ]; then
                T_COLOR="${RED}"
            elif [ "$INT_DEG" -ge 65 ]; then
                T_COLOR="${YELLOW}"
            else
                T_COLOR="${GREEN}"
            fi
            printf "    %-20s : ${T_COLOR}%5.1f °C${RESET}\n" "$TYPE" "$DEG"
        fi
    done
    
    # NPU Node
    echo -e "\n  ${BOLD}Hardware Accelerators:${RESET}"
    NPU_ACTIVE=false
    NPU_NODE_STR=""
    if [ -e /dev/rknpu ] || compgen -G "/dev/rknpu*" > /dev/null; then
        NPU_ACTIVE=true
        NPU_NODE_STR="/dev/rknpu active"
    else
        for rnode in /sys/class/drm/renderD*/device/driver; do
            if [ -e "$rnode" ] && grep -qi "rknpu" <<< "$(readlink -f "$rnode")"; then
                DRM_NAME=$(basename "$(dirname "$(dirname "$rnode")")")
                NPU_ACTIVE=true
                NPU_NODE_STR="/dev/dri/${DRM_NAME} active"
                break
            fi
        done
        if [ "$NPU_ACTIVE" = false ] && [ -d /sys/devices/platform/fdab0000.npu ]; then
            NPU_ACTIVE=true
            NPU_NODE_STR="Platform NPU active"
        fi
    fi

    if [ "$NPU_ACTIVE" = true ]; then
        NPU_TAG=""
        if [ -f /sys/kernel/debug/rknpu/version ] && [ -r /sys/kernel/debug/rknpu/version ]; then
            NPU_TAG=" ($(cat /sys/kernel/debug/rknpu/version 2>/dev/null | tr -d '\n\r'))"
        elif [ -f /sys/kernel/debug/rknpu/version ] && sudo -n true 2>/dev/null; then
            NPU_TAG=" ($(sudo -n cat /sys/kernel/debug/rknpu/version 2>/dev/null | tr -d '\n\r'))"
        fi
        if [ -z "$NPU_TAG" ] && command -v dmesg >/dev/null 2>&1; then
            D_VER=$(dmesg 2>/dev/null | grep -i "Initialized rknpu" | tail -n 1 | sed -n 's/.*Initialized rknpu \([^ ]*\).*/v\1/p')
            [ -n "$D_VER" ] && NPU_TAG=" (${D_VER})"
        fi
        echo -e "    NPU (6 TOPS)     : ${GREEN}[FOUND] ${NPU_NODE_STR}${NPU_TAG}${RESET}"
    else
        echo -e "    NPU (6 TOPS)     : ${RED}[MISSING] Driver node not detected${RESET}"
    fi
    
    if [ -e /dev/mali0 ]; then
        echo -e "    Mali-G610 GPU    : ${GREEN}[FOUND] /dev/mali0 active${RESET}"
    else
        echo -e "    Mali-G610 GPU    : ${YELLOW}[WARN] /dev/mali0 not exposed${RESET}"
    fi
    
    if [ -e /dev/mpp_service ]; then
        echo -e "    MPP VPU Decoder  : ${GREEN}[FOUND] /dev/mpp_service (8K HW Video ready)${RESET}"
    else
        echo -e "    MPP VPU Decoder  : ${YELLOW}[WARN] /dev/mpp_service missing${RESET}"
    fi
    
    # Memory and Storage
    echo -e "\n  ${BOLD}Memory & Storage Status:${RESET}"
    RAM_USED=$(free -h | awk '/^Mem:/ {print $3}')
    RAM_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
    echo -e "    RAM Utilization  : ${GREEN}${RAM_USED} / ${RAM_TOTAL}${RESET}"
    
    ROOT_DEV=$(df -h / | tail -n 1 | awk '{print $1 " (" $4 " free of " $2 ")"}')
    echo -e "    Root Filesystem  : ${CYAN}${ROOT_DEV}${RESET}"
    
    echo -e "\nPress [ENTER] to return to the main menu..."
    read_input _
}

# 2. Performance Governor Lock
set_performance() {
    echo -e "\n${BOLD}${YELLOW}=== [2] Locking System to Maximum Performance Mode ===${RESET}\n"
    
    # Elevate with sudo if not root
    SUDO_CMD=""
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo >/dev/null 2>&1; then
            echo -e "${YELLOW}[!] Elevating permissions via sudo...${RESET}"
            SUDO_CMD="sudo"
        else
            echo -e "${RED}[ERROR] Root privileges required and sudo not available.${RESET}"
            echo -e "Press [ENTER] to return..."
            read_input _
            return
        fi
    fi
    
    echo "Setting CPU DVFS governors to 'performance'..."
    for pol in /sys/devices/system/cpu/cpufreq/policy*; do
        if [ -f "$pol/scaling_governor" ]; then
            echo "performance" | $SUDO_CMD tee "$pol/scaling_governor" >/dev/null 2>&1 || true
            CURR_MHZ=$(($(cat "$pol/scaling_cur_freq") / 1000))
            echo -e "  $(basename "$pol") locked at: ${GREEN}${CURR_MHZ} MHz${RESET}"
        fi
    done
    
    # GPU Performance
    for gpu_gov in /sys/class/devfreq/*gpu*/governor; do
        if [ -f "$gpu_gov" ]; then
            echo "performance" | $SUDO_CMD tee "$gpu_gov" >/dev/null 2>&1 || true
            echo -e "  GPU Governor set to: ${GREEN}performance${RESET}"
        fi
    done
    
    # NPU Performance
    for npu_gov in /sys/class/devfreq/*npu*/governor; do
        if [ -f "$npu_gov" ]; then
            echo "performance" | $SUDO_CMD tee "$npu_gov" >/dev/null 2>&1 || true
            echo -e "  NPU Governor set to: ${GREEN}performance${RESET}"
        fi
    done
    
    echo -e "\n${GREEN}${BOLD}[SUCCESS] Full hardware performance mode engaged!${RESET}"
    echo -e "${YELLOW}Note: Ensure active fan cooling is connected to prevent thermal throttling.${RESET}"
    echo -e "\nPress [ENTER] to return..."
    read_input _
}

# 3. Default Power-Saving Governor
set_powersave() {
    echo -e "\n${BOLD}${CYAN}=== [3] Restoring Balanced Power Governor (Schedutil) ===${RESET}\n"
    
    SUDO_CMD=""
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo >/dev/null 2>&1; then
            echo -e "${YELLOW}[!] Elevating permissions via sudo...${RESET}"
            SUDO_CMD="sudo"
        else
            echo -e "${RED}[ERROR] Root privileges required and sudo not available.${RESET}"
            echo -e "Press [ENTER] to return..."
            read_input _
            return
        fi
    fi
    
    for pol in /sys/devices/system/cpu/cpufreq/policy*; do
        if [ -f "$pol/scaling_governor" ]; then
            AVAILABLE=$(cat "$pol/scaling_available_governors")
            TARGET_GOV="schedutil"
            if [[ "$AVAILABLE" =~ schedutil ]]; then
                TARGET_GOV="schedutil"
            elif [[ "$AVAILABLE" =~ ondemand ]]; then
                TARGET_GOV="ondemand"
            fi
            echo "$TARGET_GOV" | $SUDO_CMD tee "$pol/scaling_governor" >/dev/null 2>&1 || true
            echo -e "  $(basename "$pol") restored to: ${GREEN}$(cat "$pol/scaling_governor")${RESET}"
        fi
    done
    
    echo -e "\n${GREEN}[SUCCESS] Balanced dynamic frequency scaling restored.${RESET}"
    echo -e "\nPress [ENTER] to return..."
    read_input _
}

# 4. Storage Benchmark
run_storage_benchmark() {
    echo -e "\n${BOLD}${MAGENTA}=== [4] Storage I/O Benchmark (Sequential Throughput) ===${RESET}\n"
    
    TEST_DIR="${HOME:-/tmp}"
    if [ ! -w "$TEST_DIR" ]; then
        TEST_DIR="/tmp"
    fi
    TEST_FILE="${TEST_DIR}/.opi5_speedtest_tmp"
    
    echo -e "Target Directory         : ${CYAN}${TEST_DIR}${RESET}"
    echo "Running 256MB direct write benchmark (fdatasync)..."
    WRITE_RESULT=$(LC_ALL=C dd if=/dev/zero of="$TEST_FILE" bs=1M count=256 conv=fdatasync 2>&1)
    WRITE_SPEED=$(echo "$WRITE_RESULT" | grep -o '[0-9.]* [M|G|k|K]B/s' | tail -n 1)
    
    echo -e "  Sequential Write Speed : ${GREEN}${WRITE_SPEED:-N/A}${RESET}"
    
    # Flush cache if permissions allow
    CACHE_CLEARED=false
    if [ "$EUID" -eq 0 ]; then
        echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
        CACHE_CLEARED=true
    elif command -v sudo >/dev/null 2>&1; then
        sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null && CACHE_CLEARED=true || true
    fi
    
    echo "Running 256MB direct read benchmark..."
    READ_RESULT=$(LC_ALL=C dd if="$TEST_FILE" of=/dev/null bs=1M count=256 2>&1)
    READ_SPEED=$(echo "$READ_RESULT" | grep -o '[0-9.]* [M|G|k|K]B/s' | tail -n 1)
    
    if [ "$CACHE_CLEARED" = true ]; then
        echo -e "  Sequential Read Speed  : ${GREEN}${READ_SPEED:-N/A}${RESET} (Uncached direct disk read)"
    else
        echo -e "  Sequential Read Speed  : ${YELLOW}${READ_SPEED:-N/A}${RESET} (Page cache active - root needed for purge)"
    fi
    
    rm -f "$TEST_FILE"
    
    echo -e "\n${BOLD}Evaluation Guide:${RESET}"
    echo "  > 300 MB/s : M.2 NVMe PCIe Gen2 x1 SSD (Optimal for Orange Pi 5)"
    echo "  ~ 100 MB/s : High-speed eMMC module"
    echo "  < 35 MB/s  : Standard MicroSD card (High bottleneck for I/O)"
    
    echo -e "\nPress [ENTER] to return..."
    read_input _
}

# 5. NPU Verification & Benchmark
run_npu_test() {
    echo -e "\n${BOLD}${CYAN}=== [5] Neural Processing Unit (NPU - 6 TOPS) Self-Test ===${RESET}\n"
    
    NPU_NODE_STR=""
    if [ -e /dev/rknpu ] || compgen -G "/dev/rknpu*" > /dev/null; then
        NPU_NODE_STR="/dev/rknpu"
    else
        for rnode in /sys/class/drm/renderD*/device/driver; do
            if [ -e "$rnode" ] && grep -qi "rknpu" <<< "$(readlink -f "$rnode")"; then
                DRM_NAME=$(basename "$(dirname "$(dirname "$rnode")")")
                NPU_NODE_STR="/dev/dri/${DRM_NAME}"
                break
            fi
        done
        if [ -z "$NPU_NODE_STR" ] && [ -d /sys/devices/platform/fdab0000.npu ]; then
            NPU_NODE_STR="/sys/devices/platform/fdab0000.npu"
        fi
    fi

    if [ -z "$NPU_NODE_STR" ]; then
        echo -e "${RED}[FAIL] NPU device node not detected!${RESET}"
        echo -e "The Rockchip NPU driver is not loaded in this kernel."
        echo -e "Press [ENTER] to return..."
        read_input _
        return
    fi
    
    echo -e "NPU Hardware Node     : ${GREEN}[OK] ${NPU_NODE_STR} detected${RESET}"
    
    NPU_VER=""
    if [ -f /sys/kernel/debug/rknpu/version ] && [ -r /sys/kernel/debug/rknpu/version ]; then
        NPU_VER=$(cat /sys/kernel/debug/rknpu/version 2>/dev/null | tr -d '\n\r')
    elif [ -f /sys/kernel/debug/rknpu/version ] && sudo -n true 2>/dev/null; then
        NPU_VER=$(sudo -n cat /sys/kernel/debug/rknpu/version 2>/dev/null | tr -d '\n\r')
    fi
    if [ -z "$NPU_VER" ] && command -v dmesg >/dev/null 2>&1; then
        D_VER=$(dmesg 2>/dev/null | grep -i "Initialized rknpu" | tail -n 1 | sed -n 's/.*Initialized rknpu \([^ ]*\).*/v\1/p')
        [ -n "$D_VER" ] && NPU_VER="${D_VER}"
    fi
    [ -n "$NPU_VER" ] && echo -e "RKNPU Driver Version  : ${CYAN}${NPU_VER}${RESET}"
    
    # Check Python bindings
    echo "Checking Python RKNN-Toolkit-Lite2 bindings..."
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "from rknnlite.api import RKNNLite; print('RKNNLite: OK')" 2>/dev/null; then
            echo -e "Python RKNN Binding   : ${GREEN}[OK] RKNNLite API importable${RESET}"
        elif [ -f "$HOME/rknn_env/bin/python3" ]; then
            if "$HOME/rknn_env/bin/python3" -c "from rknnlite.api import RKNNLite; print('RKNNLite: OK')" 2>/dev/null; then
                echo -e "Python RKNN Binding   : ${GREEN}[OK] RKNNLite active in ~/rknn_env${RESET}"
            fi
        else
            echo -e "Python RKNN Binding   : ${YELLOW}[NOTE] Python package not found in current environment${RESET}"
            echo -e "  Run 'bash scripts/setup_npu.sh' to install the isolated NPU runtime."
        fi
    fi
    
    echo -e "\n${GREEN}[SUCCESS] NPU hardware subsystem is healthy and ready for inference!${RESET}"
    echo -e "\nPress [ENTER] to return..."
    read_input _
}

# 6. Static MAC Address Fix
fix_mac_address() {
    echo -e "\n${BOLD}${YELLOW}=== [6] Permanent MAC Address Lock Utility ===${RESET}\n"
    
    SUDO_CMD=""
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo >/dev/null 2>&1; then
            echo -e "${YELLOW}[!] Elevating permissions via sudo...${RESET}"
            SUDO_CMD="sudo"
        else
            echo -e "${RED}[ERROR] Root privileges required and sudo not available.${RESET}"
            echo -e "Press [ENTER] to return..."
            read_input _
            return
        fi
    fi
    
    # Prioritize physical Ethernet (end*, eth*) or WiFi (wl*)
    IFACE=$(ip -br link | awk '$1 ~ /^(en|eth|wl)/ {print $1}' | head -n 1)
    if [ -z "$IFACE" ]; then
        IFACE=$(ip -br link | awk '$1 !~ /^(lo|docker|veth|br|tailscale|tun|tap)/ {print $1}' | head -n 1)
    fi
    
    if [ -z "$IFACE" ]; then
        echo -e "${RED}[ERROR] No physical network interface found!${RESET}"
        echo -e "Press [ENTER] to return..."
        read_input _
        return
    fi
    
    CURRENT_MAC=$(ip link show "$IFACE" | awk '/ether/ {print $2}')
    echo -e "Detected Network Interface : ${CYAN}${IFACE}${RESET}"
    echo -e "Current Assigned MAC       : ${BOLD}${CURRENT_MAC}${RESET}"
    
    echo -e "\nDo you want to permanently bind interface '${IFACE}' to MAC '${CURRENT_MAC}'? (y/N)"
    read_input CONFIRM
    if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
        RULE_FILE="/etc/udev/rules.d/70-persistent-net.rules"
        echo "SUBSYSTEM==\"net\", ACTION==\"add\", DRIVERS==\"?*\", ATTR{address}==\"${CURRENT_MAC}\", NAME=\"${IFACE}\"" | $SUDO_CMD tee "$RULE_FILE" >/dev/null
        echo -e "${GREEN}[SUCCESS] Udev rule created at ${RULE_FILE}.${RESET}"
        echo -e "Your MAC address and DHCP IP lease will remain persistent across reboots."
    else
        echo "Operation cancelled."
    fi
    
    echo -e "\nPress [ENTER] to return..."
    read_input _
}

# 7. Live Thermal & Frequency Monitor Loop
monitor_live() {
    print_header
    echo -e "${BOLD}${CYAN}=== [7] Live Thermal & DVFS Telemetry (Ctrl+C to exit) ===${RESET}\n"
    
    trap 'echo -e "\nMonitor stopped."; return' INT
    
    while true; do
        CPU_TEMP=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "0")
        CPU_C=$(awk "BEGIN {printf \"%.1f\", $CPU_TEMP / 1000}")
        
        A55_FREQ=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || echo "0")
        A55_MHZ=$((A55_FREQ / 1000))
        
        A76_0_FREQ=$(cat /sys/devices/system/cpu/cpufreq/policy4/scaling_cur_freq 2>/dev/null || echo "0")
        A76_0_MHZ=$((A76_0_FREQ / 1000))
        
        A76_1_FREQ=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq 2>/dev/null || echo "0")
        A76_1_MHZ=$((A76_1_FREQ / 1000))
        
        printf "\r  CPU: %5.1f °C | A55: %4d MHz | A76_Cluster0: %4d MHz | A76_Cluster1: %4d MHz   " \
               "$CPU_C" "$A55_MHZ" "$A76_0_MHZ" "$A76_1_MHZ"
        sleep 1
    done
}

# Main Menu Loop
main_menu() {
    while true; do
        print_header
        echo -e "${BOLD}Select a task:${RESET}\n"
        echo -e "  ${GREEN}1)${RESET} 🩺 Comprehensive Hardware Health & Subsystem Diagnostics"
        echo -e "  ${GREEN}2)${RESET} ⚡ Lock Max Performance Mode (2.4 GHz CPU + NPU Boost)"
        echo -e "  ${GREEN}3)${RESET} 🔋 Restore Balanced Power Governor (Schedutil/Ondemand)"
        echo -e "  ${GREEN}4)${RESET} 💾 Run Storage I/O Benchmark (Direct NVMe Throughput)"
        echo -e "  ${GREEN}5)${RESET} 🧠 Neural Processing Unit (NPU - 6 TOPS) Self-Test"
        echo -e "  ${GREEN}6)${RESET} 🌐 Fix Random MAC Address Permanently (Static Rule)"
        echo -e "  ${GREEN}7)${RESET} 🌡️ Live Real-Time Thermal & Frequency Monitor"
        echo -e "  ${RED}0)${RESET} 🚪 Exit"
        echo ""
        echo -ne "${BOLD}Enter choice [0-7]: ${RESET}"
        read_input CHOICE
        
        if [ -z "$CHOICE" ]; then
            echo -e "\nExiting. Happy Hacking!\n"
            exit 0
        fi

        case "$CHOICE" in
            1) run_diagnostics ;;
            2) set_performance ;;
            3) set_powersave ;;
            4) run_storage_benchmark ;;
            5) run_npu_test ;;
            6) fix_mac_address ;;
            7) monitor_live ;;
            0) echo -e "\nExiting. Happy Hacking!\n"; exit 0 ;;
            *) echo -e "\n${RED}Invalid option.${RESET} Please select between 0 and 7."; sleep 1 ;;
        esac
    done
}

main_menu
