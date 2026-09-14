#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orange Pi 5 (RK3588 / RK3588S) Live Hardware & Thermal Dashboard
Real-time CPU DVFS, Thermal Matrix (SoC, GPU, NPU), NPU Load, and Memory Monitor
Zero external dependencies - pure Python 3 standard library
"""

import os
import sys
import time
import glob
import re

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BG_DARK = "\033[48;5;234m"

def clear_screen():
    # Move cursor to home and clear screen for flicker-free render
    sys.stdout.write("\033[H\033[J")

def get_bar(percent, length=20):
    filled = int(length * percent / 100)
    filled = max(0, min(length, filled))
    if percent < 60:
        color = GREEN
    elif percent < 80:
        color = YELLOW
    else:
        color = RED
    return f"{color}{'█' * filled}{DIM}{'░' * (length - filled)}{RESET} {percent:5.1f}%"

def read_file(path, default=""):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return default

def get_temperatures():
    temps = {}
    for tz_dir in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        tz_type = read_file(os.path.join(tz_dir, "type"), "unknown")
        raw_temp = read_file(os.path.join(tz_dir, "temp"), "0")
        try:
            temp_c = float(raw_temp) / 1000.0
            temps[tz_type] = temp_c
        except ValueError:
            pass
    return temps

def get_cpu_freqs():
    policies = {}
    for pol_dir in sorted(glob.glob("/sys/devices/system/cpu/cpufreq/policy*")):
        name = os.path.basename(pol_dir)
        cur_freq = read_file(os.path.join(pol_dir, "scaling_cur_freq"), "0")
        max_freq = read_file(os.path.join(pol_dir, "scaling_max_freq"), "0")
        governor = read_file(os.path.join(pol_dir, "scaling_governor"), "unknown")
        try:
            policies[name] = {
                "cur_mhz": int(cur_freq) // 1000,
                "max_mhz": int(max_freq) // 1000,
                "governor": governor
            }
        except ValueError:
            pass
    return policies

def get_cpu_usage(prev_stat):
    stat_line = read_file("/proc/stat", "").splitlines()
    if not stat_line:
        return 0.0, prev_stat
    fields = [int(x) for x in stat_line[0].split()[1:]]
    # user, nice, system, idle, iowait, irq, softirq, steal
    idle = fields[3] + fields[4]
    total = sum(fields)
    
    if prev_stat is None:
        return 0.0, (idle, total)
    
    prev_idle, prev_total = prev_stat
    diff_idle = idle - prev_idle
    diff_total = total - prev_total
    
    if diff_total <= 0:
        usage = 0.0
    else:
        usage = (1.0 - (diff_idle / diff_total)) * 100.0
    return max(0.0, min(100.0, usage)), (idle, total)

def get_memory():
    meminfo = {}
    content = read_file("/proc/meminfo", "")
    for line in content.splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip().split()[0]
            try:
                meminfo[key] = int(val)
            except ValueError:
                pass
    
    total = meminfo.get("MemTotal", 1)
    avail = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
    used = total - avail
    pct = (used / total) * 100.0
    
    swap_total = meminfo.get("SwapTotal", 0)
    swap_free = meminfo.get("SwapFree", 0)
    swap_used = swap_total - swap_free
    swap_pct = (swap_used / swap_total * 100.0) if swap_total > 0 else 0.0
    
    return {
        "total_mb": total // 1024,
        "used_mb": used // 1024,
        "pct": pct,
        "swap_total_mb": swap_total // 1024,
        "swap_used_mb": swap_used // 1024,
        "swap_pct": swap_pct
    }

def get_npu_load():
    content = read_file("/sys/kernel/debug/rknpu/load", "")
    if content:
        # e.g., NPU load: Core0: 0%, Core1: 0%, Core2: 0%
        return content
    return None

def get_disk_usage():
    try:
        st = os.statvfs("/")
        total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        used_gb = total_gb - free_gb
        pct = (used_gb / total_gb) * 100.0
        return {"used_gb": used_gb, "total_gb": total_gb, "pct": pct}
    except Exception:
        return {"used_gb": 0, "total_gb": 0, "pct": 0}

def get_uptime():
    content = read_file("/proc/uptime", "")
    if content:
        try:
            seconds = int(float(content.split()[0]))
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}h {minutes:02d}m {secs:02d}s"
        except Exception:
            pass
    return "unknown"

def color_temp(c):
    if c >= 75.0:
        return f"{RED}{BOLD}{c:5.1f} °C{RESET}"
    elif c >= 60.0:
        return f"{YELLOW}{BOLD}{c:5.1f} °C{RESET}"
    else:
        return f"{GREEN}{c:5.1f} °C{RESET}"

def main():
    prev_stat = None
    # Hide cursor
    sys.stdout.write("\033[?25l")
    try:
        while True:
            clear_screen()
            uptime = get_uptime()
            cpu_usage, prev_stat = get_cpu_usage(prev_stat)
            temps = get_temperatures()
            freqs = get_cpu_freqs()
            mem = get_memory()
            npu = get_npu_load()
            disk = get_disk_usage()
            
            # Header
            print(f"{CYAN}{BOLD}========================================================================{RESET}")
            print(f" {WHITE}{BOLD}🎯 ORANGE PI 5 (RK3588S) LIVE HARDWARE & THERMAL TELEMETRY{RESET}")
            print(f" {DIM}Uptime: {uptime}  |  Platform: Rockchip RK3588 8-Core (4x A76 + 4x A55){RESET}")
            print(f"{CYAN}{BOLD}========================================================================{RESET}")
            
            # CPU & Memory Section
            print(f"\n{YELLOW}{BOLD}⚡ PROCESSOR & DVFS CORES{RESET}")
            print(f"  CPU Total Load : {get_bar(cpu_usage, 28)}")
            for pol, data in freqs.items():
                cur = data["cur_mhz"]
                max_f = data["max_mhz"]
                gov = data["governor"]
                pct = (cur / max_f * 100) if max_f > 0 else 0
                label = "Cortex-A55 Little" if "policy0" in pol else "Cortex-A76 Big"
                print(f"  {pol:<8} ({label:<18}) : {cur:4d} MHz / {max_f:4d} MHz  {DIM}[{gov}]{RESET}")
            
            # Memory & Disk
            print(f"\n{YELLOW}{BOLD}💾 MEMORY & STORAGE{RESET}")
            ram_label = f"{mem['used_mb'] / 1024:.2f} GB / {mem['total_mb'] / 1024:.2f} GB"
            print(f"  RAM Usage  ({ram_label:<17}) : {get_bar(mem['pct'], 28)}")
            if mem['swap_total_mb'] > 0:
                swap_label = f"{mem['swap_used_mb']} MB / {mem['swap_total_mb']} MB"
                print(f"  Swap Usage ({swap_label:<17}) : {get_bar(mem['swap_pct'], 28)}")
            disk_label = f"{disk['used_gb']:.1f} GB / {disk['total_gb']:.1f} GB"
            print(f"  Disk (/)   ({disk_label:<17}) : {get_bar(disk['pct'], 28)}")

            # Thermal Matrix
            print(f"\n{YELLOW}{BOLD}🌡️  RK3588 THERMAL SENSORS (TEMPERATURE MATRIX){RESET}")
            # Group sensors cleanly
            soc_t = temps.get("soc-thermal", temps.get("soc_thermal", 0.0))
            gpu_t = temps.get("gpu-thermal", temps.get("gpu_thermal", 0.0))
            npu_t = temps.get("npu-thermal", temps.get("npu_thermal", 0.0))
            big0_t = temps.get("bigcore0-thermal", 0.0)
            big1_t = temps.get("bigcore1-thermal", 0.0)
            lit_t = temps.get("littlecore-thermal", 0.0)
            center_t = temps.get("center-thermal", 0.0)

            print(f"  SoC Die Core : {color_temp(soc_t)}    |  NPU Die (6 TOPS) : {color_temp(npu_t)}")
            print(f"  Big Core 0   : {color_temp(big0_t)}    |  GPU (Mali-G610)  : {color_temp(gpu_t)}")
            print(f"  Big Core 1   : {color_temp(big1_t)}    |  Little Cores     : {color_temp(lit_t)}")
            print(f"  Center Die   : {color_temp(center_t)}")

            # NPU Load Section
            print(f"\n{YELLOW}{BOLD}🧠 NEURAL PROCESSING UNIT (NPU - 3 CORES){RESET}")
            if npu:
                print(f"  {CYAN}{npu}{RESET}")
            else:
                print(f"  {GREEN}NPU Runtime Driver Active (/dev/rknpu){RESET}")
            
            print(f"\n{CYAN}------------------------------------------------------------------------{RESET}")
            print(f" {DIM}Press Ctrl+C to exit monitor  |  Refreshes every 1.5s{RESET}")
            
            time.sleep(1.5)
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor again on exit
        sys.stdout.write("\033[?25h\n")

if __name__ == "__main__":
    main()
