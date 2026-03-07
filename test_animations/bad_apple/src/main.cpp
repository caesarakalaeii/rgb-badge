#include <FastLED.h>
#include <LittleFS.h>

// LED Matrix Configuration
#define MATRIX_WIDTH 10
#define MATRIX_HEIGHT 10
#define NUM_LEDS_PER_STRIP 50
#define LED_PIN_1 13
#define LED_PIN_2 12
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

// Bad Apple Configuration
#define BA_BYTES_PER_FRAME 13
#define BA_FRAME_MS 50  // 20 FPS = 50ms per frame
#define DATA_FILE "/bad_apple_frames.bin"

// Color modes
enum ColorMode {
  MODE_CLASSIC = 0,     // Black and white
  MODE_RAINBOW = 1,     // Rainbow cycle
  MODE_PULSE = 2,       // Pulsing single color
  MODE_FIRE = 3,        // Fire effect
  MODE_MATRIX = 4,      // Matrix green
  MODE_OCEAN = 5,       // Ocean blue-cyan
  MODE_COUNT = 6
};

CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];

// Playback state
File dataFile;
uint16_t totalFrames = 0;
uint16_t currentFrame = 0;
uint8_t frameBuffer[BA_BYTES_PER_FRAME];
unsigned long lastFrameTime = 0;
uint8_t colorMode = MODE_RAINBOW;
uint8_t colorHue = 0;
bool playing = true;
bool loopVideo = true;

// Forward declarations
void setPixel(int x, int y, CRGB color);
bool readFrameHeader();
bool readFrame();
void displayFrame();
CRGB getColorForMode(bool pixelOn);
void nextColorMode();
void resetPlayback();

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n=================================");
  Serial.println("Bad Apple RGB Edition");
  Serial.println("10x10 LED Matrix");
  Serial.println("=================================\n");

  // Initialize LED strips
  FastLED.addLeds<LED_TYPE, LED_PIN_1, COLOR_ORDER>(leds1, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, LED_PIN_2, COLOR_ORDER>(leds2, NUM_LEDS_PER_STRIP);
  FastLED.setBrightness(80);
  FastLED.clear();
  FastLED.show();

  // Initialize filesystem
  Serial.println("Initializing LittleFS...");
  if (!LittleFS.begin(true)) {
    Serial.println("✗ LittleFS initialization failed!");
    Serial.println("\nPlease upload the data file:");
    Serial.println("  pio run --target uploadfs");
    Serial.println("  or");
    Serial.println("  arduino-cli upload -p /dev/ttyUSB0");

    // Show error pattern
    while (true) {
      fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Red);
      fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Red);
      FastLED.show();
      delay(500);
      FastLED.clear();
      FastLED.show();
      delay(500);
    }
  }
  Serial.println("✓ LittleFS initialized");

  // List files
  Serial.println("\nFiles in LittleFS:");
  File root = LittleFS.open("/");
  File file = root.openNextFile();
  while (file) {
    Serial.printf("  - %s (%d bytes)\n", file.name(), file.size());
    file = root.openNextFile();
  }

  // Open data file
  Serial.printf("\nOpening: %s\n", DATA_FILE);
  dataFile = LittleFS.open(DATA_FILE, "r");
  if (!dataFile) {
    Serial.println("✗ Failed to open data file!");
    Serial.println("\nMake sure you:");
    Serial.println("  1. Ran: python3 bad_apple_converter.py");
    Serial.println("  2. Uploaded data folder to SPIFFS");

    while (true) {
      fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Orange);
      fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Orange);
      FastLED.show();
      delay(1000);
      FastLED.clear();
      FastLED.show();
      delay(1000);
    }
  }

  Serial.printf("✓ File opened: %d bytes\n", dataFile.size());

  // Read header
  if (!readFrameHeader()) {
    Serial.println("✗ Failed to read header!");
    while (true) delay(1000);
  }

  Serial.println("\n=================================");
  Serial.printf("Ready to play %d frames\n", totalFrames);
  Serial.println("=================================");
  Serial.println("\nColor Modes (auto-cycles):");
  Serial.println("  0: Classic B&W");
  Serial.println("  1: Rainbow");
  Serial.println("  2: Pulse");
  Serial.println("  3: Fire");
  Serial.println("  4: Matrix");
  Serial.println("  5: Ocean");
  Serial.println("\nStarting playback...\n");

  delay(1000);
}

void loop() {
  unsigned long currentTime = millis();

  // Update color animations
  colorHue = (colorHue + 1) % 256;

  // Check if it's time for next frame
  if (playing && (currentTime - lastFrameTime >= BA_FRAME_MS)) {
    lastFrameTime = currentTime;

    if (readFrame()) {
      displayFrame();
      FastLED.show();

      currentFrame++;

      // Progress indicator
      if (currentFrame % 100 == 0) {
        float progress = (float)currentFrame / totalFrames * 100;
        Serial.printf("Frame %d/%d (%.1f%%) - Mode: %d\n",
                     currentFrame, totalFrames, progress, colorMode);
      }

      // Check if video ended
      if (currentFrame >= totalFrames) {
        Serial.println("\n✓ Video finished!");

        if (loopVideo) {
          Serial.println("Looping...\n");
          nextColorMode();  // Change color mode each loop
          resetPlayback();
        } else {
          playing = false;
          Serial.println("Playback stopped.");
        }
      }
    } else {
      Serial.println("✗ Error reading frame, resetting...");
      resetPlayback();
    }
  }

  delay(1);
}

bool readFrameHeader() {
  // Read 6-byte header
  uint8_t header[6];
  if (dataFile.read(header, 6) != 6) {
    return false;
  }

  // Parse header
  totalFrames = header[0] | (header[1] << 8);
  uint8_t fps = header[2];
  uint8_t width = header[3];
  uint8_t height = header[4];

  Serial.printf("\nHeader Info:\n");
  Serial.printf("  Frames: %d\n", totalFrames);
  Serial.printf("  FPS: %d\n", fps);
  Serial.printf("  Resolution: %dx%d\n", width, height);

  return (width == MATRIX_WIDTH && height == MATRIX_HEIGHT);
}

bool readFrame() {
  // Read one frame (13 bytes)
  size_t bytesRead = dataFile.read(frameBuffer, BA_BYTES_PER_FRAME);
  return (bytesRead == BA_BYTES_PER_FRAME);
}

void displayFrame() {
  // Clear display
  fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Black);
  fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Black);

  // Decode and display frame
  int pixelIndex = 0;

  for (int byteIndex = 0; byteIndex < BA_BYTES_PER_FRAME; byteIndex++) {
    uint8_t byte = frameBuffer[byteIndex];

    // Extract 8 pixels from this byte
    for (int bit = 7; bit >= 0; bit--) {
      if (pixelIndex >= (MATRIX_WIDTH * MATRIX_HEIGHT)) break;

      bool pixelOn = (byte & (1 << bit)) != 0;

      // Calculate x, y coordinates
      int x = pixelIndex % MATRIX_WIDTH;
      int y = pixelIndex / MATRIX_WIDTH;

      // Get color based on current mode
      CRGB color = pixelOn ? getColorForMode(true) : CRGB::Black;

      setPixel(x, y, color);
      pixelIndex++;
    }
  }
}

CRGB getColorForMode(bool pixelOn) {
  if (!pixelOn) return CRGB::Black;

  switch (colorMode) {
    case MODE_CLASSIC:
      // Classic black and white
      return CRGB::White;

    case MODE_RAINBOW:
      // Rainbow cycle
      return CHSV(colorHue, 255, 255);

    case MODE_PULSE: {
      // Pulsing purple/pink
      uint8_t brightness = 128 + 127 * sin(millis() / 200.0);
      return CHSV(200, 255, brightness);
    }

    case MODE_FIRE: {
      // Fire effect (red-orange-yellow)
      uint8_t heat = random(150, 255);
      uint8_t hue = random(0, 30);  // Red to yellow range
      return CHSV(hue, 255, heat);
    }

    case MODE_MATRIX:
      // Matrix green
      return CRGB::Green;

    case MODE_OCEAN: {
      // Ocean waves (blue-cyan)
      uint8_t wave = 128 + 127 * sin(millis() / 300.0 + colorHue);
      return CHSV(128 + (colorHue / 4), 255, wave);
    }

    default:
      return CRGB::White;
  }
}

void setPixel(int x, int y, CRGB color) {
  int ledIndex;

  // Serpentine layout
  if (y % 2 == 0) {
    ledIndex = y * MATRIX_WIDTH + x;
  } else {
    ledIndex = y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x);
  }

  // Split between two strips
  if (ledIndex < NUM_LEDS_PER_STRIP) {
    leds1[ledIndex] = color;
  } else {
    leds2[ledIndex - NUM_LEDS_PER_STRIP] = color;
  }
}

void nextColorMode() {
  colorMode = (colorMode + 1) % MODE_COUNT;
  Serial.printf("\n→ Color mode: %d\n", colorMode);
}

void resetPlayback() {
  // Seek back to start of frames (after header)
  dataFile.seek(6);
  currentFrame = 0;
  lastFrameTime = millis();
  Serial.println("↺ Playback reset");
}
