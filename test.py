import pygame
import random
import os

pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#define game variables
GRAVITY = 0.75
TILE_SIZE = 55

#define player action variables
moving_left = False
moving_right = False
grenade = False
grenade_thrown = False


#load images
#bullet
bullet_img = pygame.image.load('Sprites/7-Objects/1-BOMB/1-Bomb Off/1.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('Sprites/7-Objects/1-BOMB/1-Bomb Off/1.png').convert_alpha()
#pick up boxes
health_box = pygame.image.load('Sprites/7-Objects/17-Heart/1-Idle/1.png').convert_alpha()
health_box = pygame.transform.scale2x(health_box)
bomb_box = pygame.image.load('Sprites/7-Objects/17-Heart/1-Idle/1.png').convert_alpha()
bomb_box = pygame.transform.scale2x(bomb_box)
item_boxes = {
	'Health' : health_box,
	'Bomb' : bomb_box
}


#define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

def draw_bg():
	screen.fill(BG)
	pygame.draw.line(screen, RED, (0, 300), (SCREEN_WIDTH, 300))



class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.grenades = grenades
		self.health = 100
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
		#ai specific variables
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		
		#load all images for the players
		animation_types = ['Idle', 'Run', 'Jump', 'Hit', 'Dead Hit', 'Attack']
		try:
			for animation in animation_types:
				#reset temporary list of images
				temp_list = []
				#count number of files in the folder
				num_of_frames = len(os.listdir(f'Sprites/{self.char_type}/{animation}'))
				for i in range(1,num_of_frames):
					img = pygame.image.load(f'Sprites/{self.char_type}/{animation}/{i}.png').convert_alpha()
					img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
					temp_list.append(img)
				self.animation_list.append(temp_list)
		except Exception as e:
			pass
		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)


	def update(self):
		self.update_animation()
		

	def move(self, moving_left, moving_right):
		#reset movement variables
		dx = 0
		dy = 0

		#assign movement variables if moving left or right
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		#apply gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y

		#check collision with floor
		if self.rect.bottom + dy > 300:
			dy = 300 - self.rect.bottom
			self.in_air = False

		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy


	def ai(self):
		if self.alive and player.alive:
			# Check if the AI should idle (random chance)
			if not self.idling and random.randint(1, 200) == 1:
				self.update_action(0)  # 0: idle
				self.idling = True
				self.idling_counter = 50

			# Distance to player
			distance_to_player = abs(self.rect.centerx - player.rect.centerx)
			
			# If within a certain range, stop and attack
			if distance_to_player < 60:
				self.update_action(5)  # 5: Attack animation
				if self.rect.centerx < player.rect.centerx:
					self.direction = 1  # Face right
				else:
					self.direction = -1  # Face left

			# If not within attack range, patrol
			else:
				if not self.idling:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right

					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)  # 1: Running animation
					self.move_counter += 1

					# Update vision to follow the AI movement
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					# Reverse direction after moving for a certain distance
					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= -1
				else:
					# Handle idle behavior
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False





	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN = 100
		#update image depending on current frame
		self.image = self.animation_list[self.action][self.frame_index]
		#check if enough time has passed since the last update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#if the animation has run out the reset back to the start		
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:  # "Hit" animation ends
				player.get_hurt = False
				if self.alive:
					self.update_action(0)  # Return to idle or another state
			elif self.action == 4:  # "Dead Hit" animation
				self.frame_index = len(self.animation_list[self.action]) - 1  # Freeze on the last frame
				self.kill()
			else:
				self.frame_index = 0



	def update_action(self, new_action):
		#check if the new action is different to the previous one
		if new_action != self.action:
			self.action = new_action
			#update the animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()
			
	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
		pygame.draw.rect(screen,RED,self.rect,1)


class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		if pygame.sprite.collide_rect(self,player):
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Bomb':
				player.grenades += 5
			self.kill()


class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#update with new health
		self.health = health
		#calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#check collision with floor
		if self.rect.bottom + dy > 300:
			dy = 300 - self.rect.bottom
			self.speed = 0

		#check collision with walls
		if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
			self.direction *= -1
			dx = self.direction * self.speed

		#update grenade position
		self.rect.x += dx
		self.rect.y += dy

		#countdown timer
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
			explosion_group.add(explosion)
			#do damage to anyone that is nearby
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 1.5 and \
			abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 1.5:
				player.get_hurt = True
				if player.alive:
					player.health -= 40
					if player.health > 0:
						player.update_action(3)
					else:
						player.update_action(4)
				
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE  * 1.5 and \
				abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 1.5:
					if enemy.alive:  # Check if the enemy is still alive
						enemy.health -= 40
						if enemy.health > 0:
							enemy.update_action(3)  # Play hit animation
						else:
							enemy.update_action(4)  # Play dead animation


class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
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
		EXPLOSION_SPEED = 4
		#update explosion amimation
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#if the animation is complete then delete the explosion
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]



#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()

#items
item_box = ItemBox('Health', 100, 245)
item_box_group.add(item_box)
item_box = ItemBox('Bomb', 400, 245)
item_box_group.add(item_box)

player = Soldier('1-Player-Bomb Guy', 200, 200, 1.65, 5, 20)
health_bar = HealthBar(10, 10, player.health, player.health)

enemy2 = Soldier('2-Enemy-Bald Pirate', 300, 220, 1.65, 5, 0)
enemy_group.add(enemy2)


run = True
while run:

	clock.tick(FPS)

	draw_bg()

	#show player health
	health_bar.draw(player.health)

	#show grenades
	draw_text('GRENADES: ', font, WHITE, 10, 60)
	for x in range(player.grenades):
		screen.blit(grenade_img, (135 + (x * 15), 60))

	player.update()
	player.draw()

	for enemy in enemy_group:
		enemy.ai()
		enemy.update()
		enemy.draw()

	#update and draw groups
	bullet_group.update()
	grenade_group.update()
	explosion_group.update()
	item_box_group.update()	
	bullet_group.draw(screen)
	grenade_group.draw(screen)
	explosion_group.draw(screen)
	item_box_group.draw(screen)

	#update player actions
	if player.alive and player.get_hurt == False:
		#throw grenades
		if grenade and grenade_thrown == False and player.grenades > 0:
			grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
			 			player.rect.top, player.direction)
			grenade_group.add(grenade)
			#reduce grenades
			player.grenades -= 1
			grenade_thrown = True
		if player.in_air:
			player.update_action(2)#2: jump
		elif moving_left or moving_right:
			player.update_action(1)#1: run
		elif player.get_hurt:
			player.update_action(3)
		else:
			player.update_action(0)#0: idle
		player.move(moving_left, moving_right)


	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
			run = False
		#keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_q:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
			if event.key == pygame.K_ESCAPE:
				run = False


		#keyboard button released
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown = False





	pygame.display.update()

pygame.quit()