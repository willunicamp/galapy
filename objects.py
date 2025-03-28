import pygame
import random
import math
import constants
from utils import load_image

# Carregar imagens
player_img = load_image("player.png", (50, 50))
enemy_img = load_image("enemy.png", (50, 50))
enemy2_img = load_image("enemy2.png", (50, 50))
agile_enemy_img = load_image("agile_enemy.png", (50, 50))
teleport_enemy_img = load_image("teleport.png", (50, 50))
bullet_img = pygame.Surface((5, 10))
bullet_img.fill(constants.WHITE)


teleport_animation = [load_image(f"teleport/t{i}.png", (50, 50)) for i in range(14)]

# Animação da bomba (82 frames)
bomb_animation = []
for i in range(82):
    frame_number = str(i).zfill(4)
    try:
        frame = pygame.image.load(f"bomb/frame{frame_number}.png")
        bomb_animation.append(pygame.transform.scale(frame, (360, 360)))
    except:
        surf = pygame.Surface((360, 360), pygame.SRCALPHA)
        progress = i / 81
        radius = int(180 * (1 if progress < 0.5 else 2 * (1 - progress)))
        alpha = int(255 * (1 - progress * 1.2))
        color = (255, max(0, 165 - int(165 * progress)), 0, alpha)
        pygame.draw.circle(surf, color, (180, 180), radius)
        bomb_animation.append(surf)

class Bomb:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.target_x = x
        self.target_y = max(50, y - 400)
        self.x = x
        self.y = y
        self.frames = bomb_animation
        self.current_frame = 0
        self.state = "moving"
        self.start_time = pygame.time.get_ticks()
        self.explosion_time = 0
        self.active = True

    def update(self):
        if not self.active:
            return False

        time_elapsed = pygame.time.get_ticks() - self.start_time

        if self.state == "moving":
            progress = min(1.0, time_elapsed / 200)
            progress = math.sin(progress * math.pi / 2)  # Efeito ease-out
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
            pygame.draw.circle(screen, constants.RED, (int(self.x), int(self.y)), 5)
        else:
            screen.blit(self.frames[self.current_frame], (self.x - 180, self.y - 180))

    def check_collision(self, enemies):
        if not self.active or self.state != "exploding" or self.current_frame < 2:
            return []
        return [enemy for enemy in enemies if self.rect_collision(enemy)]

    def rect_collision(self, enemy):
        return self.x - 180 <= enemy.rect.centerx <= self.x + 180 and self.y - 180 <= enemy.rect.centery <= self.y + 180

class Player:
    def __init__(self):
        self.rect = player_img.get_rect(midbottom=(constants.WIDTH // 2, constants.HEIGHT - 20))
        self.speed = 5
        self.bombs = 5
        self.score_for_bomb = 0

    def move(self, dx):
        self.rect.x = max(0, min(constants.WIDTH - self.rect.width, self.rect.x + dx * self.speed))

    def draw(self, screen, font):
        screen.blit(player_img, self.rect)
        bomb_text = font.render(f"Bombas: {self.bombs}", True, constants.WHITE)
        screen.blit(bomb_text, (constants.WIDTH - 120, 10))

    def add_score(self, points):
        self.score_for_bomb += points
        if self.score_for_bomb >= 100:
            self.bombs += 1
            self.score_for_bomb -= 100

class BaseEnemy:
    def __init__(self, x, y, speed, img):
        self.rect = img.get_rect(topleft=(x, y))
        self.y = float(y)
        self.speed = float(speed)
        self.image = img
        self.last_shot_time = pygame.time.get_ticks()

    def move(self):
        self.y += self.speed
        self.rect.y = round(self.y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def shoot(self, enemy_bullets):
        if pygame.time.get_ticks() - self.last_shot_time > 2000:
            enemy_bullets.append(Bullet(self.rect.centerx, self.rect.bottom, 5))
            self.last_shot_time = pygame.time.get_ticks()

class Enemy(BaseEnemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y, speed, enemy_img)

'''
class AgileEnemy(BaseEnemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y, speed, agile_enemy_img)

    def move(self, bullets=None):
        self.rect.y += 2
        if bullets:
            for bullet in bullets:
                if abs(self.rect.x - bullet.rect.x) < 50:
                    self.rect.x += self.speed if bullet.rect.x < self.rect.x else -self.speed
        self.rect.x = max(0, min(constants.WIDTH - self.rect.width, self.rect.x))
'''


class AgileEnemy(BaseEnemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y, speed, agile_enemy_img)  # Corrigir a chamada do super para incluir a imagem

    def move(self, bullets=None):
        self.rect.y += 2  # Movimentação vertical do inimigo

        if bullets:
            for bullet in bullets:
                # Calcular a distância entre o inimigo e a bala
                distance = math.sqrt((self.rect.centerx - bullet.rect.centerx) ** 2 + (self.rect.centery - bullet.rect.centery) ** 2)

                # Definir uma distância mínima para começar a desviar
                if distance < 150:  # Alterar este valor conforme necessário
                    if self.rect.centerx < bullet.rect.centerx:  # Se a bala está à direita
                        self.rect.x -= self.speed  # Desvia para a esquerda
                    elif self.rect.centerx > bullet.rect.centerx:  # Se a bala está à esquerda
                        self.rect.x += self.speed  # Desvia para a direita

        # Limitar a movimentação para que o inimigo não saia da tela
        self.rect.x = max(0, min(constants.WIDTH - self.rect.width, self.rect.x))

    def draw(self, screen):
        screen.blit(agile_enemy_img, self.rect)


class Enemy2(BaseEnemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y, speed, enemy2_img)
        self.angle = 0
        self.radius = 60
        self.center_x = x
        self.rotation_speed = 2

    def move(self):
        self.angle += self.rotation_speed
        self.y += self.speed
        self.rect.centerx = self.center_x + self.radius * math.sin(math.radians(self.angle))
        self.rect.centery = round(self.y)


class TeleportEnemy(BaseEnemy):
    def __init__(self):
        x = random.randint(0, constants.WIDTH - teleport_enemy_img.get_width())
        y = random.randint(0, constants.HEIGHT // 2)
        super().__init__(x, y, constants.INITIAL_ENEMY_SPEED , teleport_enemy_img)
        self.last_teleport_time = pygame.time.get_ticks()
        self.animation_state = "appearing"
        self.animation_frame = 0
        self.animation_start_time = pygame.time.get_ticks()
        self.alpha = 0  # Controle do fade-in

    def teleport(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_teleport_time > 2000 and self.animation_state == "active":
            self.animation_state = "disappearing"
            self.animation_frame = len(teleport_animation)
            self.animation_start_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        frame_duration = 45 # Tempo entre frames

        if self.animation_state == "appearing":
            if current_time - self.animation_start_time > frame_duration:
                self.animation_frame += 1
                self.animation_start_time = current_time
                if self.animation_frame >= len(teleport_animation):
                    self.animation_state = "active"
                    self.animation_frame = len(teleport_animation) - 1

        elif self.animation_state == "disappearing":
            if current_time - self.animation_start_time > frame_duration:
                self.animation_frame -= 1
                self.animation_start_time = current_time
                if self.animation_frame <= 0:
                    self.animation_state = "appearing"
                    self.animation_frame = 0
                    self.rect.x = random.randint(0, constants.WIDTH)
                    #self.rect.y = random.randint(0, constants.HEIGHT // 2)
                    self.last_teleport_time = current_time
                    self.alpha = 0  # Reset do fade-in

        self.alpha = min(255, (self.animation_frame / len(teleport_animation)) * 255)

    def draw(self, screen):
        image = teleport_animation[min(self.animation_frame, len(teleport_animation) - 1)].copy()
        image.set_alpha(self.alpha)
        screen.blit(image, self.rect)

    def move(self):
        self.y += self.speed
        self.rect.y = round(self.y)
        self.teleport()

'''
class TeleportEnemy(BaseEnemy):
    def __init__(self):
        x = random.randint(0, constants.WIDTH - teleport_enemy_img.get_width())
        y = random.randint(0, constants.HEIGHT // 2)
        super().__init__(x, y, constants.INITIAL_ENEMY_SPEED , teleport_enemy_img)
        self.last_teleport_time = pygame.time.get_ticks()

    def teleport(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_teleport_time > 2000:
            max_movement = constants.WIDTH // 4
            new_x = max(0, min(constants.WIDTH - self.rect.width, self.rect.x + random.randint(-max_movement, max_movement)))
            self.rect.x = new_x
            self.last_teleport_time = current_time

    def move(self):
        self.y += self.speed
        self.rect.y = round(self.y)
        self.teleport()
'''


# Modifique a classe Bullet para incluir a animação
class Bullet:
    def __init__(self, x, y, speed=-7, direction_x=0):
        self.rect = bullet_img.get_rect(midbottom=(x, y))
        self.speed = speed
        self.direction_x = direction_x

        # Propriedades para a animação de muzzle flash
        self.flash_start_time = pygame.time.get_ticks()
        self.showing_flash = True
        self.flash_frames = []

        # Cria os frames da animação (fallback se não carregar imagens)
        for i in range(constants.MUZZLE_FLASH_FRAMES):
            try:
                frame = pygame.image.load(f"muzzle_flash/muzzle_{i}.png")
                self.flash_frames.append(pygame.transform.scale(frame, (30, 30)))
            except:
                # Fallback - círculo amarelo-alaranjado que diminui
                surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                alpha = 255 - (i * 50)
                color = (255, 255, 255, alpha)
                radius = 15 - (i * 3)
                pygame.draw.circle(surf, color, (15, 15), radius)
                self.flash_frames.append(surf)

    def update_flash(self):
        if not self.showing_flash:
            return False

        elapsed = pygame.time.get_ticks() - self.flash_start_time
        frame_duration = constants.MUZZLE_FLASH_DURATION // constants.MUZZLE_FLASH_FRAMES

        # Termina a animação após o tempo total
        if elapsed > constants.MUZZLE_FLASH_DURATION:
            self.showing_flash = False
            return False

        return True

    def get_current_flash_frame(self):
        elapsed = pygame.time.get_ticks() - self.flash_start_time
        frame_index = min(
            constants.MUZZLE_FLASH_FRAMES - 1,
            elapsed // (constants.MUZZLE_FLASH_DURATION // constants.MUZZLE_FLASH_FRAMES)
        )
        return self.flash_frames[frame_index]

    def move(self):
        self.rect.y += self.speed
        self.rect.x += self.direction_x

    def draw(self, screen):
        # Desenha o flash primeiro (se ainda estiver ativo)
        if self.showing_flash and self.update_flash():
            flash_img = self.get_current_flash_frame()
            flash_pos = (
                self.rect.centerx - flash_img.get_width() // 2,
                self.rect.centery - flash_img.get_height() // 2
            )
            screen.blit(flash_img, flash_pos)

        # Desenha a bala
        screen.blit(bullet_img, self.rect)

'''
class Bullet:
    def __init__(self, x, y, speed=-7, direction_x=0):
        self.rect = bullet_img.get_rect(midbottom=(x, y))
        self.speed = speed
        self.direction_x = direction_x

    def move(self):
        self.rect.y += self.speed
        self.rect.x += self.direction_x

    def draw(self, screen):
        screen.blit(bullet_img, self.rect)

'''
