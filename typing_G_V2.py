import pygame
import random
import sys
import platform
import asyncio
import math

# Initialize Pygame
pygame.init()




# Screen setup
WIDTH, HEIGHT = 800, 800
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Shooter")
clock = pygame.time.Clock()

player_image = pygame.image.load("Pixel_Me.png").convert_alpha()
enemy_image = pygame.image.load("BurtPixel_shooter.png").convert_alpha()
laser_image = pygame.image.load("laser.png").convert_alpha()
# Optionally scale it to match the current laser size:
#laser_image = pygame.transform.scale(laser_image, (4, 4))  # Current laser size is 4x4 pixels



# Colors
WHITE = (255, 255, 255)
RED = (255, 100, 100)
BLACK = (0, 0, 0)
GREY = (50, 50, 50)
GREEN = (0, 255, 0)

# Font
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 48)

# Player setup
player_pos = [WIDTH // 2, HEIGHT - 50]  # List for mutable position
PLAYER_SIZE = 20
PLAYER_SPEED = 5

class Enemy:
    def __init__(self, word, x, y):
        self.word = word
        self.typed = ""
        self.x = x
        self.y = y
        self.speed = 1.5
        self.angle = math.atan2(player_pos[1] - y, player_pos[0] - x)  # Aim at player

    def draw(self, surface):
        surface.blit(enemy_image, (self.x - 15, self.y - 15))  # Centered on (self.x, self.y)

        typed_text = font.render(self.typed, True, RED)
        untyped_text = font.render(self.word[len(self.typed):], True, WHITE)
        text_y = self.y + 36 # <--- This controls how far below the enemy the word appears
        surface.blit(typed_text, (self.x - typed_text.get_width() // 2, text_y))
        surface.blit(untyped_text, (self.x - typed_text.get_width() // 2 + typed_text.get_width(), text_y))

    def update(self):
        # Move toward player
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def check_collision(self, player_x, player_y):
        # Simple rectangular collision detection
        enemy_rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)
        player_rect = pygame.Rect(player_x - PLAYER_SIZE, player_y - PLAYER_SIZE, PLAYER_SIZE * 2, PLAYER_SIZE * 2)
        return enemy_rect.colliderect(player_rect)

class Laser:
    def __init__(self, x, y, target_enemy):
        self.x = x
        self.y = y
        self.target = target_enemy
        self.speed = 10
        angle = math.atan2(target_enemy.y - y, target_enemy.x - x)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

    def update(self):
        self.x += self.dx
        self.y += self.dy
        # Check if laser hits target
        laser_rect = pygame.Rect(self.x - 2, self.y - 2, 4, 4)
        enemy_rect = pygame.Rect(self.target.x - 15, self.target.y - 15, 30, 30)
        return not laser_rect.colliderect(enemy_rect)

    def draw(self, surface):
        surface.blit(laser_image, (self.x - 2, self.y - 2))  # Centered on laser position

# Word enemy setup
def load_words_from_file(path):
    with open(path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

words = load_words_from_file("wordarray.txt")


def spawn_enemies(existing_words=None):
    if existing_words is None:
        existing_words = []

    enemies = []
    available_words = [w for w in words if w not in existing_words]
    num_to_spawn = min(5, len(available_words))
    min_distance = 100  # Minimum distance between ships, considering ship size and text width

    for _ in range(num_to_spawn):
        if not available_words:
            break
        attempts = 0
        max_attempts = 10
        placed = False
        while attempts < max_attempts and not placed:
            word = random.choice(available_words)
            x = random.randint(50, WIDTH - 50)
            y = -random.randint(50, 300)
            text_width = font.render(word, True, WHITE).get_width()
            # Check for overlap with existing enemies
            too_close = False
            for enemy in enemies:
                existing_text_width = font.render(enemy.word, True, WHITE).get_width()
                max_width = max(text_width, existing_text_width)
                dist = math.hypot(x - enemy.x, y - enemy.y)
                if dist < max_width + min_distance:
                    too_close = True
                    break
            if not too_close:
                enemies.append(Enemy(word, x, y))
                available_words.remove(word)
                placed = True
            attempts += 1

    return enemies

def draw_pause_menu():
    screen.fill(GREY)
    options = ["Resume (R)", "Restart (Enter)", "Quit (Q)"]
    for i, option in enumerate(options):
        text = big_font.render(option, True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 200 + i * 60))
    pygame.display.flip()

def draw_end_screen(score):
    screen.fill(BLACK)
    game_over_text = big_font.render("Game Over!", True, RED)
    score_text = big_font.render(f"Final Score: {score}", True, WHITE)
    restart_text = font.render("Press Enter to Restart", True, WHITE)
    quit_text = font.render("Press Q to Quit", True, WHITE)
    
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 150))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 350))
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, 400))
    pygame.display.flip()

async def game_loop():
    global current_enemy
    enemies = spawn_enemies()
    current_enemy = None
    lasers = []
    score = 0
    running = True
    paused = False
    game_over = False

    while running:
        if paused:
            draw_pause_menu()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        paused = False
                    elif event.key == pygame.K_RETURN:
                        enemies = spawn_enemies()
                        current_enemy = None
                        lasers = []
                        score = 0
                        player_pos[0] = WIDTH // 2
                        paused = False
                    elif event.key == pygame.K_q:
                        running = False
            await asyncio.sleep(1.0 / FPS)
            continue

        if game_over:
            draw_end_screen(score)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        enemies = spawn_enemies()
                        current_enemy = None
                        lasers = []
                        score = 0
                        player_pos[0] = WIDTH // 2
                        game_over = False
                    elif event.key == pygame.K_q:
                        running = False
            await asyncio.sleep(1.0 / FPS)
            continue

        screen.fill(BLACK)

        # Handle player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_pos[0] > PLAYER_SIZE:
            player_pos[0] -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] and player_pos[0] < WIDTH - PLAYER_SIZE:
            player_pos[0] += PLAYER_SPEED

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
                    continue

                key = event.unicode.lower()
                if current_enemy:
                    if len(current_enemy.typed) < len(current_enemy.word):
                        expected = current_enemy.word[len(current_enemy.typed)]
                        if key == expected:
                            current_enemy.typed += key
                            # Fire a laser
                            lasers.append(Laser(player_pos[0], player_pos[1], current_enemy))
                            if current_enemy.typed == current_enemy.word:
                                if current_enemy in enemies:
                                    enemies.remove(current_enemy)
                                    score += len(current_enemy.word) * 10
                                current_enemy = None
                        else:
                            pass
                else:
                    matching = [e for e in enemies if e.word.startswith(key)]
                    if matching:
                        closest = max(matching, key=lambda e: e.y)
                        closest.typed = key
                        current_enemy = closest
                        lasers.append(Laser(player_pos[0], player_pos[1], current_enemy))

        if not enemies:
            enemies = spawn_enemies([e.word for e in enemies])

        # Update and draw enemies
        for enemy in enemies[:]:
            enemy.update()
            enemy.draw(screen)
            # Check for collision with player
            if enemy.check_collision(player_pos[0], player_pos[1]):
                game_over = True
                break

        # Update and draw lasers
        for laser in lasers[:]:
            if laser.update():
                laser.draw(screen)
            else:
                lasers.remove(laser)

        # Draw player spaceship
       # pygame.draw.polygon(screen, WHITE, [
        #    (player_pos[0], player_pos[1] - PLAYER_SIZE),  # Top
         #   (player_pos[0] - PLAYER_SIZE, player_pos[1] + PLAYER_SIZE),  # Bottom left
          #  (player_pos[0] + PLAYER_SIZE, player_pos[1] + PLAYER_SIZE)  # Bottom right
        #])
        pygame.draw.circle(screen, GREEN, (player_pos[0], player_pos[1] - 5), 5)  # Cockpit

        # Draw player character image centered on player_pos
        player_rect = player_image.get_rect(center=(player_pos[0], player_pos[1]))
        screen.blit(player_image, player_rect)

        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

    pygame.quit()
    sys.exit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(game_loop())
else:
    if __name__ == "__main__":
        asyncio.run(game_loop())