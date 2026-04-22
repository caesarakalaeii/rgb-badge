#include <FastLED.h>

// ============================================================================
// A Day in the Life of a Cat
// ----------------------------------------------------------------------------
// Multi-scene animation for a 10x10 WS2812B matrix (serpentine, two strips).
// Scenes cycle: blink -> laser chase -> pounce -> knock cup -> sleep -> repeat
// ============================================================================

#define MATRIX_WIDTH       10
#define MATRIX_HEIGHT      10
#define NUM_LEDS_PER_STRIP 50
#define LED_PIN_1          13
#define LED_PIN_2          12
#define LED_TYPE           WS2812B
#define COLOR_ORDER        GRB

CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];
CRGB frame[MATRIX_WIDTH][MATRIX_HEIGHT];

// Cat palette (ginger tabby, because they have the most personality)
const CRGB FUR         = CRGB(255, 110,  20);
const CRGB FUR_SHADE   = CRGB(140,  55,   8);
const CRGB FUR_BELLY   = CRGB(255, 180,  90);
const CRGB EYE_GREEN   = CRGB( 80, 255,  40);
const CRGB EYE_SLIT    = CRGB(255, 230,  60);
const CRGB NOSE        = CRGB(255, 100, 140);
const CRGB WHISKER     = CRGB( 80,  80,  80);
const CRGB LASER       = CRGB(255,   0,   0);
const CRGB LASER_GLOW  = CRGB(120,   0,   0);
const CRGB ZZZ         = CRGB( 90, 140, 255);
const CRGB CUP         = CRGB(120, 200, 255);
const CRGB TABLE       = CRGB( 90,  60,  30);
const CRGB DUST        = CRGB(200, 180, 120);

enum Scene {
  SCENE_FACE    = 0,
  SCENE_LASER   = 1,
  SCENE_POUNCE  = 2,
  SCENE_KNOCK   = 3,
  SCENE_SLEEP   = 4,
  SCENE_COUNT
};

const unsigned long SCENE_MS[SCENE_COUNT] = {
  5000,  // face / blinking
  7000,  // laser chase
  4500,  // pounce
  6000,  // knocking the cup off
  6500,  // sleeping
};

int           currentScene = SCENE_FACE;
unsigned long sceneStart   = 0;

// ---------------------------------------------------------------------------
// Frame buffer helpers
// ---------------------------------------------------------------------------

void clearFrame() {
  for (int x = 0; x < MATRIX_WIDTH; x++)
    for (int y = 0; y < MATRIX_HEIGHT; y++)
      frame[x][y] = CRGB::Black;
}

void putPixel(int x, int y, CRGB c) {
  if (x < 0 || x >= MATRIX_WIDTH || y < 0 || y >= MATRIX_HEIGHT) return;
  frame[x][y] = c;
}

// Serpentine mapping identical to the snake demo so this runs on the same hw.
void pushFrame() {
  for (int y = 0; y < MATRIX_HEIGHT; y++) {
    for (int x = 0; x < MATRIX_WIDTH; x++) {
      int idx = (y % 2 == 0)
              ? y * MATRIX_WIDTH + x
              : y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x);
      CRGB c = frame[x][y];
      if (idx < NUM_LEDS_PER_STRIP) leds1[idx] = c;
      else                          leds2[idx - NUM_LEDS_PER_STRIP] = c;
    }
  }
  FastLED.show();
}

// ---------------------------------------------------------------------------
// SCENE 1 — Big cat face with slow blinks and occasional slit-eye moods
// ---------------------------------------------------------------------------
// Sprite legend: 0=off  1=fur  2=belly  3=eye  4=nose  5=whisker
static const uint8_t CAT_FACE[10][10] = {
  {0,0,1,0,0,0,0,1,0,0},
  {0,1,1,1,0,0,1,1,1,0},
  {1,1,1,1,1,1,1,1,1,1},
  {1,1,1,1,1,1,1,1,1,1},
  {1,1,3,1,2,2,1,3,1,1},
  {1,1,1,2,2,2,2,1,1,1},
  {5,1,1,2,4,4,2,1,1,5},
  {5,1,1,1,2,2,1,1,1,5},
  {0,1,1,1,1,1,1,1,1,0},
  {0,0,1,1,1,1,1,1,0,0},
};

void drawCatFace(unsigned long t) {
  // Full blink every 2.5s, lasting ~180ms. Plus a slow "love blink" occasionally.
  unsigned long cycle = t % 2500;
  bool blinking = cycle < 180;
  // Every ~10s, the cat squints (slit eyes) for a beat.
  bool squint = (t % 10000) < 700 && !blinking;

  for (int y = 0; y < 10; y++) {
    for (int x = 0; x < 10; x++) {
      CRGB c = CRGB::Black;
      switch (CAT_FACE[y][x]) {
        case 1: c = FUR;        break;
        case 2: c = FUR_BELLY;  break;
        case 3: c = blinking ? FUR : (squint ? EYE_SLIT : EYE_GREEN); break;
        case 4: c = NOSE;       break;
        case 5: c = WHISKER;    break;
      }
      putPixel(x, y, c);
    }
  }

  // Purr: very subtle overall brightness pulse (chest rumbles)
  uint8_t purr = 230 + (uint8_t)(25.0 * sin(t / 180.0));
  for (int y = 0; y < 10; y++)
    for (int x = 0; x < 10; x++)
      frame[x][y].nscale8(purr);
}

// ---------------------------------------------------------------------------
// SCENE 2 — Laser chase: a 3x3 cat hunts a darting red dot
// ---------------------------------------------------------------------------
// The laser jitters with tiny darts plus occasional big teleports.
// The cat follows the laser with some delay and a springy overshoot.

struct V { float x, y; };

void drawLaserChase(unsigned long t) {
  static bool    initialised = false;
  static V       laser = {5, 5};
  static V       cat   = {1, 8};
  static uint32_t lastTeleport = 0;
  static uint32_t lastJitter   = 0;

  if (!initialised) {
    initialised = true;
    laser = {5, 5};
    cat   = {1, 8};
    lastTeleport = millis();
    lastJitter   = millis();
  }

  // Jitter the laser a bit every 80ms
  uint32_t now = millis();
  if (now - lastJitter > 80) {
    lastJitter = now;
    laser.x += (random(-100, 101) / 100.0f) * 1.2f;
    laser.y += (random(-100, 101) / 100.0f) * 1.2f;
  }
  // Every 700-1400ms the laser teleports somewhere fresh to taunt the cat
  if (now - lastTeleport > (uint32_t)random(700, 1400)) {
    lastTeleport = now;
    laser.x = random(0, MATRIX_WIDTH);
    laser.y = random(0, MATRIX_HEIGHT);
  }
  if (laser.x < 0) laser.x = 0;
  if (laser.x > 9) laser.x = 9;
  if (laser.y < 0) laser.y = 0;
  if (laser.y > 9) laser.y = 9;

  // Springy pursuit
  cat.x += (laser.x - cat.x) * 0.12f;
  cat.y += (laser.y - cat.y) * 0.12f;

  int cx = (int)round(cat.x);
  int cy = (int)round(cat.y);

  // 3x3 mini-cat: ears on top, body square, tail kink behind
  //   X . X        ears
  //   X X X        head/body
  //   . X .        paw
  static const int8_t mini[5][2] = {
    { 0, -1}, { 2, -1},             // ears
    { 0,  0}, { 1,  0}, { 2,  0},   // body
  };
  for (int i = 0; i < 5; i++) {
    putPixel(cx - 1 + mini[i][0], cy + mini[i][1], FUR);
  }
  // Tiny eyes on the middle row (x=cx-1+0 already fur; overwrite ears with eyes)
  putPixel(cx - 1, cy - 1, EYE_GREEN);
  putPixel(cx + 1, cy - 1, EYE_GREEN);
  // Wiggling tail behind the cat (opposite side from laser)
  int tailDir = (laser.x > cat.x) ? -1 : +1;
  int tailJog = ((t / 120) % 2) ? 0 : 1;
  putPixel(cx + 2 * tailDir,     cy,     FUR_SHADE);
  putPixel(cx + 2 * tailDir,     cy - tailJog, FUR_SHADE);

  // Laser glow + dot
  int lx = (int)round(laser.x);
  int ly = (int)round(laser.y);
  for (int dx = -1; dx <= 1; dx++)
    for (int dy = -1; dy <= 1; dy++)
      if (dx || dy) putPixel(lx + dx, ly + dy, LASER_GLOW);
  putPixel(lx, ly, LASER);
}

// ---------------------------------------------------------------------------
// SCENE 3 — Pounce: crouch, wiggle butt, leap in an arc, land
// ---------------------------------------------------------------------------

void drawCatSide(int baseX, int baseY, int crouch, bool airborne) {
  // crouch: 0 = standing, 1 = low crouch. airborne: stretched out flying pose.
  // Cat is drawn roughly 4 wide x 3 tall at baseX, baseY (feet row).
  if (airborne) {
    // Stretched flying pose: ===>
    putPixel(baseX + 0, baseY - 1, FUR);         // head
    putPixel(baseX + 1, baseY - 1, FUR);         // neck
    putPixel(baseX + 2, baseY - 1, FUR);         // back
    putPixel(baseX + 3, baseY - 1, FUR);         // hips
    putPixel(baseX + 4, baseY - 1, FUR_SHADE);   // tail
    putPixel(baseX + 0, baseY - 2, FUR);         // ear
    putPixel(baseX - 1, baseY - 1, EYE_GREEN);   // nose/eye tip
    // front + back legs tucked under
    putPixel(baseX + 1, baseY, FUR_SHADE);
    putPixel(baseX + 3, baseY, FUR_SHADE);
    return;
  }
  int bodyTop = baseY - 2 + crouch;             // lower body if crouched
  putPixel(baseX + 0, bodyTop, FUR);             // head
  putPixel(baseX + 0, bodyTop - 1, FUR);         // ear
  putPixel(baseX + 1, bodyTop, FUR);
  putPixel(baseX + 2, bodyTop, FUR);
  putPixel(baseX + 3, bodyTop, FUR);             // back
  putPixel(baseX + 3, bodyTop - 1, FUR_SHADE);   // tail base
  putPixel(baseX + 4, bodyTop - 1, FUR_SHADE);   // tail tip (up!)
  putPixel(baseX + 1, bodyTop + 1, FUR_SHADE);   // front leg
  putPixel(baseX + 3, bodyTop + 1, FUR_SHADE);   // back leg
  // eye
  putPixel(baseX, bodyTop, EYE_GREEN);
}

void drawPounce(unsigned long t) {
  // Timeline (ms):
  //   0 - 1200: crouching, butt wiggle
  //   1200 - 1350: tail flick (anticipation)
  //   1350 - 2500: airborne arc across the matrix
  //   2500 - 4500: landed, tail flicks proudly
  const int startX = 0;
  const int endX   = 6;
  const int groundY = 8;

  // Ground shadow pixel under the cat
  int shadowX = startX + 1;

  if (t < 1200) {
    int wiggle = ((t / 150) % 2) ? 0 : 1;
    drawCatSide(startX + wiggle, groundY, 1, false);
    putPixel(shadowX, groundY + 1, FUR_SHADE);
  } else if (t < 1350) {
    drawCatSide(startX, groundY, 0, false);  // stand up sharply
  } else if (t < 2500) {
    float u = (t - 1350) / 1150.0f;          // 0..1 arc
    int   x = (int)round(startX + u * (endX - startX));
    int   y = (int)round(groundY - 4.0f * sinf(u * 3.14159f));
    drawCatSide(x, y, 0, true);
    // motion blur dust at takeoff
    if (u < 0.2f) putPixel(startX, groundY + 1, DUST);
  } else {
    int tailWag = ((t / 200) % 2) ? 0 : 1;
    drawCatSide(endX, groundY, 0, false);
    // Proud tail flick overrides
    putPixel(endX + 4, groundY - 3 - tailWag, FUR_SHADE);
    // Landing dust cloud dissipates
    unsigned long since = t - 2500;
    if (since < 600) {
      uint8_t b = 255 - (uint8_t)((since * 255UL) / 600UL);
      CRGB d = DUST; d.nscale8(b);
      putPixel(endX, groundY + 1, d);
      putPixel(endX + 1, groundY + 1, d);
    }
  }
}

// ---------------------------------------------------------------------------
// SCENE 4 — Knocking the cup off the table (classic cat behaviour)
// ---------------------------------------------------------------------------

void drawKnock(unsigned long t) {
  const int tableY = 6;
  // Table surface
  for (int x = 0; x < 10; x++) putPixel(x, tableY, TABLE);
  // Table legs
  putPixel(1, tableY + 1, TABLE);
  putPixel(1, tableY + 2, TABLE);
  putPixel(8, tableY + 1, TABLE);
  putPixel(8, tableY + 2, TABLE);

  // Cat sits on the table, left side, facing right
  int catX = 0;
  drawCatSide(catX, tableY, 0, false);

  // Cup starts near the right edge; timeline:
  //   0 - 2000 : staring, judging the cup
  //   2000 - 2400 : paw extends (scene 4 highlight)
  //   2400 - ... : cup tumbles off with gravity
  int cupX = 7;
  int cupTopY = tableY - 1;

  if (t < 2000) {
    // stationary cup, cat stares
    putPixel(cupX,     cupTopY,     CUP);
    putPixel(cupX + 1, cupTopY,     CUP);
    putPixel(cupX,     cupTopY - 1, CUP);
    putPixel(cupX + 1, cupTopY - 1, CUP);
    // ears twitch
    if ((t / 300) % 2) putPixel(catX, tableY - 3, FUR);
  } else if (t < 2400) {
    // paw reaches out toward cup
    int reach = 1 + (t - 2000) / 100; // 1..5 pixels of extension
    for (int i = 0; i < reach; i++) {
      putPixel(catX + 3 + i, tableY - 1, FUR);
    }
    putPixel(cupX,     cupTopY,     CUP);
    putPixel(cupX + 1, cupTopY,     CUP);
    putPixel(cupX,     cupTopY - 1, CUP);
    putPixel(cupX + 1, cupTopY - 1, CUP);
  } else {
    // Cup falls; simple parabola, slides right & down off the edge
    float dt = (t - 2400) / 1000.0f;
    int fx = cupX + (int)(dt * 2.0f);
    int fy = cupTopY + (int)(0.5f * 9.8f * dt * dt);   // "gravity"
    putPixel(fx,     fy,     CUP);
    putPixel(fx + 1, fy,     CUP);
    putPixel(fx,     fy - 1, CUP);
    putPixel(fx + 1, fy - 1, CUP);
    // Cat leans over edge and looks down
    putPixel(catX + 4, tableY - 1, FUR);  // paw still out
    // Tilted head: shift eye down a pixel
    putPixel(catX, tableY - 1, EYE_GREEN);
  }
}

// ---------------------------------------------------------------------------
// SCENE 5 — Sleeping cat with floating Z's
// ---------------------------------------------------------------------------
// Curled-up cat filling the lower-middle of the matrix. Small "Z" glyphs
// drift upward from the cat's head and fade as they rise.

// 3x3 Z glyph:  XXX
//               .X.
//               XXX
static const uint8_t Z_GLYPH[3][3] = {
  {1,1,1},
  {0,1,0},
  {1,1,1},
};

void drawSleep(unsigned long t) {
  // Curled cat occupies rows 6-9.
  static const uint8_t CURL[4][10] = {
    //x: 0 1 2 3 4 5 6 7 8 9
       {0,0,1,1,1,1,1,1,0,0},  // y=6 back
       {0,1,1,2,2,2,2,1,1,1},  // y=7 body + belly + tail curl at x=9
       {1,1,3,1,2,2,1,1,1,0},  // y=8 closed eye (3 -> whisker/eyelid)
       {0,1,1,1,1,1,1,1,0,0},  // y=9 legs tucked
  };
  for (int dy = 0; dy < 4; dy++) {
    for (int x = 0; x < 10; x++) {
      uint8_t k = CURL[dy][x];
      CRGB c = CRGB::Black;
      if (k == 1) c = FUR;
      else if (k == 2) c = FUR_BELLY;
      else if (k == 3) c = WHISKER; // closed eye line
      putPixel(x, 6 + dy, c);
    }
  }

  // Gentle breathing: scale bottom rows by a slow sine
  float breath = 0.92f + 0.08f * sinf(t / 700.0f);
  for (int y = 6; y < 10; y++)
    for (int x = 0; x < 10; x++)
      frame[x][y].nscale8((uint8_t)(breath * 255));

  // Z's float up every ~1.3s, starting from the head (x=2,y=7) going up-right.
  const unsigned long Z_PERIOD = 1300;
  for (int i = 0; i < 2; i++) {
    long tz = (long)t - (long)(i * 650);   // staggered
    if (tz < 0) continue;
    unsigned long phase = ((unsigned long)tz) % Z_PERIOD;
    float u = phase / (float)Z_PERIOD;     // 0..1 rise
    int zx = 3 + (int)(u * 3.0f);
    int zy = 5 - (int)(u * 5.0f);
    uint8_t fade = (uint8_t)(255 * (1.0f - u));
    CRGB zc = ZZZ; zc.nscale8(fade);
    for (int gy = 0; gy < 3; gy++)
      for (int gx = 0; gx < 3; gx++)
        if (Z_GLYPH[gy][gx]) putPixel(zx + gx, zy + gy, zc);
  }
}

// ---------------------------------------------------------------------------
// Scene dispatch
// ---------------------------------------------------------------------------

void nextScene() {
  currentScene = (currentScene + 1) % SCENE_COUNT;
  sceneStart   = millis();
  Serial.printf("🐈 scene -> %d\n", currentScene);
}

void setup() {
  Serial.begin(115200);
  delay(100);

  FastLED.addLeds<LED_TYPE, LED_PIN_1, COLOR_ORDER>(leds1, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, LED_PIN_2, COLOR_ORDER>(leds2, NUM_LEDS_PER_STRIP);
  FastLED.setBrightness(60);
  FastLED.clear();
  FastLED.show();

  randomSeed(analogRead(0));
  sceneStart = millis();

  Serial.println("=== A Day in the Life of a Cat ===");
  Serial.println("Scenes: face -> laser -> pounce -> knock -> sleep");
}

void loop() {
  unsigned long now     = millis();
  unsigned long elapsed = now - sceneStart;

  clearFrame();

  switch (currentScene) {
    case SCENE_FACE:   drawCatFace(elapsed);    break;
    case SCENE_LASER:  drawLaserChase(elapsed); break;
    case SCENE_POUNCE: drawPounce(elapsed);     break;
    case SCENE_KNOCK:  drawKnock(elapsed);      break;
    case SCENE_SLEEP:  drawSleep(elapsed);      break;
  }

  pushFrame();

  if (elapsed >= SCENE_MS[currentScene]) nextScene();

  delay(25);
}
