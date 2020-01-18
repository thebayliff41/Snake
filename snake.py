from enum import Enum
from random import randint
from math import floor
import pygame

speed = 10
noBoundry = True
size = 40
moving = False

class Game():
    """Class to create a game of snake 

    Public Methods:
    userInput()
    play()
    end()

    Instance Variables:
    size - the size of the blocks (snake and food)
    windowHeight - height of the window element
    windowWidth - width of the window element
    scale - determines 
    """
    rows = None
    cols = None
    size = None
    windowWidth = None
    windowHeight = None
    noBoundry = None
    done = None
    def __init__(self, fps, speed):
        Game.cols = floor(Game.windowHeight/size - 1) #fix
        Game.rows = floor(Game.windowWidth/size - 1)
        Game.done = False
        self.screen = pygame.display.set_mode((Game.windowWidth, Game.windowHeight))
        self.food = Food(Game.windowWidth, Game.windowHeight, Game.size)
        self.snake = Snake(Game.size, self.food)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.speed = speed
        self.wait = False
        
    def userInput(self, key):
        """
        Converts key press into action

        Available keys: 
        UP_ARROW, DOWN_ARROW, LEFT_ARROW, RIGHT_ARROW - movement
        J - end game

        Arguments:
        key - the key that was pressed
        """
        if key == pygame.K_UP:
            self.snake.changeDirection(Direction.UP)
        elif key == pygame.K_DOWN:
            self.snake.changeDirection(Direction.DOWN)
        elif key == pygame.K_LEFT:
            self.snake.changeDirection(Direction.LEFT)
        elif key == pygame.K_RIGHT:
            self.snake.changeDirection(Direction.RIGHT)
        elif key == pygame.K_j:
            self.snake.die()

    def play(self):
        """
        Main game loop. Handles movement and updating screen
        """
        global moving
        moved = False
        timer = 0
        buffer = []
        while not Game.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    Game.done = True

                if event.type == pygame.KEYDOWN and moved:
                    self.userInput(event.key)
                    moved = False
                elif event.type == pygame.KEYDOWN and not moved:
                    buffer.append(event.key)


            if buffer and moved:
                for key in buffer:
                    self.userInput(buffer.pop(0))

            if timer * speed * Game.size > self.size:
                timer = 0
                self.snake.move()
                moved = True

            self.screen.fill((0, 0, 0))
            pygame.draw.rect(self.screen, Snake.color, self.snake)
            pygame.draw.rect(self.screen, Food.color, self.snake.food)

            for block in self.snake.tail:
                pygame.draw.rect(self.screen, Snake.color, block)
                pygame.draw.rect(self.screen, block.border_color, block.border, 1)

            pygame.display.flip()

            timer += self.clock.tick(self.fps) / 1000 #fps

    def end(self):
        self.snake.changeDirection(Direction.NONE)

class Direction(Enum):
    """
    Enumeration for what direction the snake is heading
    """
    UP = [0, -size]
    DOWN = [0, size]
    LEFT = [-size, 0]
    RIGHT = [size, 0]
    NONE = [0, 0]

    def flip(self):
        """Flip the direction"""
        return [-self.value[0], -self.value[1]]

    def __eq__(self, other):
        """Directions are equivalent if they have the same list value"""
        return self.value == other


class Block(pygame.Rect):
    def __init__(self, size, x, y):
        self.width = size
        self.height = size
        self.x = x
        self.y = y
        self.border = pygame.Rect(self.x, self.y, size+1, size+1).clamp(self)
        self.border_color = (0, 0, 0)
        self.safe = False


class Food(pygame.Rect):
    color = (255, 0, 100)

    def __init__(self, windowWidth, windowHeight, size):
        self.width = size
        self.height = size
        self.relocate()

    def relocate(self):
        """Move the food to a random spot in the grid"""
        self.x, self.y = randint(0, Game.rows), randint(0, Game.cols)
        self.x *= Game.size
        self.y *= Game.size

    def isSafe(self, rect):
        """Checks if the rectangle is inside the given rectangle
        
        Keyword arguments:
        rect -- the rectangle to check if the food is within
        """
        return not (self.x, self.y) == (rect.x, rect.y)



class Snake(pygame.Rect):
    color = (0, 128, 255) 

    def __init__(self, startingSize, food):
        self.x = floor(Game.rows/2) * Game.size # Head values
        self.y = floor(Game.cols/2) * Game.size
        self.width = startingSize
        self.height = startingSize
        self.dx = 0
        self.dy = 0
        self.tail = []
        self.food = food


    def eat(self):
        """When a block is eaten, the size is increased and the food is moved"""
        self.tail.append(Block(Game.size, self.x, self.y))
        safe = False
        while not safe:
            self.food.relocate()
            i = 0
            for i, t in enumerate(self.tail):
                if not self.food.isSafe(t):
                    break
            if i != len(self.tail) - 1:
                continue
            
            safe = self.food.isSafe(self)


    def changeDirection(self, direction):
        """Change the direction of the snake"""
        print(f"\ndirection = {direction} and self.direction = {self.getDirection()}")
        if (direction == self.getDirection() or direction == self.getDirection().flip()) and not len(self.tail) == 0:
            print("no change")
            return
        self.dx, self.dy = direction.value

    def getDirection(self):
        return Direction([self.dx, self.dy])

    def move(self):
        """Move the snake.
        
        The snake moves by shifting the entire array of the tail to the left (removing the last
        element) and putting a new Block where the head used to be. """
        print("moving")
        for i, t in enumerate(self.tail):
            if i == len(self.tail) - 1:
                break
            self.tail[i] = self.tail[i+1] #shift left
        
        if self.tail:
            self.tail[len(self.tail) - 1] = Block(self.width, self.x, self.y) #insert new block to where old head was (before movement)

        self.y += self.dy #Move head
        self.x += self.dx

        self.hitWall()
        if not self.checkEat():
            self.hitSelf()

    def checkEat(self):
        """Check if the snake is touching the food"""
        if self.colliderect(self.food):
            self.eat()
            return True
        else:
            return False

    def hitWall(self):
        """Check if the snake hit the wall"""

        global noBoundry
        if self.x < 0 or self.y < 0 or self.x > Game.windowWidth - self.width or self.y > Game.windowHeight - self.height:
            if not noBoundry:
                self.die()
            else:
                if self.x < 0:
                    self.x = Game.windowWidth
                elif self.y < 0:
                    self.y = Game.windowHeight
                elif self.x > Game.windowWidth - self.width:
                    self.x = 0
                elif self.y > Game.windowHeight - self.height:
                    self.y = 0
                else: 
                    raise RunTimeError("Position invalid")

    def hitSelf(self):
        """Check if the snake head hit part of it's tail"""
        for block in self.tail:
            if self.colliderect(block):
                print("ouch")
                print(block)
                print(self)
                print(self.getDirection())
                self.die()

    def die(self):
        """Kill the snake"""
        self.changeDirection(Direction.NONE)
        print("You have died! Game Over")
        Game.done = True


def main():
    """
    Main entry into the program, creates a game and plays it
    """
    speed = 1
    Game.size = 40
    Game.windowWidth = 800
    Game.windowHeight = 600
    Game.done = False
    game = Game(60, speed)
    game.play()
    print("finished!")

if __name__ == "__main__":
    pygame.init()
    main()