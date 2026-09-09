cmake_minimum_required(VERSION 3.10)
project(OrangePi_Hardware_Control CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find wiringPi / wiringOP library on system
find_library(WIRINGOP_LIB wiringPi PATHS /usr/local/lib /usr/lib)

add_executable(hardware_app src/main.cpp)
if(WIRINGOP_LIB)
    target_link_libraries(hardware_app PRIVATE ${WIRINGOP_LIB} pthread)
else()
    target_link_libraries(hardware_app PRIVATE pthread)
endif()
