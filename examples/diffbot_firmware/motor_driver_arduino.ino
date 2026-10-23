// Embedded Firmware for Arduino Microcontroller Motor Driver
#include <Arduino.h>

#define ENCODER_A_PIN 2
#define ENCODER_B_PIN 3
#define MOTOR_PWM_PIN 5
#define MOTOR_DIR_PIN 4

volatile long encoder_ticks = 0;
volatile unsigned long last_interrupt_time = 0;

// Interrupt Service Routine (ISR) for Quadrature Encoder
void IRAM_ATTR encoder_isr() {
    int b = digitalRead(ENCODER_B_PIN);
    if (b > 0) {
        encoder_ticks++;
    } else {
        encoder_ticks--;
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(ENCODER_A_PIN, INPUT_PULLUP);
    pinMode(ENCODER_B_PIN, INPUT_PULLUP);
    pinMode(MOTOR_PWM_PIN, OUTPUT);
    pinMode(MOTOR_DIR_PIN, OUTPUT);

    // Attach hardware interrupt on pin 2
    attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), encoder_isr, RISING);
    Serial.println("Motor driver initialized.");
}

void loop() {
    // Non-blocking timer check (every 50ms)
    static unsigned long last_loop_time = 0;
    unsigned long current_time = millis();

    if (current_time - last_loop_time >= 50) {
        last_loop_time = current_time;

        // Read and reset tick count atomically
        noInterrupts();
        long ticks = encoder_ticks;
        interrupts();

        // Calculate velocity (ticks per 50ms)
        float velocity = (ticks * 1000.0) / 50.0;
        Serial.print("Velocity: ");
        Serial.println(velocity);
    }
}
