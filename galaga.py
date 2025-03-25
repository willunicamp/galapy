import pygame
import random
import math
import os

# Inicialização do Pygame
pygame.init()
WIDTH, HEIGHT = 600, 1200 # Nova resolução
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galapy")

# Cores
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Configurações do jogo
faculdades = ["USP", "Unicamp", "Unesp", "Fuvest", "UEL"]
MIN_ENEMIES = 5
MAX_ENEMIES = 10
ENEMY_SPAWN_DELAY = 2000  # 2 segundos entre spawns
ENEMY_SPEED_INCREMENT = 0.1
INITIAL_ENEMY_SPEED = 2.0

# Carregamento de imagens
def load_image(name, scale=None):
    try:
        img = pygame.image.load(name)
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except:
        # Fallback caso a imagem não exista
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        if "enemy" in name:
            pygame.draw.rect(surf, RED, (0, 0, 50, 50))
        elif "player" in name:
            pygame.draw.polygon(surf, WHITE, [(25, 0), (0, 50), (50, 50)])
        return surf

# Carrega o background (com fallback)
try:
    background = pygame.image.load("bgi2.jpg")
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except:
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((0, 0, 20))  # Fundo azul escuro como fallback
    # Adiciona estrelas como fallback
    for _ in range(100):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        pygame.draw.circle(background, WHITE, (x, y), 1)

player_img = load_image("player.png", (50, 50))
enemy_img = load_image("enemy.png", (50, 50))
enemy2_img = load_image("enemy2.png", (50, 50))
bullet_img = pygame.Surface((5, 10))
bullet_img.fill(WHITE)

# Animação da bomba (82 frames)
bomb_animation = []
for i in range(82):  # frame0000.png até frame0081.png
    frame_number = str(i).zfill(4)
    try:
        frame = pygame.image.load(f"bomb/frame{frame_number}.png")
        bomb_animation.append(pygame.transform.scale(frame, (360, 360)))
    except:
        # Fallback visual
        surf = pygame.Surface((360, 360), pygame.SRCALPHA)
        progress = i / 81
        radius = int(180 * (1 if progress < 0.5 else 2 * (1 - progress)))
        alpha = int(255 * (1 - progress * 1.2))
        color = (255, max(0, 165 - int(165 * progress)), 0, alpha)
        pygame.draw.circle(surf, color, (180, 180), radius)
        bomb_animation.append(surf)

# Fontes
font = pygame.font.Font(None, 24)
game_over_font = pygame.font.Font(None, 48)
wave_font = pygame.font.Font(None, 36)

# Classes do jogo
class Bomb:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.target_x = x
        self.target_y = max(50, y - 400)
        self.x = x
        self.y = y
        self.speed = 480
        self.frames = bomb_animation
        self.current_frame = 0
        self.state = "moving"
        self.start_time = pygame.time.get_ticks()
        self.explosion_time = 0
        self.active = True

    def update(self):
        if not self.active:
            return False

        if self.state == "moving":
            progress = min(1.0, (pygame.time.get_ticks() - self.start_time) / 200)
            self.x = self.start_x
            self.y = self.start_y + (self.target_y - self.start_y) * progress

            if progress >= 1.0:
                self.state = "exploding"
                self.explosion_time = pygame.time.get_ticks()

        elif self.state == "exploding":
            frame_time = pygame.time.get_ticks() - self.explosion_time
            self.current_frame = min(len(self.frames) - 1, frame_time // 30)

            if frame_time > 30 * len(self.frames):
                self.active = False
                return False

        return True

    def draw(self, screen):
        if not self.active:
            return

        if self.state == "moving":
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 5)
        else:
            if self.current_frame < len(self.frames):
                screen.blit(self.frames[self.current_frame], (self.x - 180, self.y - 180))

    def check_collision(self, enemies):
        if not self.active or self.state != "exploding" or self.current_frame < 2:
            return []

        hit_enemies = []
        for enemy in enemies[:]:
            distance = math.sqrt((enemy.rect.centerx - self.x)**2 + (enemy.rect.centery - self.y)**2)
            if distance <= 180:
                hit_enemies.append(enemy)
        return hit_enemies

class Player:
    def __init__(self):
        self.rect = player_img.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
        self.speed = 5
        self.bombs = 5
        self.score_for_bomb = 0

    def move(self, dx):
        self.rect.x += dx * self.speed
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

    def draw(self):
        screen.blit(player_img, self.rect)
        bomb_text = font.render(f"Bombas: {self.bombs}", True, WHITE)
        screen.blit(bomb_text, (WIDTH - 120, 10))

    def add_score(self, points):
        self.score_for_bomb += points
        if self.score_for_bomb >= 100:
            self.bombs += 1
            self.score_for_bomb -= 100

class Enemy:
    def __init__(self, x, y, speed):
        self.rect = enemy_img.get_rect(topleft=(x, y))
        self.y = float(y)
        self.speed = float(speed)
        self.nome = random.choice(faculdades)
        self.last_shot_time = pygame.time.get_ticks()

    def move(self):
        self.y += self.speed
        self.rect.y = round(self.y)

    def draw(self):
        screen.blit(enemy_img, self.rect)
        text_surface = font.render(self.nome, True, WHITE)
        text_rect = text_surface.get_rect(midbottom=(self.rect.centerx, self.rect.top - 5))
        screen.blit(text_surface, text_rect)

    def shoot(self, enemy_bullets):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > 2000:
            enemy_bullets.append(Bullet(self.rect.centerx, self.rect.bottom, 5))
            self.last_shot_time = current_time

class Enemy2:
    def __init__(self, x, y, speed):
        self.rect = enemy2_img.get_rect(topleft=(x, y))
        self.speed = float(speed)
        self.angle = 0
        self.radius = 60
        self.center_x = x
        self.y = float(y)
        self.rotation_speed = 2
        self.last_shot_time = pygame.time.get_ticks()

    def move(self):
        self.angle += self.rotation_speed
        self.y += self.speed
        self.rect.centerx = self.center_x + self.radius * math.sin(math.radians(self.angle))
        self.rect.centery = round(self.y)

    def draw(self):
        screen.blit(enemy2_img, self.rect)

    def shoot(self, enemy_bullets):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > 2000:
            direction_x = math.sin(math.radians(self.angle)) * 2
            enemy_bullets.append(Bullet(self.rect.centerx, self.rect.bottom, 5, direction_x))
            self.last_shot_time = current_time

class Bullet:
    def __init__(self, x, y, speed=-7, direction_x=0):
        self.rect = bullet_img.get_rect(midbottom=(x, y))
        self.speed = speed
        self.direction_x = direction_x

    def move(self):
        self.rect.y += self.speed
        self.rect.x += self.direction_x

    def draw(self):
        screen.blit(bullet_img, self.rect)
# Funções do jogo
def spawn_enemy():
    global enemy_speed, current_wave

    x = random.randint(50, WIDTH - 50)
    y = random.randint(-200, -50)

    # Aumenta a chance de inimigos difíceis conforme as ondas avançam
    hard_enemy_chance = min(0.5, 0.2 + (current_wave * 0.02))

    if random.random() < hard_enemy_chance:
        enemies.append(Enemy2(x, y, enemy_speed))
    else:
        enemies.append(Enemy(x, y, enemy_speed))

    # Aumenta a velocidade a cada 10 inimigos derrotados
    if score_hits >= current_wave * 10:
        enemy_speed += ENEMY_SPEED_INCREMENT
        current_wave += 1

def reset_game():
    global player, enemies, bullets, enemy_bullets, bombs, last_shot_time, score_hits, score_misses, enemy_speed, running, last_spawn_time, current_wave

    player = Player()
    enemy_speed = INITIAL_ENEMY_SPEED
    enemies = []
    bullets = []
    enemy_bullets = []
    bombs = []
    last_shot_time = 0
    last_spawn_time = 0
    score_hits = 0
    score_misses = 0
    current_wave = 1
    running = True

    # Cria inimigos iniciais
    for _ in range(MIN_ENEMIES):
        spawn_enemy()

def game_over_screen():
    screen.blit(background, (0, 0))

    # Overlay escuro para melhorar legibilidade
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    text = game_over_font.render("GAME OVER", True, WHITE)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(text, text_rect)

    score_text = wave_font.render(f"Pontuação: {score_hits}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
    screen.blit(score_text, score_rect)

    restart_text = font.render("Pressione R para reiniciar ou ESC para sair", True, WHITE)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
    screen.blit(restart_text, restart_rect)

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    return True
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

def main():
    global running, last_shot_time, score_hits, score_misses, last_spawn_time

    reset_game()
    clock = pygame.time.Clock()

    while running:
        # Desenha o background
        screen.blit(background, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.bombs > 0:
                    player.bombs -= 1
                    bombs.append(Bomb(player.rect.centerx, player.rect.centery))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            player.move(-1)
        if keys[pygame.K_d]:
            player.move(1)
        if keys[pygame.K_w] and pygame.time.get_ticks() - last_shot_time > 400:
            bullets.append(Bullet(player.rect.centerx, player.rect.top))
            last_shot_time = pygame.time.get_ticks()

        # Atualiza bombas
        for bomb in bombs[:]:
            if not bomb.update():
                bombs.remove(bomb)
            bomb.draw(screen)
            hit_enemies = bomb.check_collision(enemies)
            for enemy in hit_enemies:
                if enemy in enemies:
                    enemies.remove(enemy)
                    score_hits += 1
                    player.add_score(10)

        # Atualiza inimigos
        for enemy in enemies[:]:
            enemy.move()
            enemy.draw()
            enemy.shoot(enemy_bullets)

            if enemy.rect.colliderect(player.rect):
                if game_over_screen():
                    return

            if enemy.rect.y > HEIGHT:
                enemies.remove(enemy)
                score_misses += 1
                if score_misses >= 20:
                    if game_over_screen():
                        return

        # Spawn de novos inimigos
        current_time = pygame.time.get_ticks()
        if len(enemies) < MIN_ENEMIES and current_time - last_spawn_time > ENEMY_SPAWN_DELAY:
            spawn_enemy()
            last_spawn_time = current_time

        # Remove balas fora da tela
        bullets[:] = [b for b in bullets if b.rect.bottom >= 0]
        enemy_bullets[:] = [b for b in enemy_bullets if b.rect.top <= HEIGHT]

        # Atualiza balas do jogador
        for bullet in bullets:
            bullet.move()
            bullet.draw()
            for enemy in enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    enemies.remove(enemy)
                    bullets.remove(bullet)
                    score_hits += 1
                    player.add_score(10)
                    break

        # Atualiza balas inimigas
        for bullet in enemy_bullets:
            bullet.move()
            bullet.draw()
            if bullet.rect.colliderect(player.rect):
                if game_over_screen():
                    return

        # Desenha HUD
        player.draw()

        # Painel de informações
        hud_bg = pygame.Surface((400, 80), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 150))
        screen.blit(hud_bg, (10, 10))

        score_text = font.render(f"Eliminadas: {score_hits}  Passaram: {score_misses}", True, WHITE)
        screen.blit(score_text, (20, 20))

        wave_text = font.render(f"Onda: {current_wave}  Velocidade: {enemy_speed:.1f}", True, WHITE)
        screen.blit(wave_text, (20, 50))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    while True:
        main()
