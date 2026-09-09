#include <iostream>
#include <chrono>
#include <thread>
#include <wiringPi.h>

#define LED_PIN    4   // Physical Pin 7 (GPIO1_C6 - wiringOP 4)
#define BUTTON_PIN 0   // Physical Pin 11 (GPIO4_B2 - wiringOP 0)

int main() {
    std::cout << "--- Orange Pi 5 Hardware Control (C++) ---" << std::endl;

    // 1. Initialize wiringOP engine
    if (wiringPiSetup() == -1) {
        std::cerr << "[ERROR] Failed to initialize wiringPi / wiringOP!" << std::endl;
        return 1;
    }

    // 2. Configure pin directions
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT);
    pullUpDnControl(BUTTON_PIN, PUD_UP); // Enable internal pull-up resistor

    std::cout << "LED and Button control loop started. Press Ctrl+C to exit." << std::endl;

    for (int i = 0; i < 10; ++i) {
        // Read button state (active low with pull-up)
        int btn_state = digitalRead(BUTTON_PIN);
        if (btn_state == LOW) {
            std::cout << "Button Pressed!" << std::endl;
        }

        // Turn LED on
        digitalWrite(LED_PIN, HIGH);
        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        // Turn LED off
        digitalWrite(LED_PIN, LOW);
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }

    return 0;
}
