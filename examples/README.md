# Orange Pi 5 Code Examples

This directory provides standalone, verified source code templates matching the project tutorials in this repository.

## Directory Structure

* **`gpio_cpp/`**: Complete CMake project demonstrating physical GPIO control (LED blinking and button input with internal pull-up) using standard C++17 and the `wiringOP` library.
  * [CMakeLists.txt](gpio_cpp/CMakeLists.txt)
  * [src/main.cpp](gpio_cpp/src/main.cpp)
* **`kernel_driver/`**: Complete Linux Kernel Module (LKM) misc character device driver controlling physical Pin 7 (`GPIO1_C6` / sysfs 54) at Ring 0.
  * [Makefile](kernel_driver/Makefile)
  * [opi5_gpio_driver.c](kernel_driver/opi5_gpio_driver.c)

## Licensing

All source code and build definitions in this directory are licensed under the permissive [MIT License](../LICENSE).
