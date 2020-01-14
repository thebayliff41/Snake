from enum import Enum
from random import randint
import pygame

speed = 40
windowHeight = 600
windowWidth = 800
size = 40
done = False


class Direction(Enum):
    UP = [0, -speed]
    DOWN = [0, speed]
    LEFT = [-speed, 0]
    RIGHT = [speed, 0]
    NONE = [0, 0]

    def flip(self):
        return [-self.value[0], -self.value[1]]

    def __eq__(self, other):
        return self.value == other


class Block(pygame.Rect):
    def __init__(self, size, x, y):
        self.width = size
        self.height = size
        self.x = x
        self.y = y
        self.border = pygame.Rect(self.x, self.y, size+1, size+1).clamp(self)
        self.border_color = (0, 0, 0)


class Food(pygame.Rect):
    color = (255, 0, 100)

    def __init__(self, windowWidth, windowHeight, size):
        self.width = size
        self.height = size
        self.relocate()

    def relocate(self):
        cols = windowWidth/size - 1
        rows = windowHeight/size - 1
        self.x, self.y = randint(0, cols), randint(0, rows)
        self.x *= size
        self.y *= size     

    def isSafe(self, rect):
        return not (self.x, self.y) == (rect.x, rect.y)



class Snake(pygame.Rect):
    color = (0, 128, 255)

    def __init__(self, x, y, startingSize, food):
        self.x = x  # Head values
        self.y = y
        self.width = startingSize
        self.height = startingSize
        self.dx = 0
        self.dy = 0
        self.tail = []
        self.food = food


    def eat(self):
        self.tail.append(Block(size, self.x, self.y))
        safe = False
        while not safe:
            for t in self.tail:
                safe = self.food.isSafe(t)
                if not safe:
                    break
            safe = self.food.isSafe(self)

            if not safe:
                self.food.relocate()

    def changeDirection(self, direction):
        print(str(self.getDirection().flip()) + " " + str(direction))
        if direction == self.getDirection() or direction == self.getDirection().flip():
            return
        self.dx, self.dy = direction.value

    def getDirection(self):
        return Direction([self.dx, self.dy])

    def move(self):
        print("here")
        for i, t in enumerate(self.tail):
            if i == len(self.tail) - 1:
                break
            self.tail[i] = self.tail[i+1]
        if self.tail:
            self.tail[len(self.tail) - 1] = Block(self.width, self.x, self.y)

        self.y += self.dy
        self.x += self.dx

        self.hitWall()
        if not self.checkEat():
            self.hitSelf()

    def checkEat(self):
        if self.colliderect(self.food):
            self.eat()
            return True

    def hitWall(self):
        if self.x + self.dx < 0 or self.y + self.dy< 0 or self.x + self.dx> windowWidth - self.width or self.y + self.dy > windowHeight - self.height:
            self.die()

    def hitSelf(self):
        for block in self.tail:
            if self.colliderect(block):
                self.die()

    def die(self):
        self.changeDirection(Direction.NONE)
        print("You have died!")
        global done
        done = True



pygame.init()

screen = pygame.display.set_mode((windowWidth, windowHeight))


food = Food(windowWidth, windowHeight, size)
snake = Snake(windowWidth/2, windowHeight/2, size, food)


def end():
    global done
    done = True
    print("Game Over!")


clock = pygame.time.Clock()
controlClock = pygame.time.Clock()

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    pressed = pygame.key.get_pressed()

    snake.move()

    #Controls
    if pressed[pygame.K_UP]:
        snake.changeDirection(Direction.UP)
    elif pressed[pygame.K_DOWN]:
        snake.changeDirection(Direction.DOWN)
    elif pressed[pygame.K_LEFT]:
        snake.changeDirection(Direction.LEFT)
    elif pressed[pygame.K_RIGHT]:
        snake.changeDirection(Direction.RIGHT)
    elif pressed[pygame.K_j]:
        snake.die()

    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, Snake.color, snake)
    pygame.draw.rect(screen, Food.color, snake.food)

    for block in snake.tail:
        pygame.draw.rect(screen, Snake.color, block)
        pygame.draw.rect(screen, block.border_color, block.border, 1)

    pygame.display.flip()
    clock.tick(30) #fps
