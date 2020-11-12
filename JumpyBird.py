import pygame
import neat
import time
import os
import random
import sys, os 

pygame.font.init()

WIN_WIDTH = 500             # Window Width (CONST)
WIN_HEIGHT = 900            # Window Height (CONST)

# Importing the images used in the game
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 45)
QUIT_FONT = pygame.font.SysFont("comicsans", 40)

# Creating a Bird class
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 20
    ROT_VEL = 10
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0             # Keeps track of last jump
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel*self.tick_count + 1.5*self.tick_count**2           # This tells us whether the bird is moving up or down (USING SELF.TICK_COUNT)

        if d >= 16:         # If the bird is moving down more than 16
            d = 20              # Move down only by 16

        if d < 0:           # If it's moving upwards
            d -= 2              # Move higher by 2  

        self.y = self.y + d         # Changing the y placement based on d

        if d < 0 or self.y < self.height + 10:          # If the bird is moving upwards (and still moving upwards)
            if self.tilt < self.MAX_ROTATION:               # Prevent bird from tilting too much
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -60:                     # As it's falling downwards
                self.tilt -= 40              # Tilt

    # Bird's flapping animation
    def draw(self, win):
        self.img_count += 1

        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0                                  # Reset the image count

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2              # Prevents frame skipping as bird jumps back up

        rotated_image = pygame.transform.rotate(self.img, self.tilt)            # Rotate the bird with the proper tilt
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)             # Prevents bird from tilting weirdly
        win.blit(rotated_image, new_rect.topleft)               # Draw the rotated bird

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200            # Gap between pipes
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)        # Flip the pipe for the pipes coming down from the ceiling
        self.PIPE_BOTTOM = PIPE_IMG                 # Regular facing pipe for pipes coming up from the floor

        self.passed = False             # When bird hasn't passed by the pipe
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)                 # To randomize generated pipe height
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    # Drawing the pipe
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Detecting collision using masks
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Setting the offsets
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)          # Defines the point of collision or overlap
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:            # If collision is detected return true  
            return True

        return False                    # Otherwise return false


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    # Moving the ground platform 
    def move(self):
        self.x1 -= self.VEL         # Part 1 of the ground platform
        self.x2 -= self.VEL         # Part 2 of the ground platform

        if self.x1 + self.WIDTH < 0:             # When part 1 reaches the end of window screen (far left)
            self.x1 = self.x2 + self.WIDTH          # Move it back to the beginning (far right)

        if self.x2 + self.WIDTH < 0:             # When part 2 reaches the end of window screen (far left)
            self.x2 = self.x1 + self.WIDTH          # Move it back to the beginning (far right)

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0))             # Draw the window at (0,0) location

    for pipe in pipes:                  # Draw the pipes
        pipe.draw(win)

    # Drawing the score
    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 12 - text.get_width(), 11))

    text = QUIT_FONT.render("Press Q to Quit", 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 283 - text.get_width(), 11))

    base.draw(win)                      # Draw the window

    bird.draw(win)                      # Draw the bird
    pygame.display.update()             # Update the game screen


def main():
    bird = Bird(200,150)                # Create a Bird object
    base = Base(730)                    # Create a Base object
    pipes = [Pipe(700)]                 # Create a Pipes object
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    gravity = 0.25
    bird_movement = 0
    bird.tick_count += 1

    
    run = True
    while run:             # While game is running
        clock.tick(30)
        for event in pygame.event.get():            # Runs the game loop
            if event.type == pygame.QUIT:
                run = False
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


                    

        bird.move()                    # Make the bird move
       # bird_movement += gravity
        #bird_rect.center += bird_movement

        rem = []                        # List of removed pipes
        add_pipe = False
        for pipe in pipes:
            pipe.move()

            if pipe.collide(bird):
                main()

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:              # When pipe is off the screen
                rem.append(pipe)                                        # Remove pipe

            if not pipe.passed and pipe.x < bird.x:                 # When pipe has not been passed (in front of the bird)
                pipe.passed = True
                add_pipe = True                                     # Add pipe to the front

        if add_pipe:                                # After pipe has been added                  
            score += 1                                  # Add 1 to the game score
            pipes.append(Pipe(700))                     # Add a Pipe object to the pipes list

        for r in rem:                               # Remove off screen pipes that have been moved to the rem list
            pipes.remove(r)

        if bird.y + bird.img.get_height() > 730:            # If bird hits the floor
            main()

        base.move()                     # Make the ground platform move
        draw_window(win, bird, pipes, base, score)          # Draw the game window

    # Quits the game
     
    pygame.quit()

main()