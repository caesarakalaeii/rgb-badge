#include <Arduino.h>
#include <FastLED.h>
#include "data/hamis.h"
#include "data/pride_flag.h"

#define MATRIX_WIDTH 10
#define MATRIX_HEIGHT 10
#define NUM_LEDS_PER_STRIP 50
#define LED_PIN_1 13
#define LED_PIN_2 12
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS 80

CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];

enum AnimationMode { MODE_HAMIS, MODE_PRIDE, MODE_COUNT };
uint8_t currentMode = MODE_HAMIS;
uint8_t currentFrame = 0;

unsigned long lastFrameTime = 0;
const int FRAME_DELAY = 150; // ms per frame

unsigned long lastModeSwitch = 0;
const unsigned long MODE_DURATION = 5000; // switch animation after x ms

// Forward declarations
void setPixel(int x, int y, CRGB color);
void drawFrame(const uint32_t* bitmap);

void setup()
{
  Serial.begin(115200);
  delay(500);
  Serial.println("Loading Bitmaps...");

  FastLED.addLeds<LED_TYPE, LED_PIN_1, COLOR_ORDER>(leds1, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, LED_PIN_2, COLOR_ORDER>(leds2, NUM_LEDS_PER_STRIP);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
}

void loop()
{
  unsigned long now = millis();

  if (now - lastFrameTime >= FRAME_DELAY)
  {
    lastFrameTime = now;
    
    const uint32_t* frameData = nullptr;
    
    if (currentMode == MODE_HAMIS)
    {
      // Hamis 👍
      if (currentFrame >= hamis_len) currentFrame = 0;
      frameData = (const uint32_t*)pgm_read_ptr(&hamis_frames[currentFrame]);
    } 
    else
    {
      // Pride Flag
      if (currentFrame >= pride_flag_len) currentFrame = 0;
      frameData = (const uint32_t*)pgm_read_ptr(&pride_flag_frames[currentFrame]);
    }

    if (frameData != nullptr)
    {
      drawFrame(frameData);
      FastLED.show();
      currentFrame++;
    }
  }

  if (now - lastModeSwitch >= MODE_DURATION)
  {
    lastModeSwitch = now;

    currentMode = (currentMode == MODE_HAMIS) ? MODE_PRIDE : MODE_HAMIS;
    currentFrame = 0; // Reset
  }
}

void drawFrame(const uint32_t* bitmap)
{
  for (int y = 0; y < MATRIX_HEIGHT; y++)
  {
    for (int x = 0; x < MATRIX_WIDTH; x++)
    {
      int index = y * MATRIX_WIDTH + x;
      
      uint32_t color32 = pgm_read_dword(&bitmap[index]);
      
      CRGB color;
      color.red   = (color32 >> 16) & 0xFF;
      color.green = (color32 >> 8) & 0xFF;
      color.blue  = color32 & 0xFF;
      
      setPixel(x, y, color);
    }
  }
}

void setPixel(int x, int y, CRGB color)
{
  if (x < 0 || x >= MATRIX_WIDTH || y < 0 || y >= MATRIX_HEIGHT) return;

  int ledIndex;

  if (y % 2 == 0)
  {
    ledIndex = y * MATRIX_WIDTH + x;
  }
  else
  {
    ledIndex = y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x);
  }

  if (ledIndex < NUM_LEDS_PER_STRIP)
  {
    leds1[ledIndex] = color;
  }
  else
  {
    leds2[ledIndex - NUM_LEDS_PER_STRIP] = color;
  }
}

// Bims was here
// Stay hydrated :D
