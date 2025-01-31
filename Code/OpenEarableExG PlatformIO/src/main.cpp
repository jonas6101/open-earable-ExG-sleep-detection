#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include "OpenEarable.h"
#include "NHB_AD7124.h"
#include "ArduinoBLE.h"

BLEService adcService("0029d054-23d0-4c58-a199-c6bdc16c4975");
// Updated: BLE characteristic can hold 20 bytes (4 for timestamp + 16 for floats)
BLECharacteristic adcCharacteristic("20a4a273-c214-4c18-b433-329f30ef7275", BLERead | BLENotify, 20);

Ad7124 adc(EPIN_SPI_CS, 8000000); // max sample rate: ~12100 SPS (when nothing printed on Serial, ~7080 when writing to Serial with 32 bit float)

float data[4] = {0.0}; // Reduced to 4 floats
int i = 0;

// Updated: Struct for BLE payload (includes timestamp and 4 floats)
struct BLEPayload {
  uint32_t timestamp;  // 4 bytes
  float readings[4];   // 16 bytes (4 floats)
};

BLEPayload payload;

// Sampling rate configuration
const uint16_t samplesPerSecondVal = 75; // 75 == 256 SPS

void updateBLE(float reading) {
  data[i] = reading;
  if (i == 3) { 
    payload.timestamp = millis(); // Include timestamp in the payload
    memcpy(payload.readings, data, sizeof(data)); 

    // Write payload to BLE characteristic
    adcCharacteristic.writeValue((byte*)&payload, sizeof(payload));
    memset(data, 0, sizeof(data)); // Clear data buffer
    i = 0;
  } else {
    i++;
  }
}

void readExternalADC() {
  float reading = (float)adc.readVolts(0);
  Serial.write((byte*)&reading, 4);
  Serial.write('\n');
  updateBLE(reading);
}

void measureSampleRate() {
  unsigned long startTime = millis();
  unsigned long endTime = startTime + 5000;
  unsigned long sampleCount = 0;

  while (millis() < endTime) {
    readExternalADC();
    sampleCount++;
  }

  double sampleRate = (double)sampleCount / 5.0;
  Serial.print("Achieved sample rate: ");
  Serial.print(sampleRate);
  Serial.println(" samples per second");
}

void setup() {
  Serial.begin(115200);
  open_earable.begin();

  adc.begin();
  adc.reset();
  adc.setAdcControl(AD7124_OpMode_Continuous, AD7124_FullPower, true);

  adc.setup[0].setConfig(AD7124_Ref_Internal, AD7124_Gain_1, true);
  adc.setup[0].setFilter(AD7124_Filter_SINC4, samplesPerSecondVal, AD7124_PostFilter_NoPost, false);
  adc.setChannel(0, 0, AD7124_Input_AIN1, AD7124_Input_AIN0, true);

  BLE.setAdvertisedService(adcService);
  adcService.addCharacteristic(adcCharacteristic);
  BLE.addService(adcService);
  adcCharacteristic.writeValue((byte*)&payload, sizeof(payload)); // Initialize BLE characteristic
  BLE.advertise();
}

void loop() {
  open_earable.update();
  readExternalADC();
}
