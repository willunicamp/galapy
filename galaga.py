import pygame
import random
import math
import os
from objects import Player, Enemy, Enemy2, Bullet, Bomb, AgileEnemy, TeleportEnemy
from utils import load_image
import constants

# Inicialização do Pygame
pygame.init()
screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))
pygame.display.set_caption("Galapy")




# Carrega o background (com fallback)
try:
    background = pygame.image.load("bgi2.jpg")
    background = pygame.transform.scale(background, (constants.WIDTH, constants.HEIGHT))
except:
    background = pygame.Surface((constants.WIDTH, constants.HEIGHT))
    background.fill((0, 0, 20))  # Fundo azul escuro como fallback
    # Adiciona estrelas como fallback
    for _ in range(100):
        x = random.randint(0, constants.WIDTH)
        y = random.randint(0, constants.HEIGHT)
        pygame.draw.circle(background, constants.WHITE, (x, y), 1)


# Fontes
font = pygame.font.Font(None, 24)
game_over_font = pygame.font.Font(None, 48)
wave_font = pygame.font.Font(None, 36)

def spawn_enemy():
    global enemy_speed, current_wave
    total_population = sum(enemy_population.values())
    choice = random.choices(
        population=["Enemy", "Enemy2", "AgileEnemy","TeleportEnemy"],
        weights=[enemy_population["Enemy"], enemy_population["Enemy2"],
                 enemy_population["AgileEnemy"],enemy_population["TeleportEnemy"]],
        k=1
    )[0]
    x = random.randint(50, constants.WIDTH - 50)
    y = random.randint(-200, -50)
    if choice == "Enemy":
        enemies.append(Enemy(x, y, enemy_speed))
    elif choice == "Enemy2":
        enemies.append(Enemy2(x, y, enemy_speed))
    elif choice == "TeleportEnemy":
        enemies.append(TeleportEnemy())
    else:
        enemies.append(AgileEnemy(x, y, enemy_speed))
    if score_hits >= current_wave * 10:
        enemy_speed += 0.5
        current_wave += 1

def update_population():
    global enemy_population
    for enemy in enemies:
        if enemy.rect.y > HEIGHT - 100:  # Se o inimigo chegou perto da base, ele "sobreviveu bem"
            enemy_population[type(enemy).__name__] += 1
        elif enemy in bullets:  # Se morreu rápido, reduz a frequência
            enemy_population[type(enemy).__name__] = max(1, enemy_population[type(enemy).__name__] - 1)


'''
def spawn_enemy():
    global enemy_speed, current_wave
    x = random.randint(50, constants.WIDTH - 50)
    y = random.randint(-200, -50)
    r = random.random()
    if r < 0.6:
        enemies.append(Enemy(x, y, enemy_speed))
    elif r < 0.9:
        enemies.append(Enemy2(x, y, enemy_speed))
    else:
        enemies.append(AgileEnemy(x, y, enemy_speed))
    if score_hits >= current_wave * 5:
        enemy_speed += constants.ENEMY_SPEED_INCREMENT
        current_wave += 1
'''

def reset_game():
    global player, enemies, bullets, enemy_bullets, bombs, last_shot_time, score_hits, score_misses, enemy_speed, running, last_spawn_time, current_wave, enemy_population

    player = Player()
    enemy_speed = constants.INITIAL_ENEMY_SPEED
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
    enemy_population = {"Enemy": 5, "Enemy2": 3, "AgileEnemy": 2,"TeleportEnemy": 3}  # Inicia população

    # Cria inimigos iniciais
    for _ in range(constants.MIN_ENEMIES):
        spawn_enemy()

def game_over_screen():
    screen.blit(background, (0, 0))

    # Overlay escuro para melhorar legibilidade
    overlay = pygame.Surface((constants.WIDTH, constants.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    text = game_over_font.render("GAME OVER", True, constants.WHITE)
    text_rect = text.get_rect(center=(constants.WIDTH // 2, constants.HEIGHT // 3))
    screen.blit(text, text_rect)

    score_text = wave_font.render(f"Pontuação: {score_hits}", True, constants.WHITE)
    score_rect = score_text.get_rect(center=(constants.WIDTH // 2, constants.HEIGHT // 2 - 30))
    screen.blit(score_text, score_rect)

    restart_text = font.render("Pressione R para reiniciar ou ESC para sair", True, constants.WHITE)
    restart_rect = restart_text.get_rect(center=(constants.WIDTH // 2, constants.HEIGHT // 2 + 30))
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
            if isinstance(enemy, AgileEnemy):
                enemy.move(bullets)
            else:
                enemy.move()

            if isinstance(enemy, TeleportEnemy):
                enemy.update()
            enemy.draw(screen)
            enemy.shoot(enemy_bullets)

            if enemy.rect.colliderect(player.rect):
                if game_over_screen():
                    return

            if enemy.rect.y > constants.HEIGHT:
                enemies.remove(enemy)
                score_misses += 1
                if score_misses >= 20:
                    if game_over_screen():
                        return

        # Spawn de novos inimigos
        current_time = pygame.time.get_ticks()
        if len(enemies) < constants.MIN_ENEMIES and current_time - last_spawn_time > constants.ENEMY_SPAWN_DELAY:
            spawn_enemy()
            last_spawn_time = current_time

        # Remove balas fora da tela
        bullets[:] = [b for b in bullets if b.rect.bottom >= 0]
        enemy_bullets[:] = [b for b in enemy_bullets if b.rect.top <= constants.HEIGHT]

        # Atualiza balas do jogador
        for bullet in bullets:
            bullet.move()
            bullet.draw(screen)
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
            bullet.draw(screen)
            if bullet.rect.colliderect(player.rect):
                if game_over_screen():
                    return

        # Desenha HUD
        player.draw(screen, font)

        # Painel de informações
        hud_bg = pygame.Surface((400, 80), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 150))
        screen.blit(hud_bg, (10, 10))

        score_text = font.render(f"Eliminadas: {score_hits}  Passaram: {score_misses}", True, constants.WHITE)
        screen.blit(score_text, (20, 20))

        wave_text = font.render(f"Onda: {current_wave}  Velocidade: {enemy_speed:.1f}", True, constants.WHITE)
        screen.blit(wave_text, (20, 50))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    while True:
        main()
