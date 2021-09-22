#! /usr/bin/env python3
import pygame
from enum import Enum
from random import randint
from math import floor


class Game():
    def __init__(self, fps, width, height):
        pygame.init()
        self.done = False
        self.fps = fps
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((width, height))
        self.snake = Snake(self, 40)
        self.food = Food(self, 40) 
        self.score = Score(self.screen, (10, 10))
        self.pause = False

        def checkPause(self, key):
            if key == pygame.K_SPACE:
                self.pause = ~self.pause

    def play(self):
        timer = 0
        speed = 10
        input_buffer = []
        moved = False
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

                if event.type == pygame.KEYDOWN:
                    if moved:
                        self.userInput(event.key)
                        moved = False
                    else:
                        input_buffer.append(event.key)

            while self.pause:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        self.checkPause(event.key)

            if input_buffer and moved:
                self.userInput(input_buffer.pop(0))
                moved = False

            if timer * speed > 1:
                timer = 0
                self.snake.move()
                if self.snake.checkDead():
                    self.gameOver()
                moved = True

            self.snake.checkEat()
            self.screen.fill((0, 0, 0))
            self.score.draw()
            pygame.draw.rect(self.screen, Snake.color, self.snake)
            pygame.draw.rect(self.screen, Food.color, self.food)

            for block in self.snake.tail:
                pygame.draw.rect(self.screen, Block.color, block)

            timer += self.clock.tick(self.fps) / 1000
            pygame.display.flip()

    def userInput(self, key):
        if key == pygame.K_UP:
            self.snake.changeDirection(Direction.UP)
        elif key == pygame.K_DOWN:
            self.snake.changeDirection(Direction.DOWN)
        elif key == pygame.K_LEFT:
            self.snake.changeDirection(Direction.LEFT)
        elif key == pygame.K_RIGHT:
            self.snake.changeDirection(Direction.RIGHT)
        elif key == pygame.K_SPACE:
            self.pause = ~self.pause

    def gameOver(self):
        print(f"You have died! You ate {len(self.snake.tail)} pieces of food!")
        self.done = True


class Block(pygame.Rect):
    color = (0, 128, 255)  # blue

    def __init__(self, size, x, y):
        self.width = size
        self.height = size
        self.x = x
        self.y = y
        self.dim = size


class Direction(Enum):
    UP = [0, -40]
    DOWN = [0, 40]
    LEFT = [-40, 0]
    RIGHT = [40, 0]
    NONE = [0, 0]

    def __invert__(self):
        return Direction([-self.value[0], -self.value[1]])


class Snake(Block):
    color = (124, 252, 0)

    def __init__(self, game, size):
        Block.__init__(self, size,
                       floor((pygame.display.get_window_size()
                              [0]/size - 1)/2) * size,
                       floor((pygame.display.get_window_size()
                              [1]/size - 1)/2) * size)
        self.direction = Direction.NONE
        self.game = game
        self.tail = []
        self.hit_self = False
        self.hit_wall = False

    def move(self):
        if self.tail:
            self.tail = self.tail[1:]
            self.tail.append(Block(self.dim, self.x, self.y))

        self.x += self.direction.value[0]
        self.y += self.direction.value[1]

        self.checkEat()
        self.hitWall()
        self.hitSelf()
        

    def changeDirection(self, newDirection):
        if newDirection.value == [-x for x in self.direction.value]:
            return
        self.direction = newDirection

    def checkEat(self):
        if self.colliderect(self.game.food):
            self.game.food.relocate()
            self.growTail()
            self.game.score.changeScore(1)
            self.ate = True
        else:
            self.ate = False

    def growTail(self):
        self.tail.append(Block(
            self.dim, self.x - self.direction.value[0], self.y - self.direction.value[1]))

    def hitWall(self):
        if (self.x < 0 or self.y < 0
                    or self.x > pygame.display.get_window_size()[0] - self.dim
                    or self.y > pygame.display.get_window_size()[1] - self.dim
                ):
            self.hit_wall = True
            # Push back
            self.x -= self.direction.value[0]
            self.y -= self.direction.value[1]
        else:
            self.hit_wall = False

    def hitSelf(self):
        for block in self.tail:
            if block.colliderect(self):
                self.hit_self = True
                return
        self.hit_self = False

    def checkDead(self):
        if self.hit_self or self.hit_wall:
            return True
        else:
            return False


class Food(Block):
    color = (255, 0, 100)

    def __init__(self, game, size):
        Block.__init__(self, size, 0, 0)
        self.game = game
        self.relocate()

    def relocate(self):
        cols = floor(pygame.display.get_window_size()[0]/self.dim - 1)
        rows = floor(pygame.display.get_window_size()[1]/self.dim - 1)

        self.x, self.y = randint(0, cols) * \
            self.dim, randint(0, rows) * self.dim

        if not self.isSafe():
            self.relocate()

    def isSafe(self):
        if self.colliderect(self.game.snake):
            return False
        else:
            return True

class Score():
    def __init__(self, screen, location):
        self.font = pygame.font.Font(None, 36)
        self.value = 0
        self.location = location
        self.screen = screen

    def draw(self):
        text = self.font.render(f"Score: {self.value}", 1, (255, 255, 255))
        self.screen.blit(text, self.location)

    def changeScore(self, change):
        self.value += change

    def reset(self):
        self.value = 0

def main():
    game = Game(60, 800, 600)
    game.play()


if __name__ == "__main__":
    main()
