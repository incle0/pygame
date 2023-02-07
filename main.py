import pygame
import pytmx
import os
import csv
from os import listdir
from os.path import isfile, join

pygame.init()

WIDTH = 1400  # ширина игрового окна
HEIGHT = 900  # высота игрового окна
FPS = 60  # частота кадров в секунду
PLAYER_VEL = 5
MAPS_DIR = "maps"
ARIAL_50 = pygame.font.SysFont('arial', 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


class Menu:
    def __init__(self):
        self.option_surface = []
        self.callback = []
        self.current_index = 0

    def append_option(self, option, callback):
        self.option_surface.append(ARIAL_50.render(option, True, (255, 255, 255)))
        self.callback.append(callback)

    def switch(self, direction):
        self.current_index = max(0, min(self.current_index + direction,
                                        len(self.option_surface) - 1))  # для того что бы не выйти за границу массива

    def select(self):
        self.callback[self.current_index]()

    def draw(self, surf, x, y, option_y_padding):
        for i, option in enumerate(self.option_surface):
            option_rect = option.get_rect()
            option_rect.topleft = (x, y + i * option_y_padding)
            if i == self.current_index:
                pygame.draw.rect(surf, (0, 100, 0), option_rect)
            surf.blit(option, option_rect)


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, width, height, direction=False):
    path = join("data", dir1)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("data", "blocks.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(32, 32, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("Monkey", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mack = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 20
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "Idle"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "Jump"
        if self.x_vel != 0:
            sprite_sheet = "Run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        # self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_y):
        # self.sprite = self.SPRITES["Idle_" + self.direction][0]
        win.blit(self.sprite, (self.rect.x, self.rect.y - offset_y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offest_y):
        win.blit(self.image, (self.rect.x, self.rect.y - offest_y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    image = pygame.image.load(join("data", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_y):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_y)

    player.draw(window, offset_y)

    pygame.display.update()


def handle_verctical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

        collided_objects.append(obj)

    return collided_objects


def handle_move(player, objects):
    key = pygame.key.get_pressed()

    player.x_vel = 0
    if key[pygame.K_LEFT] or key[pygame.K_a]:
        player.move_left(PLAYER_VEL)
    if key[pygame.K_RIGHT] or key[pygame.K_d]:
        player.move_right(PLAYER_VEL)

    handle_verctical_collision(player, objects, player.y_vel)


go = 0


def letsgo():
    global go
    go += 1
    return go


def main_menu():
    global go
    camera = Camera()

    background, bg_image = get_background("2.jpg")
    block_size = 48

    player = Player(100, 100, 50, 50)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in
             range(-WIDTH // block_size, WIDTH * 2 // block_size)]

    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size),
               Block(block_size * 8, HEIGHT - block_size * 10, block_size),
               Block(block_size * 9, HEIGHT - block_size * 10, block_size),
               Block(block_size * 10, HEIGHT - block_size * 10, block_size),
               Block(block_size * 6, HEIGHT - block_size * 15, block_size),
               Block(block_size * 5, HEIGHT - block_size * 15, block_size), ]

    offset_y = 0
    scroll_area_height = 120
    clock = pygame.time.Clock()
    # map = Map("map.tmx", 1, 1)
    menu = Menu()
    menu.append_option("Start", letsgo)
    menu.append_option("Quit", quit)
    pygame.display.set_caption("Game")
    black = (0, 0, 0)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    menu.switch(-1)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    menu.switch(1)
                elif event.key == pygame.K_SPACE:
                    menu.select()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        if go == 0:
            screen.fill((0, 0, 0))
            menu.draw(screen, 100, 100, 75)
            pygame.display.flip()
        if go >= 1:
            player.loop(FPS)
            handle_move(player, objects)
            draw(screen, background, bg_image, player, objects, offset_y)

        if (player.rect.y - offset_y >= HEIGHT - scroll_area_height and player.y_vel < 0):
            offset_y += player.y_vel


# class Map:
#     def __init__(self, filename, free_tiles, finish_tile):
#         self.map = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")
#         self.height = self.map.height
#         self.width = self.map.width
#         self.tile_size = self.map.tilewidth
#         self.free_tiles = free_tiles
#         self.finish_tile = finish_tile
#
#     def render(self, screen):
#         for y in range(self.height):
#             for x in range(self.width):
#                 image = self.map.get_tile_image(x, y, 0)
#                 screen.blit(image, (x * self.tile_size, y * self.tile_size))
#
#     def get_tile_id(self, position):
#         return self.map.tiledgidmap[self.map.get_tile_gid(*position, 0)]
#
#     def is_free(self, position):
#         return self.get_tile_id(position) in self.free_tiles
#
#     def find_path_step(self, start, target):
#         INF = 1000
#         x, y = start
#         distance = [[INF] * self.width for _ in range(self.height)]
#         distance[y][x] = 0
#         prev = [[None] * self.width for _ in range(self.height)]
#         queue = [(x, y)]
#         while queue:
#             x, y = queue.pop(0)
#             for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):
#                 next_x, next_y = x + dx, y + dy
#                 if 0 <= next_x < self.width and 0 < next_y < self.height and self.is_free((next_x, next_y)) and \
#                         distance[next_y][next_x] == INF:
#                     distance[next_y][next_x] = distance[y][x] + 1
#                     prev[next_y][next_x] = (x, y)
#                     queue.append((next_x, next_y))
#         x, y = target
#         if distance[y][x] == INF or start == target:
#             return start
#         while prev[y][x] != start:
#             x, y = prev[y][x]
#         return x, y


main_menu()
pygame.quit()
