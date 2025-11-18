import pygame
import random
import sys
import time
import math
import os

GAME_MUSIC_LIST = [
    "BGmusik.mp3",
    "BGmusik2.mp3",
    "BGmusik3.mp3"
]

current_music_index = 0

# --- Konfigurasi awal ---
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Warna
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

camera_shake_timer = 0

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

# --- Helper highscore ---
def load_highscore():
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read())
    except:
        return 0

def save_highscore(score):
    try:
        with open("highscore.txt", "w") as f:
            f.write(str(score))
    except:
        pass

# === CLASSES ===

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, boss=False):
        super().__init__()
        self.x = x
        self.y = y
        self.boss = boss
        # Durasi
        self.timer = 40 if boss else 15
        # Surface size
        if boss:
            self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self.rect = self.image.get_rect()
        else:
            self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=(x, y))

        # debris
        self.debris = []
        if boss:
            count = 40
            speed_min, speed_max = 4, 12
            size_min, size_max = 3, 6
        else:
            count = 10
            speed_min, speed_max = 2, 5
            size_min, size_max = 2, 3

        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(speed_min, speed_max)
            size = random.randint(size_min, size_max)
            self.debris.append({
                "x": x,
                "y": y,
                "vx": speed * math.cos(angle),
                "vy": speed * math.sin(angle),
                "size": size,
                "alpha": 255
            })

        # smoke only for boss
        self.smoke = []
        if boss:
            for _ in range(25):
                self.smoke.append({
                    "x": x + random.randint(-20, 20),
                    "y": y + random.randint(-20, 20),
                    "size": random.randint(20, 60),
                    "alpha": 200
                })

        # flash
        self.flash_radius = 0
        self.flash_max = 120 if boss else 0

        # sound
        if boss:
            try:
                snd = pygame.mixer.Sound("boss_explosion.wav")
                snd.set_volume(0.9)
                snd.play()
            except Exception:
                pass

    def update(self):
        self.timer -= 1
        self.image.fill((0, 0, 0, 0))

        # flash
        if self.boss and self.flash_radius < self.flash_max:
            self.flash_radius += 6
            pygame.draw.circle(
                self.image, (255, 220, 120, 160),
                (self.x, self.y),
                self.flash_radius
            )

        # debris
        for d in self.debris:
            d["x"] += d["vx"]
            d["y"] += d["vy"]
            d["alpha"] -= 8
            if d["alpha"] > 0:
                pygame.draw.circle(
                    self.image,
                    (255, 140, 0, max(d["alpha"], 0)),
                    (int(d["x"]), int(d["y"])),
                    d["size"]
                )

        # smoke
        if self.boss:
            for s in self.smoke:
                s["y"] -= 0.3
                s["alpha"] -= 2
                s["size"] += 0.7
                pygame.draw.circle(
                    self.image,
                    (120, 120, 120, max(s["alpha"], 0)),
                    (int(s["x"]), int(s["y"])),
                    int(s["size"])
                )

        if self.timer <= 0:
            self.kill()


class BossLaser(pygame.sprite.Sprite):
    def __init__(self, boss):
        super().__init__()
        self.boss = boss
        self.width = 8
        self.height = SCREEN_HEIGHT
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((255, 80, 0))
        self.rect = self.image.get_rect(midtop=(boss.rect.centerx, 0))
        self.follow_speed = 0.15

    def update(self):
        target_x = self.boss.rect.centerx
        self.rect.centerx += int((target_x - self.rect.centerx) * self.follow_speed)


class Player(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        # store original image for alpha resets
        self.orig_image = pygame.transform.scale(img, (80, 80))
        self.image = self.orig_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10

        # HP system
        self.max_hp = 100
        self.hp = 100

        # invincibility & blink
        self.invincible = 0        # frames of invincibility after hit
        self.low_hp_warning = False
        self.blink = False
        self.blink_timer = 0

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

        # low HP warning
        if self.hp <= self.max_hp * 0.3:
            self.low_hp_warning = True
        else:
            self.low_hp_warning = False

        # blink logic (opacity)
        if self.low_hp_warning:
            self.blink_timer += 1
            if self.blink_timer % 20 < 10:
                self.blink = True
            else:
                self.blink = False
        else:
            self.blink = False

        # Apply alpha:
        # if invincible -> fast blink (hurt), else if low HP -> slow blink
        if self.invincible > 0:
            if self.invincible % 8 < 4:
                self.image = self.orig_image.copy()
                self.image.set_alpha(100)
            else:
                self.image = self.orig_image.copy()
                self.image.set_alpha(255)
        elif self.blink:
            self.image = self.orig_image.copy()
            self.image.set_alpha(90)
        else:
            self.image = self.orig_image.copy()
            self.image.set_alpha(255)

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
    # existing item (power-up spread)
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


class ItemHeal(pygame.sprite.Sprite):
    # heal item +30 HP
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((26, 26), pygame.SRCALPHA)
        # draw a small heart-like shape or simple green cross
        pygame.draw.rect(self.image, (0, 180, 0), (6, 6, 14, 14))
        pygame.draw.rect(self.image, (255,255,255), (6,6,14,14), 2)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = -30
        self.speedy = 3

    def update(self):
        self.rect.y += self.speedy
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

# --- UI: draw player HP bar ---
def draw_player_hp(screen, player):
    bar_width = 200
    bar_height = 18
    x = 10
    y = 10  # top-left

    fill = max(0, int(bar_width * (player.hp / player.max_hp)))
    # color based on HP
    if player.hp > 60:
        color = (0, 200, 0)   # green
    elif player.hp > 30:
        color = (240, 200, 0)  # yellow
    else:
        color = (220, 30, 30)  # red

    # background
    pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, color, (x, y, fill, bar_height))
    # border
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 2)

    # numeric
    font = pygame.font.SysFont(None, 20)
    txt = font.render(f"HP: {player.hp}/{player.max_hp}", True, WHITE)
    screen.blit(txt, (x + bar_width + 10, y))


# --- Screens ---
def splash_loading(screen):
    try:
        splash_img = pygame.image.load(resource_path("splash.png"))
        splash_img = pygame.transform.scale(splash_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except:
        splash_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        splash_img.fill((10, 10, 30))

    bar_width = 400
    bar_height = 25
    bar_x = (SCREEN_WIDTH - bar_width) // 2
    bar_y = SCREEN_HEIGHT - 80

    for progress in range(0, 101):
        screen.blit(splash_img, (0, 0))
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * (progress / 100), bar_height))
        font = pygame.font.Font(None, 40)
        text = font.render(f"Loading {progress}%", True, (255, 255, 255))
        screen.blit(text, (bar_x + 120, bar_y - 40))
        pygame.display.update()
        pygame.time.delay(6)

def start_game_music():
    global current_music_index

    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path(GAME_MUSIC_LIST[current_music_index]))
    pygame.mixer.music.play(-1)

    # maju ke lagu berikutnya (muter terus)
    current_music_index = (current_music_index + 1) % len(GAME_MUSIC_LIST)


def show_welcome_screen(screen, font, highscore, menu_bg):
    start_game_music()
    waiting = True

    while waiting:
        # Gambar background menu (di-scale biar pas layar)
        bg_scaled = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(bg_scaled, (0, 0))

        # Tampilkan
        pygame.display.flip()

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
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
    
    # warna button
    BTN_NORMAL = (80, 80, 80)
    BTN_HOVER = (140, 140, 140)
    BTN_TEXT = (255, 255, 255)

    # ukuran tombol
    button_width = 300
    button_height = 60

    # posisi tombol
    retry_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - button_width // 2,
        SCREEN_HEIGHT // 2 + 60,
        button_width,
        button_height
    )

    quit_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - button_width // 2,
        SCREEN_HEIGHT // 2 + 140,
        button_width,
        button_height
    )

    # animasi tulisan turun
    animate_text_down(screen, "GAME OVER", big_font, WHITE, SCREEN_HEIGHT // 4, speed=8)

    waiting = True
    while waiting:
        screen.fill(BLACK)

        # text
        over = big_font.render("GAME OVER", True, WHITE)
        skor = font.render(f"Skor Akhir: {score}", True, WHITE)
        hs_text = font.render(f"High Score: {highscore}", True, WHITE)

        screen.blit(over, (SCREEN_WIDTH // 2 - over.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(skor, (SCREEN_WIDTH // 2 - skor.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, SCREEN_HEIGHT // 2))

        # deteksi mouse
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        # --- BUTTON RETRY ---
        if retry_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, BTN_HOVER, retry_rect, border_radius=15)
            if mouse_click:
                return "retry"
        else:
            pygame.draw.rect(screen, BTN_NORMAL, retry_rect, border_radius=15)

        retry_text = font.render("MAIN LAGI", True, BTN_TEXT)
        screen.blit(retry_text, (retry_rect.centerx - retry_text.get_width() // 2,
                                 retry_rect.centery - retry_text.get_height() // 2))

        # --- BUTTON QUIT ---
        if quit_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, BTN_HOVER, quit_rect, border_radius=15)
            if mouse_click:
                return "quit"
        else:
            pygame.draw.rect(screen, BTN_NORMAL, quit_rect, border_radius=15)

        quit_text = font.render("KELUAR", True, BTN_TEXT)
        screen.blit(quit_text, (quit_rect.centerx - quit_text.get_width() // 2,
                                quit_rect.centery - quit_text.get_height() // 2))

        pygame.display.flip()

        # event quit aplikasi
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()



# === MAIN ===
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Shooter - HP Bar Edition")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    # load assets (with fallback)
    try:
        player_img = pygame.image.load(resource_path("Pesawat.png")).convert_alpha()
    except:
        player_img = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.polygon(player_img, (0, 150, 255), [(40,0),(0,80),(80,80)])

    try:
        enemy_img = pygame.image.load(resource_path("Musuh.png")).convert_alpha()
    except:
        enemy_img = pygame.Surface((70, 70))
        enemy_img.fill((200, 50, 50))

    try:
        boss_img = pygame.image.load(resource_path("Boss.png")).convert_alpha()
    except:
        boss_img = pygame.Surface((200, 200))
        boss_img.fill((100, 0, 120))

    try:
        menu_bg = pygame.image.load(resource_path("Tekan (3).png")).convert_alpha()
    except:
        menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        menu_bg.fill((20,20,40))

    try:
        bg_game = pygame.image.load(resource_path("bgGame.png")).convert_alpha()
    except:
        bg_game = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_game.fill((5, 5, 30))

    # sounds
    try:
        shoot_sound = pygame.mixer.Sound(resource_path("shoot.wav"))
        shoot_sound.set_volume(0.4)
    except:
        shoot_sound = None

    try:
        boss_explosion_sound = pygame.mixer.Sound(resource_path("boss_explosion.wav"))
        boss_explosion_sound.set_volume(0.9)
    except:
        boss_explosion_sound = None

    try:
        heal_sound = pygame.mixer.Sound(resource_path("heal.wav"))
        heal_sound.set_volume(0.5)
    except:
        heal_sound = None

    try:
        game_over_fx = pygame.mixer.Sound(resource_path("GameOverfx.wav"))
        game_over_fx.set_volume(0.5)
    except:
        game_over_fx = None

    explosions = pygame.sprite.Group()

    # background scroll
    bg_y1 = 0
    bg_y2 = -SCREEN_HEIGHT
    bg_speed = 3

    highscore = load_highscore()
    running = True

    # show splash
    splash_loading(screen)

    while running:
        # welcome
        result = None
        show_result = show_welcome_screen(screen, font, highscore, menu_bg)

        # Setup groups
        all_sprites = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        items = pygame.sprite.Group()      # includes Item (spread) and ItemHeal
        boss_lasers = pygame.sprite.Group()
        explosions = pygame.sprite.Group()

        player = Player(player_img)
        all_sprites.add(player)

        score = 0
        item_timer = 0
        enemy_timer = 0

        boss_spawned = False
        boss_stage = 1

        laser_delay = 5000
        laser_duration = 1500
        laser_last = pygame.time.get_ticks()
        laser_active = False
        laser_start_time = 0

        # spawn initial enemies
        for _ in range(5):
            e = Enemy(enemy_img)
            all_sprites.add(e)
            enemies.add(e)

        playing = True
        while playing:
            clock.tick(FPS)

            # events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if shoot_sound:
                        shoot_sound.play()
                    for b in player.shoot():
                        all_sprites.add(b)
                        bullets.add(b)

            # spawn heal item occasionally (small chance each frame)
            if random.randint(1, 1000) == 1:
                h = ItemHeal()
                all_sprites.add(h)
                items.add(h)

            # spawn regular item occasionally
            item_timer += 1
            if item_timer > 400:
                it = Item()
                all_sprites.add(it)
                items.add(it)
                item_timer = 0

            # spawn enemy small (cap)
            enemy_timer += 1
            if enemy_timer > 60 and len([e for e in enemies if not isinstance(e, Boss)]) < 5:
                new_enemy = Enemy(enemy_img)
                all_sprites.add(new_enemy)
                enemies.add(new_enemy)
                enemy_timer = 0

            # spawn boss every multiple of 300
            if score >= boss_stage * 300 and not boss_spawned:
                boss_hp = 80 + (boss_stage - 1) * 25
                boss = Boss(boss_img, boss_hp)
                all_sprites.add(boss)
                enemies.add(boss)
                boss_spawned = True

            # update
            all_sprites.update()

            # boss laser behaviour
            if boss_spawned:
                now = pygame.time.get_ticks()
                if not laser_active and now - laser_last > laser_delay:
                    laser = BossLaser(boss)
                    boss_lasers.add(laser)
                    laser_active = True
                    laser_start_time = now
                if laser_active and now - laser_start_time > laser_duration:
                    boss_lasers.empty()
                    laser_active = False
                    laser_last = now

            boss_lasers.update()

            # scrolling background
            bg_y1 += bg_speed
            bg_y2 += bg_speed
            if bg_y1 >= SCREEN_HEIGHT:
                bg_y1 = -SCREEN_HEIGHT
            if bg_y2 >= SCREEN_HEIGHT:
                bg_y2 = -SCREEN_HEIGHT

            # bullet hits
            hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
            for enemy in hits:
                # boss
                if isinstance(enemy, Boss):
                    enemy.hp -= 5
                    if enemy.hp <= 0:
                        # boss explosion sound
                        if boss_explosion_sound:
                            boss_explosion_sound.play()
                        boom = Explosion(enemy.rect.centerx, enemy.rect.centery, boss=True)
                        all_sprites.add(boom)
                        explosions.add(boom)
                        enemy.kill()
                        score += 150
                        boss_spawned = False
                        boss_stage += 1
                else:
                    # small enemy -> small explosion
                    small_explosion = Explosion(enemy.rect.centerx, enemy.rect.centery, boss=False)
                    all_sprites.add(small_explosion)
                    explosions.add(small_explosion)
                    enemy.kill()
                    score += 10
                    # spawn replacement
                    new_enemy = Enemy(enemy_img)
                    all_sprites.add(new_enemy)
                    enemies.add(new_enemy)

            # pick up items (both spread items and heal)
            item_hits = pygame.sprite.spritecollide(player, items, True)
            for it in item_hits:
                if isinstance(it, ItemHeal):
                    player.hp += 30
                    if player.hp > player.max_hp:
                        player.hp = player.max_hp
                    if heal_sound:
                        heal_sound.play()
                else:
                    # regular spread item
                    player.spread_mode = True
                    player.spread_timer = 300

            # enemy collision with player (damage)
            hit_enemy = pygame.sprite.spritecollide(player, enemies, True)
            if hit_enemy and player.invincible == 0:
                # small enemy collision damage (reduce hp by 15)
                player.hp -= 15
                player.invincible = 40

                # spawn small explosion(s) for the killed enemy(s)
                for _ in hit_enemy:
                    boom = Explosion(player.rect.centerx, player.rect.centery, boss=False)
                    all_sprites.add(boom)
                    explosions.add(boom)

            # laser collision (boss laser)
            if pygame.sprite.spritecollide(player, boss_lasers, False) and player.invincible == 0:
                player.hp -= 30
                player.invincible = 50

            # clamp hp
            if player.hp < 0:
                player.hp = 0

            # game over check
            if player.hp <= 0:
                pygame.mixer.music.stop()
                game_over_fx.play()
                playing = False

            # DRAW
            screen.blit(bg_game, (0, bg_y1))
            screen.blit(bg_game, (0, bg_y2))

            # draw all sprites (note explosion surfaces may be large)
            # To ensure explosions drawn on top, draw normal sprites first, then explosions
            # But all_sprites includes explosions; we can draw all_sprites, then explosions again is fine.
            all_sprites.draw(screen)
            boss_lasers.draw(screen)
            explosions.draw(screen)

            # draw boss hp bars (if any)
            for enemy in enemies:
                if isinstance(enemy, Boss):
                    bar_w = 150
                    fill = int(bar_w * (enemy.hp / enemy.max_hp))
                    bar_x = enemy.rect.centerx - bar_w // 2
                    bar_y = enemy.rect.y - 20
                    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, 10))
                    pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, fill, 10))

            # HUD: score & highscore & player HP bar
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 40))
            hs_text = font.render(f"High Score: {highscore}", True, WHITE)
            screen.blit(hs_text, (10, 70))

            draw_player_hp(screen, player)

            pygame.display.flip()

        # end playing loop -> update highscore and show game over screen
        if score > highscore:
            highscore = score
            save_highscore(highscore)

        result = show_game_over_screen(screen, font, score, highscore)
        if result == "quit":
            running = False
        elif result == "retry":
            continue

    pygame.quit()

if __name__ == "__main__":
    main()
