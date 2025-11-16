try:
    import pyi_splash
    pyi_splash.close()
except:
    pass

import pygame
import random
import sys

# Inisialisasi
pygame.init()
pygame.mixer.init()

# Konstanta
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Warna
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# === HIGHSCORE ===
def load_highscore():
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read())
    except:
        return 0

def save_highscore(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))


# === KELAS ===

# === LASER BOSS (FOLLOW DELAY) ===
# === LASER BOSS (FOLLOW BOSS DENGAN DELAY) ===
class BossLaser(pygame.sprite.Sprite):
    def __init__(self, boss):
        super().__init__()
        self.boss = boss
        self.width = 8
        self.height = SCREEN_HEIGHT
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((255, 80, 0))
        self.rect = self.image.get_rect(midtop=(boss.rect.centerx, 0))

        self.follow_speed = 0.15  # Semakin kecil = delay lebih besar

    def update(self):
        # Laser mengikuti posisi boss, bukan player
        target_x = self.boss.rect.centerx
        self.rect.centerx += int((target_x - self.rect.centerx) * self.follow_speed)


class Player(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        self.hp = 3
        self.invincible = 0
        self.image = pygame.transform.scale(img, (80, 80))
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 6
        self.spread_mode = False
        self.spread_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

        if self.spread_mode:
            self.spread_timer -= 1
            if self.spread_timer <= 0:
                self.spread_mode = False

        if self.invincible > 0:
            self.invincible -= 1

    def shoot(self):
        bullets = []
        if self.spread_mode:
            bullets.append(Bullet(self.rect.centerx, self.rect.top, 0))
            bullets.append(Bullet(self.rect.centerx, self.rect.top, -3))
            bullets.append(Bullet(self.rect.centerx, self.rect.top, 3))
        else:
            bullets.append(Bullet(self.rect.centerx, self.rect.top, 0))
        return bullets


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 255, 200), (4, 4), 4)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10
        self.speedx = angle

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        self.image = pygame.transform.scale(img, (70, 70))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -50)
        self.speed = random.randint(2, 5)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Item(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 0), (10, 10), 10)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-200, -40)
        self.speed = 3

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Boss(pygame.sprite.Sprite):
    def __init__(self, img, hp):
        super().__init__()
        self.image = pygame.transform.scale(img, (200, 200))
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = -150
        self.hp = hp
        self.max_hp = hp
        self.speed = 3
        self.direction = 1

    def update(self):
        if self.rect.top < 20:
            self.rect.y += 2
        else:
            self.rect.x += self.speed * self.direction
            if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
                self.direction *= -1


# === ANIMASI & SCREEN ===
def show_welcome_screen(screen, font, highscore, menu_bg):
    waiting = True
    while waiting:
        screen.blit(pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False


def animate_text_down(screen, text, font, color, target_y, speed=7):
    y = -150
    render = font.render(text, True, color)

    while y < target_y:
        screen.fill((0, 0, 0))
        screen.blit(render, (SCREEN_WIDTH // 2 - render.get_width() // 2, y))
        pygame.display.update()
        y += speed
        pygame.time.delay(10)


def show_game_over_screen(screen, font, score, highscore):
    big_font = pygame.font.SysFont(None, 90)
    animate_text_down(screen, "GAME OVER", big_font, WHITE, SCREEN_HEIGHT // 4, speed=8)

    waiting = True
    while waiting:
        screen.fill(BLACK)

        over = big_font.render("GAME OVER", True, WHITE)
        skor = font.render(f"Skor Akhir: {score}", True, WHITE)
        hs_text = font.render(f"High Score: {highscore}", True, WHITE)
        retry = font.render("Tekan [M] untuk main lagi", True, WHITE)
        keluar = font.render("Tekan [K] untuk keluar", True, WHITE)

        screen.blit(over, (SCREEN_WIDTH // 2 - over.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(skor, (SCREEN_WIDTH // 2 - skor.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(retry, (SCREEN_WIDTH // 2 - retry.get_width() // 2, SCREEN_HEIGHT // 2 + 90))
        screen.blit(keluar, (SCREEN_WIDTH // 2 - keluar.get_width() // 2, SCREEN_HEIGHT // 2 + 140))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    waiting = False
                elif event.key == pygame.K_k:
                    pygame.quit()
                    sys.exit()


# === GAME UTAMA ===
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Shooter - Spread Mode")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    player_img = pygame.image.load("Pesawat.png").convert_alpha()
    enemy_img = pygame.image.load("Musuh.png").convert_alpha()
    boss_img = pygame.image.load("Boss.png").convert_alpha()
    menu_bg = pygame.image.load("Tekan (3).png").convert()
    bg_game = pygame.image.load("bgGame.png").convert()

    # Background scroll
    bg_y1 = 0
    bg_y2 = -SCREEN_HEIGHT
    bg_speed = 3

    highscore = load_highscore()
    running = True

    while running:

        show_welcome_screen(screen, font, highscore, menu_bg)

        all_sprites = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        items = pygame.sprite.Group()
        boss_lasers = pygame.sprite.Group()

        player = Player(player_img)
        all_sprites.add(player)

        score = 0
        item_timer = 0
        enemy_timer = 0

        boss_spawned = False
        boss_stage = 1

        # Laser boss
        laser_delay = 5000
        laser_duration = 1500
        laser_last = pygame.time.get_ticks()
        laser_active = False
        laser_start_time = 0

        # Spawn awal musuh
        for _ in range(5):
            e = Enemy(enemy_img)
            all_sprites.add(e)
            enemies.add(e)

        playing = True
        while playing:
            clock.tick(FPS)

            # Event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    for b in player.shoot():
                        all_sprites.add(b)
                        bullets.add(b)

            # Spawn item
            item_timer += 1
            if item_timer > 300:
                item = Item()
                all_sprites.add(item)
                items.add(item)
                item_timer = 0

            # Spawn musuh
            enemy_timer += 1
            if enemy_timer > 60 and len(enemies) < 5:
                new_enemy = Enemy(enemy_img)
                all_sprites.add(new_enemy)
                enemies.add(new_enemy)
                enemy_timer = 0

            # SPAWN BOSS SETIAP KELIPATAN 300
            if score >= boss_stage * 300 and not boss_spawned:
                boss_hp = 50 + (boss_stage - 1) * 20
                boss = Boss(boss_img, boss_hp)
                all_sprites.add(boss)
                enemies.add(boss)
                boss_spawned = True

            # Update semua
            all_sprites.update()

            # === LASER BOSS ATTACK ===
            if boss_spawned:
                now = pygame.time.get_ticks()

                # Mulai laser
                if not laser_active and now - laser_last > laser_delay:
                    laser = BossLaser(boss)
                    boss_lasers.add(laser)
                    laser_active = True
                    laser_start_time = now

                # Matikan laser
                if laser_active and now - laser_start_time > laser_duration:
                    boss_lasers.empty()
                    laser_active = False
                    laser_last = now

            boss_lasers.update()

            # Scroll background
            bg_y1 += bg_speed
            bg_y2 += bg_speed
            if bg_y1 >= SCREEN_HEIGHT:
                bg_y1 = -SCREEN_HEIGHT
            if bg_y2 >= SCREEN_HEIGHT:
                bg_y2 = -SCREEN_HEIGHT

            # Hit musuh
            hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
            for enemy in hits:
                if isinstance(enemy, Boss):
                    enemy.hp -= 5
                    if enemy.hp <= 0:
                        enemy.kill()
                        score += 150
                        boss_spawned = False
                        boss_stage += 1
                else:
                    enemy.kill()
                    score += 10
                    new_enemy = Enemy(enemy_img)
                    all_sprites.add(new_enemy)
                    enemies.add(new_enemy)

            # Hit item
            item_hits = pygame.sprite.spritecollide(player, items, True)
            for _ in item_hits:
                player.spread_mode = True
                player.spread_timer = 300

            # Hit pemain oleh musuh
            hit_enemy = pygame.sprite.spritecollide(player, enemies, True)
            if hit_enemy and player.invincible == 0:
                player.hp -= 1
                player.invincible = 60

            # Hit pemain oleh laser boss
            if pygame.sprite.spritecollide(player, boss_lasers, False) and player.invincible == 0:
                player.hp -= 2
                player.invincible = 60

            # GAME OVER
            if player.hp <= 0:
                playing = False

            # RENDER
            screen.blit(bg_game, (0, bg_y1))
            screen.blit(bg_game, (0, bg_y2))

            all_sprites.draw(screen)
            boss_lasers.draw(screen)

            # HP BOSS
            for enemy in enemies:
                if isinstance(enemy, Boss):
                    bar_w = 150
                    fill = int(bar_w * (enemy.hp / enemy.max_hp))
                    bar_x = enemy.rect.centerx - bar_w // 2
                    bar_y = enemy.rect.y - 20
                    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, 10))
                    pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, fill, 10))

            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))

            hs_text = font.render(f"High Score: {highscore}", True, WHITE)
            screen.blit(hs_text, (10, 40))

            hp_text = font.render(f"HP: {player.hp}", True, WHITE)
            screen.blit(hp_text, (10, 70))

            pygame.display.flip()

        # UPDATE HIGHSCORE
        if score > highscore:
            highscore = score
            save_highscore(highscore)

        show_game_over_screen(screen, font, score, highscore)

    pygame.quit()


if __name__ == "__main__":
    main()
