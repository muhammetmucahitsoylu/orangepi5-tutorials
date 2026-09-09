#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/miscdevice.h>
#include <linux/gpio.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Muhammet Mucahit Soylu");
MODULE_DESCRIPTION("Orange Pi 5 (RK3588S) GPIO Control Character Device Driver");
MODULE_VERSION("1.0");

#define DEVICE_NAME "opi5_gpio"

/* 
 * Orange Pi 5 Physical Pin 7 = GPIO1_C6
 * Linux Sysfs Calculation: (Bank * 32) + (Port * 8) + Pin
 * GPIO1_C6 = (1 * 32) + (2 * 8) + 6 = 54
 */
#define TARGET_GPIO 54

static char driver_buffer[256];
static int led_state = 0;

static int dev_open(struct inode *inodep, struct file *filep) {
    pr_info("[OPI5_GPIO] Device file opened.\n");
    return 0;
}

static ssize_t dev_read(struct file *filep, char __user *buffer, size_t len, loff_t *offset) {
    int bytes_to_copy;
    int bytes_not_copied;
    char state_str[32];

    if (*offset > 0)
        return 0;

    snprintf(state_str, sizeof(state_str), "GPIO54 State: %d\n", led_state);
    bytes_to_copy = strlen(state_str);

    bytes_not_copied = copy_to_user(buffer, state_str, bytes_to_copy);
    if (bytes_not_copied != 0) {
        pr_warn("[OPI5_GPIO] Failed to copy data to user space!\n");
        return -EFAULT;
    }

    *offset += bytes_to_copy;
    return bytes_to_copy;
}

static ssize_t dev_write(struct file *filep, const char __user *buffer, size_t len, loff_t *offset) {
    int bytes_to_copy = min(len, sizeof(driver_buffer) - 1);

    if (copy_from_user(driver_buffer, buffer, bytes_to_copy)) {
        return -EFAULT;
    }
    driver_buffer[bytes_to_copy] = '\0';

    if (driver_buffer[0] == '1') {
        gpio_set_value(TARGET_GPIO, 1);
        led_state = 1;
        pr_info("[OPI5_GPIO] GPIO54 set to HIGH (1). Hardware active.\n");
    } else if (driver_buffer[0] == '0') {
        gpio_set_value(TARGET_GPIO, 0);
        led_state = 0;
        pr_info("[OPI5_GPIO] GPIO54 set to LOW (0). Hardware disabled.\n");
    } else {
        pr_warn("[OPI5_GPIO] Invalid command! Please write '1' or '0'.\n");
    }

    return bytes_to_copy;
}

static int dev_release(struct inode *inodep, struct file *filep) {
    pr_info("[OPI5_GPIO] Device file closed.\n");
    return 0;
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = dev_open,
    .read = dev_read,
    .write = dev_write,
    .release = dev_release,
};

static struct miscdevice opi5_miscdevice = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = DEVICE_NAME,
    .fops = &fops,
    .mode = 0666,
};

static int __init opi5_driver_init(void) {
    int result = 0;

    pr_info("[OPI5_GPIO] Loading module...\n");

    if (!gpio_is_valid(TARGET_GPIO)) {
        pr_err("[OPI5_GPIO] Invalid GPIO pin: %d\n", TARGET_GPIO);
        return -ENODEV;
    }

    result = gpio_request(TARGET_GPIO, "OPI5_LED_PIN");
    if (result) {
        pr_err("[OPI5_GPIO] Failed to claim GPIO pin: %d\n", result);
        return result;
    }

    gpio_direction_output(TARGET_GPIO, 0);

    result = misc_register(&opi5_miscdevice);
    if (result) {
        pr_err("[OPI5_GPIO] Failed to register misc device: %d\n", result);
        gpio_free(TARGET_GPIO);
        return result;
    }

    pr_info("[OPI5_GPIO] Driver successfully loaded: /dev/%s\n", DEVICE_NAME);
    return 0;
}

static void __exit opi5_driver_exit(void) {
    pr_info("[OPI5_GPIO] Unloading module...\n");
    gpio_set_value(TARGET_GPIO, 0);
    gpio_free(TARGET_GPIO);
    misc_deregister(&opi5_miscdevice);
    pr_info("[OPI5_GPIO] Driver unloaded and hardware released.\n");
}

module_init(opi5_driver_init);
module_exit(opi5_driver_exit);
