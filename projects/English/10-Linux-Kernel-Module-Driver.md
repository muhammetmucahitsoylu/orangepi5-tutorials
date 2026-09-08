# **Orange Pi 5 (RK3588S) Linux Kernel Module (LKM) and Device Driver Guide**

This guide provides an end-to-end walkthrough of Linux kernel programming on the Orange Pi 5 (Rockchip RK3588S). It explores Kernel Space vs. User Space privilege rings, demonstrates how to provision proprietary Rockchip BSP Kernel Headers, and implements a full **Character Device Driver (`/dev/opi5_gpio`)** in C to drive physical hardware GPIO lines with ring 0 privileges.

---

## **1. Kernel Space vs. User Space: Operating System Foundations**

Modern processor architectures enforce strict hardware privilege rings to guarantee system stability:

* **User Space (Ring 3):** Where application runtimes (Python, Go, userspace C++) execute. Applications cannot touch physical hardware registers or arbitrary memory addresses directly; they must transition through standard system calls (`syscall`). Unhandled exceptions cause a process crash (`Segmentation Fault`), but the OS survives.
* **Kernel Space (Ring 0):** The core operating system environment. Device drivers, virtual memory management (MMU), interrupt handlers, and CPU schedulers run here. Direct memory access and full hardware register authority exist. A single invalid pointer dereference or data race triggers an unrecoverable **Kernel Panic / OOPS**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        USER SPACE (APPLICATION)                        │
│                                                                        │
│   Shell / C App                         echo "1" > /dev/opi5_gpio      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (System Calls: open, read, write)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   VFS (Virtual File System Layer)                      │
│                   Device Node: /dev/opi5_gpio                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (File Operations: fops dispatch)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      KERNEL SPACE (RING 0 PRIVILEGE)                   │
│                                                                        │
│   opi5_gpio_driver.ko (Loadable Kernel Module)                         │
│   - copy_from_user() boundary validation                               │
│   - Direct hardware GPIO controller driver (GPIO1_D0 / Pin 7)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Physical Voltage Output)
                                    ▼
                          [ Hardware: LED / Relay ]
```

---

## **2. The Embedded Linux Pitfall: Rockchip Kernel Headers**

On standard x86 systems, running `sudo apt install linux-headers-$(uname -r)` is trivial. However, Single Board Computers running customized Rockchip BSP kernels (`5.10.110-rockchip-rk3588` or `6.1.x`) require targeted header repositories.

### **Header Provisioning & Verification:**

1. **Check Active Kernel Release:**
   ```bash
   uname -r
   ```

2. **Install Build Toolchains:**
   ```bash
   sudo apt update
   sudo apt install -y build-essential kmod gcc bc bison flex libssl-dev libelf-dev
   ```

3. **Install Kernel Headers:**
   * **On Orange Pi OS / Official Ubuntu Images:**
     ```bash
     sudo apt install -y linux-headers-$(uname -r)
     ```
     *(If unavailable via apt, run `sudo orangepi-config` and select `Software -> Headers`).*
   * **On Armbian:**
     ```bash
     sudo apt install -y linux-headers-current-rockchip-rk3588
     ```

4. **Verify Build Symlink:**  
   Ensure `/lib/modules/$(uname -r)/build` points to a valid kernel Makefile tree:
   ```bash
   ls -l /lib/modules/$(uname -r)/build
   ```
   *If this directory contains Makefile and Kconfig, your environment is ready to build kernel objects!*

---

## **3. Step 1: Device Driver Implementation (`opi5_gpio_driver.c`)**

This driver registers as a modern **Miscellaneous Character Device**, creating `/dev/opi5_gpio` automatically via sysfs/udev, and maps user-space write requests directly to physical **Pin 7 (GPIO1_D0)**.

Create workspace:
```bash
mkdir -p ~/projects/kernel_driver && cd ~/projects/kernel_driver
```

Write `opi5_gpio_driver.c`:

```c
#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/miscdevice.h>
#include <linux/gpio.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Muhammet Mucahit Soylu");
MODULE_DESCRIPTION("Orange Pi 5 (RK3588S) GPIO Hardware Character Driver");
MODULE_VERSION("1.0");

#define DEVICE_NAME "opi5_gpio"

/* 
 * Orange Pi 5 Physical Pin 7 = GPIO1_D0
 * Linux Global GPIO Index Formula:
 * Bank 1, Group D (A=0, B=1, C=2, D=3), Pin 0
 * Index = (Bank * 32) + (Group * 8) + Pin
 * GPIO1_D0 = (1 * 32) + (3 * 8) + 0 = 32 + 24 + 0 = 56
 */
#define TARGET_GPIO 56

static char driver_buffer[256];
static int led_state = 0;

/* Invoked when /dev/opi5_gpio is opened */
static int dev_open(struct inode *inodep, struct file *filep) {
    pr_info("[OPI5_GPIO] Device node opened.\n");
    return 0;
}

/* Invoked when reading from /dev/opi5_gpio (e.g. cat /dev/opi5_gpio) */
static ssize_t dev_read(struct file *filep, char __user *buffer, size_t len, loff_t *offset) {
    int bytes_to_copy;
    int bytes_not_copied;
    char state_str[32];

    if (*offset > 0)
        return 0;

    snprintf(state_str, sizeof(state_str), "GPIO56 State: %d\n", led_state);
    bytes_to_copy = strlen(state_str);

    /* Safe Memory Boundary: Kernel to User Space copy */
    bytes_not_copied = copy_to_user(buffer, state_str, bytes_to_copy);
    if (bytes_not_copied != 0) {
        pr_warn("[OPI5_GPIO] Failed to copy bytes to user space!\n");
        return -EFAULT;
    }

    *offset += bytes_to_copy;
    return bytes_to_copy;
}

/* Invoked when writing to /dev/opi5_gpio (e.g. echo "1" > /dev/opi5_gpio) */
static ssize_t dev_write(struct file *filep, const char __user *buffer, size_t len, loff_t *offset) {
    int bytes_to_copy = min(len, sizeof(driver_buffer) - 1);

    /* Safe Memory Boundary: User Space to Kernel Space copy */
    if (copy_from_user(driver_buffer, buffer, bytes_to_copy)) {
        return -EFAULT;
    }
    driver_buffer[bytes_to_copy] = '\0';

    if (driver_buffer[0] == '1') {
        gpio_set_value(TARGET_GPIO, 1);
        led_state = 1;
        pr_info("[OPI5_GPIO] GPIO56 driven HIGH (1). Hardware ON.\n");
    } else if (driver_buffer[0] == '0') {
        gpio_set_value(TARGET_GPIO, 0);
        led_state = 0;
        pr_info("[OPI5_GPIO] GPIO56 driven LOW (0). Hardware OFF.\n");
    } else {
        pr_warn("[OPI5_GPIO] Invalid argument. Send '1' or '0'.\n");
    }

    return bytes_to_copy;
}

/* Invoked when /dev/opi5_gpio is closed */
static int dev_release(struct inode *inodep, struct file *filep) {
    pr_info("[OPI5_GPIO] Device node closed.\n");
    return 0;
}

/* Virtual File System dispatch table */
static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = dev_open,
    .read = dev_read,
    .write = dev_write,
    .release = dev_release,
};

/* Misc Character Device registration */
static struct miscdevice opi5_miscdevice = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = DEVICE_NAME,
    .fops = &fops,
    .mode = 0666, /* World read/write permissions */
};

/* Module Initialization: Triggered via insmod */
static int __init opi5_driver_init(void) {
    int result = 0;

    pr_info("[OPI5_GPIO] Initializing kernel module...\n");

    /* 1. Request GPIO line from kernel subsystem */
    if (!gpio_is_valid(TARGET_GPIO)) {
        pr_err("[OPI5_GPIO] Invalid GPIO line index: %d\n", TARGET_GPIO);
        return -ENODEV;
    }

    result = gpio_request(TARGET_GPIO, "OPI5_LED_PIN");
    if (result) {
        pr_err("[OPI5_GPIO] Failed to claim GPIO line (already locked?): %d\n", result);
        return result;
    }

    /* Configure GPIO pin direction to output */
    gpio_direction_output(TARGET_GPIO, 0);

    /* 2. Register character device node */
    result = misc_register(&opi5_miscdevice);
    if (result) {
        pr_err("[OPI5_GPIO] Failed to register misc device: %d\n", result);
        gpio_free(TARGET_GPIO);
        return result;
    }

    pr_info("[OPI5_GPIO] Driver registered successfully. Accessible at /dev/%s\n", DEVICE_NAME);
    return 0;
}

/* Module Cleanup: Triggered via rmmod */
static void __exit opi5_driver_exit(void) {
    pr_info("[OPI5_GPIO] Unloading kernel module...\n");

    /* Reset hardware state and release GPIO subsystem claim */
    gpio_set_value(TARGET_GPIO, 0);
    gpio_free(TARGET_GPIO);

    /* Deregister device node */
    misc_deregister(&opi5_miscdevice);

    pr_info("[OPI5_GPIO] Driver unloaded. Hardware resources freed.\n");
}

module_init(opi5_driver_init);
module_exit(opi5_driver_exit);
```

---

## **4. Step 2: Linux Kbuild Makefile**

Linux kernel modules cannot be built directly using standalone GCC; they must execute within the kernel's Kbuild engine:

Create `Makefile`:

```makefile
obj-m += opi5_gpio_driver.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

default:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
```

---

## **5. Step 3: Compilation & Kernel Object Generation**

Compile the module:

```bash
make
```

### **Verify Generated Kernel Binary:**
```bash
ls -l *.ko
```
*Confirm availability of **`opi5_gpio_driver.ko`**.*

Inspect module metadata:
```bash
modinfo opi5_gpio_driver.ko
```
*Validates author, license (GPL), and vermagic kernel version alignment.*

---

## **6. Step 4: Loading Module & Hardware Validation**

### **1. Insert Module into Active Kernel:**
```bash
sudo insmod opi5_gpio_driver.ko
```

### **2. Check Kernel Ring Buffer (`dmesg`):**
```bash
sudo dmesg | tail -n 10
```
**Expected Output:**
```text
[  142.512034] [OPI5_GPIO] Initializing kernel module...
[  142.512150] [OPI5_GPIO] Driver registered successfully. Accessible at /dev/opi5_gpio
```

### **3. Verify Device Node:**
```bash
ls -l /dev/opi5_gpio
```
*Reports: `crw-rw-rw- 1 root root ... /dev/opi5_gpio`.*

---

### **4. Hardware Interaction from User Space:**

Connect an LED or multimeter across **Pin 7 (GPIO1_D0)** and **GND (Pin 6)**:

```bash
# Drive pin HIGH (Turn LED ON):
echo "1" > /dev/opi5_gpio

# Read state directly from kernel space:
cat /dev/opi5_gpio
# Output: GPIO56 State: 1

# Drive pin LOW (Turn LED OFF):
echo "0" > /dev/opi5_gpio
```

Inspect the driver's real-time kernel logging:
```bash
sudo dmesg | tail -n 5
```
*Reports: `[OPI5_GPIO] GPIO56 driven HIGH (1). Hardware ON.`*

---

## **7. Step 5: Unloading Driver & Safe Resource Reclamation**

```bash
sudo rmmod opi5_gpio_driver
```

Verify in kernel logs:
```bash
sudo dmesg | tail -n 5
```
*`[OPI5_GPIO] Driver unloaded. Hardware resources freed.` confirms zero memory leaks and safe GPIO pin release.*

---

## **8. Troubleshooting & Common Issues**

| Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| `insmod: Device or resource busy` | GPIO 56 is already locked by another subsystem or driver (e.g. wiringOP). | Select an alternative pin or stop the conflicting service. |
| `insmod: Invalid module format` | Vermagic mismatch between compiled header and active running kernel. | Ensure `/lib/modules/$(uname -r)/build` matches `uname -r`. |
| `make: /lib/modules/.../build: No such file` | Kernel headers package is missing or symlink is broken. | Re-run header installation in Step 2. |
| `Unknown symbol in module` | Missing GPL module license tag or calling unexported symbol. | Confirm `MODULE_LICENSE("GPL");` is defined at the top of driver. |
