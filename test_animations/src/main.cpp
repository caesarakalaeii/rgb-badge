#include <FastLED.h>

// LED Matrix Configuration
#define MATRIX_WIDTH 10
#define MATRIX_HEIGHT 10
#define NUM_LEDS_PER_STRIP 50  // Each strip has 50 LEDs (half of 100)
#define LED_PIN_1 13  // D13
#define LED_PIN_2 12  // D12
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

// Game Configuration
#define SNAKE_SPEED 150  // milliseconds between moves (faster for optimal play)
#define INITIAL_SNAKE_LENGTH 3

CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];

// Snake game variables
struct Point {
  int x;
  int y;
};

Point snake[100];
int snakeLength = INITIAL_SNAKE_LENGTH;
Point food;
int direction = 0; // 0=right, 1=down, 2=left, 3=up
CRGB snakeColor = CRGB::Green;
CRGB foodColor = CRGB::Red;
int colorHue = 0;  // For cycling through colors
unsigned long lastMoveTime = 0;
bool gameOver = false;
int highScore = INITIAL_SNAKE_LENGTH;
int foodEaten = 0;

// Forward declarations
void moveSnake();
void autoNavigate();
void checkCollisions();
void placeFood();
void displayGame();
void setPixel(int x, int y, CRGB color);
void gameOverAnimation();
void resetGame();
bool isSafe(int x, int y);
int getDirection(Point from, Point to);
bool findPathAStar(Point start, Point goal, Point path[], int &pathLength);
int manhattanDistance(Point a, Point b);
void getSafeNeighbors(Point current, Point neighbors[], int &count);
int getBestSafeDirection();

void setup() {
  Serial.begin(115200);

  // Initialize LED strips
  FastLED.addLeds<LED_TYPE, LED_PIN_1, COLOR_ORDER>(leds1, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, LED_PIN_2, COLOR_ORDER>(leds2, NUM_LEDS_PER_STRIP);
  FastLED.setBrightness(50);

  // Initialize snake in the middle
  for(int i = 0; i < snakeLength; i++) {
    snake[i].x = 5 - i;
    snake[i].y = 5;
  }

  // Place first food
  placeFood();

  Serial.println("Snake Game Started!");
  Serial.println("10x10 LED Matrix - Split across D13 and D12");
  Serial.println("AI Mode: Optimal Pathfinding (A*)");
  Serial.println("Goal: Survive as long as possible!\n");
}

void loop() {
  if(gameOver) {
    gameOverAnimation();
    delay(3000);
    resetGame();
    return;
  }

  // Cycle food color continuously
  colorHue = (colorHue + 1) % 256;
  foodColor = CHSV(colorHue, 255, 255);

  // Move snake at defined speed
  if(millis() - lastMoveTime > SNAKE_SPEED) {
    lastMoveTime = millis();
    moveSnake();
    checkCollisions();
  }

  // Update display
  displayGame();
  FastLED.show();
  delay(10);
}

void moveSnake() {
  // Calculate new head position
  Point newHead = snake[0];

  switch(direction) {
    case 0: newHead.x++; break; // right
    case 1: newHead.y++; break; // down
    case 2: newHead.x--; break; // left
    case 3: newHead.y--; break; // up
  }

  // Wrap around edges
  if(newHead.x < 0) newHead.x = MATRIX_WIDTH - 1;
  if(newHead.x >= MATRIX_WIDTH) newHead.x = 0;
  if(newHead.y < 0) newHead.y = MATRIX_HEIGHT - 1;
  if(newHead.y >= MATRIX_HEIGHT) newHead.y = 0;

  // Check if eating food
  bool ateFood = (newHead.x == food.x && newHead.y == food.y);

  if(ateFood) {
    // Snake grows and changes color to food color
    snakeColor = foodColor;
    snakeLength++;
    foodEaten++;
    placeFood();

    if(snakeLength > highScore) {
      highScore = snakeLength;
      Serial.printf("🏆 NEW HIGH SCORE: %d!\n", highScore);
    } else {
      Serial.printf("Food #%d eaten! Length: %d (High: %d)\n", foodEaten, snakeLength, highScore);
    }
  }

  // Move snake body
  for(int i = snakeLength - 1; i > 0; i--) {
    snake[i] = snake[i-1];
  }
  snake[0] = newHead;

  // Change direction automatically (simple AI for demo)
  autoNavigate();
}

void autoNavigate() {
  // Try A* pathfinding first
  Point path[100];
  int pathLength = 0;

  if(findPathAStar(snake[0], food, path, pathLength) && pathLength > 1) {
    // Follow the A* path
    direction = getDirection(snake[0], path[1]);
    return;
  }

  // Fallback: Pick the safest direction
  direction = getBestSafeDirection();
}

bool isSafe(int x, int y) {
  // Wrap coordinates
  if(x < 0) x = MATRIX_WIDTH - 1;
  if(x >= MATRIX_WIDTH) x = 0;
  if(y < 0) y = MATRIX_HEIGHT - 1;
  if(y >= MATRIX_HEIGHT) y = 0;

  // Check if position is occupied by snake body (not tail, as it will move)
  for(int i = 0; i < snakeLength - 1; i++) {
    if(snake[i].x == x && snake[i].y == y) {
      return false;
    }
  }
  return true;
}

int getDirection(Point from, Point to) {
  // Calculate direction from 'from' to 'to' considering wrap-around
  int dx = to.x - from.x;
  int dy = to.y - from.y;

  // Handle wrap-around
  if(abs(dx) > MATRIX_WIDTH/2) dx = dx > 0 ? dx - MATRIX_WIDTH : dx + MATRIX_WIDTH;
  if(abs(dy) > MATRIX_HEIGHT/2) dy = dy > 0 ? dy - MATRIX_HEIGHT : dy + MATRIX_HEIGHT;

  // Prioritize larger distance
  if(abs(dx) >= abs(dy)) {
    return (dx > 0) ? 0 : 2; // right or left
  } else {
    return (dy > 0) ? 1 : 3; // down or up
  }
}

int manhattanDistance(Point a, Point b) {
  int dx = abs(a.x - b.x);
  int dy = abs(a.y - b.y);

  // Handle wrap-around
  if(dx > MATRIX_WIDTH/2) dx = MATRIX_WIDTH - dx;
  if(dy > MATRIX_HEIGHT/2) dy = MATRIX_HEIGHT - dy;

  return dx + dy;
}

void getSafeNeighbors(Point current, Point neighbors[], int &count) {
  count = 0;

  // Four directions: right, down, left, up
  int dx[] = {1, 0, -1, 0};
  int dy[] = {0, 1, 0, -1};

  for(int i = 0; i < 4; i++) {
    int nx = current.x + dx[i];
    int ny = current.y + dy[i];

    // Wrap around
    if(nx < 0) nx = MATRIX_WIDTH - 1;
    if(nx >= MATRIX_WIDTH) nx = 0;
    if(ny < 0) ny = MATRIX_HEIGHT - 1;
    if(ny >= MATRIX_HEIGHT) ny = 0;

    if(isSafe(nx, ny)) {
      neighbors[count].x = nx;
      neighbors[count].y = ny;
      count++;
    }
  }
}

bool findPathAStar(Point start, Point goal, Point path[], int &pathLength) {
  // Simple A* implementation for small 10x10 grid
  const int MAX_NODES = 100;
  Point openSet[MAX_NODES];
  int openCount = 0;

  bool closedSet[MATRIX_WIDTH][MATRIX_HEIGHT] = {false};
  int gScore[MATRIX_WIDTH][MATRIX_HEIGHT];
  int fScore[MATRIX_WIDTH][MATRIX_HEIGHT];
  Point cameFrom[MATRIX_WIDTH][MATRIX_HEIGHT];
  bool hasParent[MATRIX_WIDTH][MATRIX_HEIGHT] = {false};

  // Initialize scores
  for(int i = 0; i < MATRIX_WIDTH; i++) {
    for(int j = 0; j < MATRIX_HEIGHT; j++) {
      gScore[i][j] = 10000;
      fScore[i][j] = 10000;
    }
  }

  // Start node
  openSet[0] = start;
  openCount = 1;
  gScore[start.x][start.y] = 0;
  fScore[start.x][start.y] = manhattanDistance(start, goal);

  while(openCount > 0) {
    // Find node with lowest fScore in openSet
    int currentIdx = 0;
    for(int i = 1; i < openCount; i++) {
      if(fScore[openSet[i].x][openSet[i].y] < fScore[openSet[currentIdx].x][openSet[currentIdx].y]) {
        currentIdx = i;
      }
    }

    Point current = openSet[currentIdx];

    // Check if we reached the goal
    if(current.x == goal.x && current.y == goal.y) {
      // Reconstruct path
      pathLength = 0;
      Point step = goal;
      while(hasParent[step.x][step.y]) {
        path[pathLength++] = step;
        step = cameFrom[step.x][step.y];
      }
      path[pathLength++] = start;

      // Reverse path
      for(int i = 0; i < pathLength / 2; i++) {
        Point temp = path[i];
        path[i] = path[pathLength - 1 - i];
        path[pathLength - 1 - i] = temp;
      }

      return true;
    }

    // Move current from open to closed
    closedSet[current.x][current.y] = true;
    for(int i = currentIdx; i < openCount - 1; i++) {
      openSet[i] = openSet[i + 1];
    }
    openCount--;

    // Check neighbors
    Point neighbors[4];
    int neighborCount = 0;
    getSafeNeighbors(current, neighbors, neighborCount);

    for(int i = 0; i < neighborCount; i++) {
      Point neighbor = neighbors[i];

      if(closedSet[neighbor.x][neighbor.y]) continue;

      int tentativeGScore = gScore[current.x][current.y] + 1;

      // Check if neighbor is in openSet
      bool inOpenSet = false;
      for(int j = 0; j < openCount; j++) {
        if(openSet[j].x == neighbor.x && openSet[j].y == neighbor.y) {
          inOpenSet = true;
          break;
        }
      }

      if(!inOpenSet) {
        if(openCount < MAX_NODES) {
          openSet[openCount++] = neighbor;
        }
      } else if(tentativeGScore >= gScore[neighbor.x][neighbor.y]) {
        continue;
      }

      // This path is the best so far
      cameFrom[neighbor.x][neighbor.y] = current;
      hasParent[neighbor.x][neighbor.y] = true;
      gScore[neighbor.x][neighbor.y] = tentativeGScore;
      fScore[neighbor.x][neighbor.y] = gScore[neighbor.x][neighbor.y] + manhattanDistance(neighbor, goal);
    }
  }

  // No path found
  return false;
}

int getBestSafeDirection() {
  // If A* fails, pick direction that maximizes space/distance from tail
  Point head = snake[0];
  int bestDir = direction; // Keep current direction as default
  int bestScore = -1;

  // Try all 4 directions
  int dx[] = {1, 0, -1, 0};
  int dy[] = {0, 1, 0, -1};

  for(int i = 0; i < 4; i++) {
    int nx = head.x + dx[i];
    int ny = head.y + dy[i];

    // Wrap around
    if(nx < 0) nx = MATRIX_WIDTH - 1;
    if(nx >= MATRIX_WIDTH) nx = 0;
    if(ny < 0) ny = MATRIX_HEIGHT - 1;
    if(ny >= MATRIX_HEIGHT) ny = 0;

    if(!isSafe(nx, ny)) continue;

    // Score based on distance to food and available space
    Point testPos = {nx, ny};
    int score = 0;

    // Prefer directions that lead toward food
    int distToFood = manhattanDistance(testPos, food);
    score += (50 - distToFood * 2); // Closer to food = better

    // Prefer directions with more space (count safe neighbors)
    Point neighbors[4];
    int count = 0;
    getSafeNeighbors(testPos, neighbors, count);
    score += count * 10; // More escape routes = better

    if(score > bestScore) {
      bestScore = score;
      bestDir = i;
    }
  }

  return bestDir;
}

void checkCollisions() {
  // Check if snake hits itself
  Point head = snake[0];
  for(int i = 1; i < snakeLength; i++) {
    if(head.x == snake[i].x && head.y == snake[i].y) {
      gameOver = true;
      Serial.println("\n════════════════════════════════");
      Serial.println("        GAME OVER");
      Serial.println("════════════════════════════════");
      Serial.printf("Final Length: %d\n", snakeLength);
      Serial.printf("Food Eaten: %d\n", foodEaten);
      Serial.printf("High Score: %d\n", highScore);
      Serial.printf("Coverage: %.1f%%\n", (snakeLength * 100.0) / (MATRIX_WIDTH * MATRIX_HEIGHT));
      Serial.println("════════════════════════════════\n");
      return;
    }
  }
}

void placeFood() {
  bool validPosition = false;
  while(!validPosition) {
    food.x = random(MATRIX_WIDTH);
    food.y = random(MATRIX_HEIGHT);

    // Check if food is on snake
    validPosition = true;
    for(int i = 0; i < snakeLength; i++) {
      if(food.x == snake[i].x && food.y == snake[i].y) {
        validPosition = false;
        break;
      }
    }
  }
}

void displayGame() {
  // Clear all LEDs
  fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Black);
  fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Black);

  // Draw snake
  for(int i = 0; i < snakeLength; i++) {
    // Fade tail
    int brightness = 255 - (i * 10);
    if(brightness < 50) brightness = 50;
    CRGB color = snakeColor;
    color.nscale8(brightness);

    setPixel(snake[i].x, snake[i].y, color);
  }

  // Draw food (pulsing effect)
  int foodBrightness = 128 + 127 * sin(millis() / 100.0);
  CRGB pulseFoodColor = foodColor;
  pulseFoodColor.nscale8(foodBrightness);
  setPixel(food.x, food.y, pulseFoodColor);
}

void setPixel(int x, int y, CRGB color) {
  // Convert x,y coordinates to LED index
  // Assuming serpentine/zigzag layout
  int ledIndex;

  if(y % 2 == 0) {
    // Even rows go left to right
    ledIndex = y * MATRIX_WIDTH + x;
  } else {
    // Odd rows go right to left
    ledIndex = y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x);
  }

  // Split between two strips
  if(ledIndex < NUM_LEDS_PER_STRIP) {
    leds1[ledIndex] = color;
  } else {
    leds2[ledIndex - NUM_LEDS_PER_STRIP] = color;
  }
}

void gameOverAnimation() {
  // Flash red a few times
  for(int i = 0; i < 3; i++) {
    fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Red);
    fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Red);
    FastLED.show();
    delay(300);

    fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Black);
    fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Black);
    FastLED.show();
    delay(300);
  }
}

void resetGame() {
  snakeLength = INITIAL_SNAKE_LENGTH;
  direction = 0;
  snakeColor = CRGB::Green;
  gameOver = false;
  foodEaten = 0;

  // Reset snake position
  for(int i = 0; i < snakeLength; i++) {
    snake[i].x = 5 - i;
    snake[i].y = 5;
  }

  placeFood();
  Serial.println("\n🔄 Game Reset - Trying again with optimal AI...\n");
}
