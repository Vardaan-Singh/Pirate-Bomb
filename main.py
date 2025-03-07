import csv
import pygame
import os
import random

pygame.init()


# Screen dimensions
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Pirate Bomb')


# Game variables
GRAVITY = 0.75
FPS = 60
TILE_SIZE = 45
img_list = []
TILE_TYPES = 32
for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/Tiles/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
ROWS = 16
COLS = 150
level = 0


# Colors
BG_COLOR = (144, 201, 120)


# Clock for controlling the frame rate
clock = pygame.time.Clock()


# Player movement variables
moving_right = False
moving_left = False


# Load bomb off image
bomb_off = pygame.image.load('Sprites/7-Objects/1-BOMB/1-Bomb Off/1.png').convert_alpha()
bomb_off = pygame.transform.scale(bomb_off, (int(bomb_off.get_width() * 1.5), int(bomb_off.get_height() * 1.5)))


# Camera class
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Offset an entity's position by the camera's position
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        # Offset a generic rectangle by the camera's position
        return rect.move(self.camera.topleft)

    def update(self, target):
        # Target is usually the player
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2

        # Clamp the camera so it doesn't go out of bounds
        x = max(-(self.width - SCREEN_WIDTH), min(0, x))
        y = max(-(self.height - SCREEN_HEIGHT), min(0, y))

        self.camera = pygame.Rect(x, y, self.width, self.height)

# player
class PLAYER(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, health):
        super().__init__()
        self.is_alive = True
        self.char_type = char_type
        self.speed = speed
        self.health = health
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        self.get_hurt = False
        self.drop_bomb = False

        # Bomb charging variables
        self.charging = False
        self.charge_start_time = 0
        self.charge_duration = 0
        self.charge_images = []

        # ai specific variables
        self.moving_counter = 0
        self.vision = pygame.Rect(0, 0, TILE_SIZE * 6, 20)
        self.idling = False
        self.idling_counter = 100
        self.attack_timer = 0
        self.velocity = pygame.Vector2(0, 0)

        for i in range(1, 12):  # Load 11 images
            img = pygame.image.load(f'Sprites/7-Objects/3-Bomb Bar/1-Charging Bar/{i}.png').convert_alpha()
            self.charge_images.append(img)
        self.charge_index = 0

        # Load all images for the player
        animation_types = ['Idle', 'Run', 'Jump', 'Hit', 'Dead Hit', 'Attack', 'Swalow (Bomb)', 'Blow the wick']
        for animation in animation_types:
            try:
                temp_list = []
                num_of_frames = len(os.listdir(f'Sprites/{self.char_type}/{animation}'))
                for i in range(1, num_of_frames):
                    img = pygame.image.load(f'Sprites/{self.char_type}/{animation}/{i}.png').convert_alpha()
                    img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                    temp_list.append(img)
                self.animation_list.append(temp_list)
            except Exception as e:
                None
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        if not self.is_alive:
            self.update_animation()
            return

        self.update_animation()
        if self.charging:
            self.update_charge_bar()

        # Update the bomb's position based on velocity
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # Add friction or stop the bomb if needed
        self.velocity *= 0.9  # Slow down over time
        if abs(self.velocity.x) < 0.1:
            self.velocity.x = 0

    def update_charge_bar(self):
        # Calculate the charge level based on how long the F key is held
        self.charge_duration = pygame.time.get_ticks() - self.charge_start_time
        charge_level = min(self.charge_duration // 100, 10)  # Max level is 10
        self.charge_index = charge_level

        # Draw the charge bar above the player's head
        if self.charge_index < len(self.charge_images):
            bar_image = self.charge_images[self.charge_index]
            bar_rect = bar_image.get_rect(center=(self.rect.centerx, self.rect.top - 10))
            screen.blit(bar_image, camera.apply_rect(bar_rect))

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 4:  # If Dead Hit animation finishes, stay on the last frame
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
            self.get_hurt = False

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), camera.apply(self))

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def move(self, moving_left, moving_right):
        dx = 0
        dy = 0

        if moving_left:
            dx = -self.speed
            if self.char_type == '6-Enemy-Whale': self.flip = False
            else: self.flip = True
            self.direction = -1

        if moving_right:
            dx = self.speed
            if self.char_type == '6-Enemy-Whale': self.flip = True
            else: self.flip = False
            self.direction = 1

        # Jump
        if self.jump and not self.in_air:
            self.vel_y = -17
            self.jump = False
            self.in_air = True

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        # Check for Collision
        for tile in world.obstacle_list:
            # check collision in x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                self.velocity.x = 0
                if moving_left:
                    self.rect.left = tile[1].right
                if moving_right:
                    self.rect.right = tile[1].left
            # check for collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                dy = 0
                self.in_air = False

        # Update rectangle position
        self.rect.x += dx
        self.rect.y += dy


    def draw_health(self):
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, 'BLACK', (self.rect.x - 2, self.rect.y - 2, 54, 9))
        pygame.draw.rect(screen, 'RED', (self.rect.x, self.rect.y, 50, 5))
        pygame.draw.rect(screen, 'GREEN', (self.rect.x, self.rect.y, 50 * ratio, 5))


    def AI(self, player):
        if self.is_alive and player.is_alive:
            # Handle idle behavior
            if self.idling:
                self.update_action(0)  # Idle animation
                self.idling_counter -= 1
                if self.idling_counter <= 0:
                    self.idling = False
                else:
                    return  # Skip the rest if idling

            # Check for bombs in vision range
            for bomb in bomb_group:
                if self.vision.colliderect(bomb.rect):
                    # If far enough, move toward the bomb
                    if abs(self.rect.centerx - bomb.rect.centerx) >= bomb.rect.width / 2:
                        self.direction = 1 if self.rect.centerx < bomb.rect.centerx else -1
                        self.rect.x += self.speed * self.direction
                        self.update_action(1)  # Running animation
                    else:
                        # Attack the bomb if close
                        self.update_action(5)  # Attack animation
                        if self.frame_index >= 5:
                            bomb.rect.x += self.direction * TILE_SIZE * 2  # Push the bomb
                            bomb.vel_y -= TILE_SIZE * 0.5  # Apply vertical force
                            self.attack_timer = 30                    
                        
                    return  # Exit after interacting with bomb
                

            # Handle attack cooldown
            if self.attack_timer > 0:
                self.attack_timer -= 1

            # Check if the player is within vision
            if self.vision.colliderect(player.rect):
                # Move toward the player if far enough
                if abs(self.rect.centerx - player.rect.centerx) >= player.rect.width / 2:
                    self.direction = 1 if self.rect.centerx < player.rect.centerx else -1
                    self.rect.x += self.speed * self.direction
                    self.update_action(1)  # Running animation
                else:
                    # Attack the player if close enough
                    self.update_action(5)  # Attack animation
                    if self.attack_timer == 0 and self.frame_index >= 5:
                        player.get_hurt = True
                        player.health -= 50
                        player.velocity.x = self.direction * TILE_SIZE * 0.35  # Push the player
                        player.vel_y -= TILE_SIZE * 0.5  # Apply vertical force
                        self.attack_timer = 30  # Cooldown for attack
                    return  # Exit after attacking player

            # If no target is detected, patrol
            if not self.idling:
                ai_moving_right = self.direction == 1
                ai_moving_left = not ai_moving_right
                self.move(ai_moving_left, ai_moving_right)
                self.update_action(1)  # Running animation
                self.moving_counter += 1

                # Update the vision box to reflect current position
                self.vision.center = (self.rect.centerx + (2 * TILE_SIZE * self.direction), self.rect.centery)

                # If patrol area exceeded, change direction and idle
                if self.moving_counter >= TILE_SIZE * 0.8 or random.randint(1, 100) == 1:
                    self.direction *= -1  # Switch patrol direction
                    self.moving_counter = 0  # Reset patrol counter
                    self.idling = True  # Enter idle state
                    self.idling_counter = random.randint(10, 100)  # Random idle duration




    def AI2(self, player):
        if self.is_alive and player.is_alive:
            # Handle idle behavior
            if self.idling:
                self.update_action(0)  # Idle animation
                self.idling_counter -= 1
                if self.idling_counter <= 0:
                    self.idling = False
                else:
                    return  # Skip the rest if idling

            # Check for bombs in vision range
            for bomb in bomb_group:
                if self.vision.colliderect(bomb.rect):
                    # If far enough, move toward the bomb
                    if abs(self.rect.centerx - bomb.rect.centerx) >= bomb.rect.width / 2:
                        self.direction = 1 if self.rect.centerx < bomb.rect.centerx else -1
                        self.rect.x += self.speed * self.direction
                        self.update_action(1)  # Running animation
                    else:
                        # Attack the bomb if close
                        self.update_action(6)  # Attack animation
                        if self.frame_index >= 5:
                            off_rect = bomb_off.get_rect(center = (bomb.rect.centerx, bomb.rect.centery))
                            bomb.kill()
                            screen.blit(bomb_off, camera.apply_rect(bomb_off.get_rect(center = (bomb.rect.centerx, bomb.rect.centery))))
                        
                    return  # Exit after interacting with bomb
                

            # Handle attack cooldown
            if self.attack_timer > 0:
                self.attack_timer -= 1

            # Check if the player is within vision
            if self.vision.colliderect(player.rect):
                # Move toward the player if far enough
                if abs(self.rect.centerx - player.rect.centerx) >= player.rect.width / 2:
                    self.direction = 1 if self.rect.centerx < player.rect.centerx else -1
                    self.rect.x += self.speed * self.direction
                    self.update_action(1)  # Running animation
                else:
                    # Attack the player if close enough
                    self.update_action(5)  # Attack animation
                    if self.attack_timer == 0 and self.frame_index >= 5:
                        player.get_hurt = True
                        player.health -= 50
                        player.velocity.x = self.direction * TILE_SIZE * 0.35  # Push the player
                        player.vel_y -= TILE_SIZE * 0.5  # Apply vertical force
                        self.attack_timer = 30  # Cooldown for attack
                    return  # Exit after attacking player

            # If no target is detected, patrol
            if not self.idling:
                ai_moving_right = self.direction == 1
                ai_moving_left = not ai_moving_right
                self.move(ai_moving_left, ai_moving_right)
                self.update_action(1)  # Running animation
                self.moving_counter += 1

                # Update the vision box to reflect current position
                self.vision.center = (self.rect.centerx + (2 * TILE_SIZE * self.direction), self.rect.centery)

                # If patrol area exceeded, change direction and idle
                if self.moving_counter >= TILE_SIZE * 0.8 or random.randint(1, 100) == 1:
                    self.direction *= -1  # Switch patrol direction
                    self.moving_counter = 0  # Reset patrol counter
                    self.idling = True  # Enter idle state
                    self.idling_counter = random.randint(10, 100)  # Random idle duration





# World class
class World():
    def __init__(self):
        self.obstacle_list = []
        self.background_list = []
        self.world_data = []

    def process_data(self, data):
        # iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile in [0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 24, 25]:
                        self.obstacle_list.append(tile_data)
                        self.world_data.append(tile_data)
                    else:
                        self.background_list.append(tile_data)
                        self.world_data.append(tile_data)

    def draw(self):
        for tile in self.world_data:
            screen.blit(tile[0], camera.apply_rect(tile[1]))


#healthbar

class HealthBar(pygame.sprite.Sprite):
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, 'BLACK', (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, 'RED', (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, 'GREEN', (self.x, self.y, 150 * ratio, 20))


#bomb


class BOMB(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frame_index = 0
        self.action = 0
        self.vel_y = 0  # Vertical velocity set during bomb creation
        self.vel_x = 10  # Default horizontal velocity
        self.animation_list = []
        self.flip = False
        self.update_time = pygame.time.get_ticks()
        self.bomb_timer = 400
        self.explosion_range = TILE_SIZE * 2
        self.push_force = TILE_SIZE/2.5
        self.speed = TILE_SIZE/2.5
        self.velocity = pygame.Vector2(0, 0)
        self.direction = player.direction

        # Load all images for the bomb
        animation_types = ['2-Bomb On', '3-Explotion']
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f'Sprites/7-Objects/1-BOMB/{animation}'))
            for i in range(1, num_of_frames):
                img = pygame.image.load(f'Sprites/7-Objects/1-BOMB/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * 1.35), int(img.get_height() * 1.35)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def apply_push(self,entities):
        if entities == player:
            distance = abs(self.rect.centerx - player.rect.centerx)
            if abs(self.rect.centerx - player.rect.centerx) < self.explosion_range and \
                abs(self.rect.centery - player.rect.centery) < self.explosion_range:
                if self.rect.centerx < player.rect.centerx:
                    player.rect.x += ((TILE_SIZE * 2)/distance) * self.push_force
                    player.rect.y -= TILE_SIZE
                elif self.rect.centerx > player.rect.centerx:
                    player.rect.x -= ((TILE_SIZE * 2)/distance) * self.push_force
                    player.rect.y -= TILE_SIZE
        else:
            for entity in entities:    
                distance = abs(self.rect.centerx - entity.rect.centerx)
                if abs(self.rect.centerx - entity.rect.centerx) < self.explosion_range and \
                    abs(self.rect.centery - entity.rect.centery) < self.explosion_range:
                    if self.rect.centerx < entity.rect.centerx:
                        entity.rect.x += ((TILE_SIZE * 2)/distance) * self.push_force
                        entity.rect.y -= TILE_SIZE
                    elif self.rect.centerx > entity.rect.centerx:
                        entity.rect.x -= ((TILE_SIZE * 2)/distance) * self.push_force
                        entity.rect.y -= TILE_SIZE


    def bomb_ai(self):
        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy = self.vel_y
        dx = self.vel_x

        # # Check for Collision
        # for tile in world.obstacle_list:
        #     # check collision in x direction
        #     if tile[1].colliderect(self.rect.x + (dx * self.direction), self.rect.y, self.width, self.height):
        #         dx = 0
        #         self.vel_x = 0
        #     if tile[1].colliderect(self.rect.x , self.rect.y, self.width, self.height):
        #         dy = 0
        #         self.vel_y = 0
        #         self.rect.bottom = tile[1].top
        #         if
        #             self.rect.top -= 1                                
    

    # Check for collision with tiles
        for tile in world.obstacle_list:
            # Horizontal Collision (x-direction)
            if tile[1].colliderect(self.rect.x + (dx * self.direction), self.rect.y, self.width, self.height):
                dx = 0  # Stop horizontal movement            
                
            # Vertical Collision (y-direction)
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                dy = 0  # Stop vertical movement
                dx = 0
                                        

        # Update bomb's position
        self.rect.x += dx * self.direction  # Use player's direction for horizontal throw
        self.rect.y += dy

        # Explosion logic
        if self.bomb_timer >= 0:
            self.bomb_timer -= 1
        if self.bomb_timer <= 0:
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            # Damage and push logic
            if abs(self.rect.centerx - player.rect.centerx) < self.explosion_range and \
            abs(self.rect.centery - player.rect.centery) < self.explosion_range:
                player.get_hurt = True
                if player.is_alive:
                    player.health -= 50
                    if player.health <= 0:
                        player.update_action(4)
                        player.is_alive = False
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < self.explosion_range and \
                abs(self.rect.centery - enemy.rect.centery) < self.explosion_range:
                    enemy.get_hurt = True
                    if enemy.is_alive:
                        enemy.health -= 50
                        if enemy.health <= 0:
                            enemy.update_action(4)
                            enemy.is_alive = False
            
            # Apply push to the player and all bombs in the bomb group
            self.apply_push(enemy_group)
            self.apply_push(bomb_group)
            self.apply_push(player)
            self.kill()


    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 1:
                self.kill()
            else:
                self.frame_index = 1


    def update(self):
        self.bomb_ai()
        self.update_animation()
        self.draw()
        

    def draw(self):
        screen.blit(self.image, camera.apply_rect(self.rect))




#explosion



class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        super().__init__()
        self.images = []
        for num in range(1, 10):
            img = pygame.image.load(f'Sprites/7-Objects/1-BOMB/3-Explotion/{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0


    def update(self):
        self.draw()
        EXPLOSION_SPEED = 4
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]
    
    def draw(self):
        screen.blit(self.image, camera.apply_rect(self.rect))




# Create player
player = PLAYER('1-Player-Bomb Guy', 200, 100, 1.25, TILE_SIZE/9, 150)
player_health = HealthBar(10, 10, player.health, player.max_health)

# Create camera
camera = Camera(COLS * TILE_SIZE, ROWS * TILE_SIZE)

# Create groups for bombs and explosions
bomb_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()



#create enemy and enemy group
enemy1 = PLAYER('6-Enemy-Whale', 800, 600, 1.5, player.speed * 0.8, 50)
enemy4 = PLAYER('6-Enemy-Whale', 2000, 600, 1.5, player.speed * 0.8, 50)
enemy5 = PLAYER('6-Enemy-Whale', 1300, 600, 1.5, player.speed * 0.8, 50)
enemy7 = PLAYER('6-Enemy-Whale', 300, 600, 1.5, player.speed * 0.8, 50)
enemy8 = PLAYER('6-Enemy-Whale', 2683, 375, 1.5, player.speed * 0.8, 50)
enemy11 = PLAYER('6-Enemy-Whale', 3220, 465, 1.5, player.speed * 0.8, 50)
enemy12 = PLAYER('6-Enemy-Whale', 2675, 600, 1.5, player.speed * 0.8, 50)
enemy14 = PLAYER('6-Enemy-Whale', 2693, 100, 1.5, player.speed * 0.8, 50)

enemy9 = PLAYER('2-Enemy-Bald Pirate', 3870, 95, 1.25, player.speed * 0.8, 50)
enemy6 = PLAYER('2-Enemy-Bald Pirate', 400, 600, 1.25, player.speed * 0.8, 50)
enemy10 = PLAYER('2-Enemy-Bald Pirate', 3830, 595, 1.25, player.speed * 0.8, 50)
enemy13 = PLAYER('2-Enemy-Bald Pirate', 3220, 240, 1.25, player.speed * 0.8, 50)
enemy3 = PLAYER('2-Enemy-Bald Pirate', 1410, 275, 1.25, player.speed * 0.8, 50)
enemy2 = PLAYER('2-Enemy-Bald Pirate', 1990, 275, 1.25, player.speed * 0.8, 50)



enemy_group = pygame.sprite.Group()
enemy_group.add(enemy1)
enemy_group.add(enemy2)
enemy_group.add(enemy3)
enemy_group.add(enemy4)
enemy_group.add(enemy5)
enemy_group.add(enemy6)
enemy_group.add(enemy7)
enemy_group.add(enemy8)
enemy_group.add(enemy9)
enemy_group.add(enemy10)
enemy_group.add(enemy11)
enemy_group.add(enemy12)
enemy_group.add(enemy13)
enemy_group.add(enemy14)


#create empty tile list
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)
world = World()
world.process_data(world_data)




# Game loop

run = True


while run:
    
    clock.tick()
    screen.fill(BG_COLOR)

    world.draw()
    camera.update(player)
    # Update and draw

    player.update()
    player.draw()
    player_health.draw(player.health)

    #enemy
    for enemy in enemy_group:
        enemy.update()
        enemy.draw()
        if enemy in [enemy1, enemy7, enemy4, enemy5, enemy8, enemy11, enemy12, enemy14]: enemy.AI2(player)
        else: enemy.AI(player)
        
    #bombs
    bomb_group.update()
    explosion_group.update()

    
    # Handle player actions
    if player.health <= 0 and player.is_alive:
        player.is_alive = False
        player.update_action(4)  # Dead Hit animation
    
    elif player.is_alive:
        if player.drop_bomb and player.get_hurt == False:
            bomb = BOMB(player.rect.centerx, player.rect.centery)
            bomb_group.add(bomb)
            player.drop_bomb = False
        
        if player.in_air:
            player.update_action(2)

        elif moving_left or moving_right:
            player.update_action(1)

        elif player.get_hurt:
            player.update_action(3)

        else:
            player.update_action(0)

    if player.is_alive:
        player.move(moving_left, moving_right)
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if player.get_hurt == False:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    moving_left = True
                if event.key == pygame.K_d:
                    moving_right = True
                if event.key == pygame.K_w:
                    player.jump = True
                if event.key == pygame.K_f:
                    player.charging = True
                    player.charge_start_time = pygame.time.get_ticks()
                if event.key == pygame.K_q:  # Place the bomb at the player's current position
                    bomb = BOMB(player.rect.centerx, player.rect.bottom)
                    bomb_group.add(bomb)
                

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    moving_left = False
                if event.key == pygame.K_d:
                    moving_right = False
                if event.key == pygame.K_f:
                    if player.charging:
                        # Release the bomb
                        charge_power = min((player.charge_duration // 100), 10)  # Scale charge power to 10 levels
                        bomb = BOMB(player.rect.centerx, player.rect.centery)
                        bomb.vel_y = -charge_power * 1.5  # Adjust velocity based on charge
                        bomb_group.add(bomb)
                        player.charging = False
                        player.charge_duration = 0
                        player.charge_index = 0
            

    pygame.display.update()

pygame.quit()
