#! /usr/bin/env python3
from enum import Enum
from random import randint
from math import floor
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

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
    noBoundry - can the snake go through walls
    done - is the game done
    """

    def __init__(self, size, fps, windowHeight, windowWidth, speed, noBoundry = False, assist = False):
        pygame.init()
        self.size = size
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight

        # - 1 so the the shape doesn't start at at the edge (meaning the rest of the shape is drawn out of the window)
        self.cols = floor(windowHeight/size - 1)
        self.rows = floor(windowWidth/size - 1)
        self.done = False
        self.screen = pygame.display.set_mode((windowWidth, windowHeight))
        self.snake = Snake(self)
        self.food = Food(self)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.speed = speed
        self.wait = False
        self.score = Score(self.screen, (floor(self.cols/2), 10))
        self.noBoundry = noBoundry
        self.assist = assist

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
        moved = False
        timer = 0
        inputBuffer = []  # holds the user input pressed while the snake is moving
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

                if event.type == pygame.KEYDOWN and moved:
                    self.userInput(event.key)
                    moved = False
                elif event.type == pygame.KEYDOWN and not moved:
                    inputBuffer.append(event.key)

            if inputBuffer and moved:  # Empty buffer
                self.userInput(inputBuffer.pop(0))
                moved = False

            if timer * self.speed  > 1:  # Controls the speed of the snake
                timer = 0
                self.snake.move()
                moved = True

            self.screen.fill((0, 0, 0))  # black

            self.score.draw()


            for block in self.snake.tail:  # draw tail
                pygame.draw.rect(self.screen, Block.color, block)
                pygame.draw.rect(
                    self.screen, block.border_color, block.border, 1)

            pygame.draw.rect(self.screen, Snake.color,
                             self.snake)  # draw head then food
            pygame.draw.rect(self.screen, Food.color, self.food)

            pygame.display.flip()  # update display

            timer += self.clock.tick(self.fps) / 1000


class Score():
    """
    Represents the score of the game

    Public Methods:
    draw() - draws the score on the screen
    changeScore() - changes the score by the given number (positive or negative)
    """
    def __init__(self, screen,location):
        self.font = pygame.font.Font(None, 36)
        self.value = 0
        self.location = location
        self.screen = screen

    def draw(self):
        text = self.font.render(f"Score: {self.value}", 1, (255, 255, 255))
        self.screen.blit(text, self.location)

    def changeScore(self, change):
        self.value += change

class Direction(Enum):
    """
    Enumeration for what direction the snake is heading
    """
    UP = [0, -1]
    DOWN = [0, 1]
    LEFT = [-1, 0]
    RIGHT = [1, 0]
    NONE = [0, 0]

    def flip(self):
        """Flip the direction (negate both sides)"""
        return [-self.value[0], -self.value[1]]

    def __eq__(self, other):
        """Directions are equivalent if they have the same list value"""
        return self.value == other


class Block(pygame.Rect):
    """
    Object used to represent all squares in the game

    Instance Variables:
    color - color of the snake body (blue)
    """
    color = (0, 128, 255)

    def __init__(self, size, x, y):
        self.width = size
        self.height = size
        self.x = x
        self.y = y
        # attach another rectanlge to the block in order to create a border
        self.border = pygame.Rect(self.x, self.y, size+1, size+1).clamp(self)
        self.border_color = (0, 0, 0)
        self.safe = False


class Food(Block):
    """
    Object used to represent the food that the snake is after

    Public Methods:
    relocate()
    isSafe(rect)

    Instance Variables:
    color - color of the food - pink
    """
    color = (255, 0, 100)

    def __init__(self, game):
        Block.__init__(self, game.size, 0, 0)
        self.game = game
        self.relocate()

    def relocate(self):
        """Move the food to a random spot in the grid"""
        self.x, self.y = randint(0, self.game.rows), randint(0, self.game.cols)
        self.x *= self.game.size
        self.y *= self.game.size

        if not self.isSafe():
            self.relocate()

    def isSafe(self):
        """
        Checks if the current food position is inside any part of the snake

        return - True if safe (not inside any part of snake), False otherwise
        """
        for block in self.game.snake.tail:
            if self.colliderect(block):
                return False
        return True


class Snake(Block):
    """
    Class to represent the snake object

    Public Methods:
    eat()
    changeDirection(direction)
    getDirection()
    move()
    checkEat()
    hitWall()
    hitSelf()
    die()

    Instance Variables:
    color - the Color of the snake head (green)
    """
    color = (124, 252, 0)

    def __init__(self, game):
        Block.__init__(self, game.size, floor(game.rows/2) *
                       game.size, floor(game.cols/2) * game.size)
        self.game = game
        self.dx = 0
        self.dy = 0
        self.tail = []

    def checkEat(self):
        """
        Checks if the snake is colliding with the food object.
        Updates the score if the food is eaten.

        returns True if colliding and False otherwise
        """
        if self.colliderect(self.game.food):
            self.game.food.relocate()
            self.tail.append(Block(self.game.size, self.x, self.y))
            self.game.score.changeScore(1)
            return True
        else:
            return False

    def changeDirection(self, direction):
        """Change the direction of the snake"""
        # You can't go backwards into yourself, and don't do anything if you're already going that direction
        # If you're just a head, you can go backwards
        if (direction == self.getDirection() or direction == self.getDirection().flip()) and not len(self.tail) == 0:
            return

        self.dx = direction.value[0] * self.game.size
        self.dy = direction.value[1] * self.game.size

    def getDirection(self):
        """Returns the current direction of the snake"""
        return Direction([self.dx/self.game.size, self.dy/self.game.size])

    def move(self):
        """
        Move the snake.

        The snake moves by shifting the entire array of the tail to the left (removing the last
        element) and putting a new Block where the head used to be. 
        """

        if self.tail:
            self.tail = self.tail[1:]
            self.tail.append(Block(self.game.size, self.x, self.y))

        self.y += self.dy # Move head
        self.x += self.dx 

        self.hitWall()

        if not self.checkEat():  # Only check if the snake hits itself if it didn't eat, eating causes another block to be placed exactly where the snake is
            self.hitSelf()

    def hitWall(self):
        """Check if the snake hit the wall"""
        if self.x < 0 or self.y < 0 or self.x > self.game.windowWidth - self.game.size or self.y > self.game.windowHeight - self.game.size:  # hit edge of screen
            if not self.game.noBoundry:
                self.die()
            else:
                if self.x < 0:
                    self.x = self.game.windowWidth
                elif self.y < 0:
                    self.y = self.game.windowHeight
                elif self.x > self.game.windowWidth - self.game.size:
                    self.x = 0
                elif self.y > self.game.windowHeight - self.game.size:
                    self.y = 0
                else:
                    raise RunTimeError("Position invalid")

    def hitSelf(self):
        """Check if the snake head hit part of it's tail"""
        for block in self.tail:
            if self.colliderect(block):
                if self.game.assist:
                    self.assist()
                    break
                else:
                    self.die()

    def die(self):
        """Kill the snake, end the game"""
        self.game.done = True
        self.changeDirection(Direction.NONE)
        print("You have died! Game Over")
        print(f"Final score = {self.game.score.value}")

    def safeDirections(self):
        """
        Returns a list of the safe directions that the snake can go at the given spot. 
        """
        safe = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        safe.remove(self.getDirection())
        safe.remove(self.getDirection().flip())
        directionCheck1 = safe[0]
        directionCheck2 = safe[1]
        if self.checkCollideWithTail(directionCheck1):
            safe.remove(directionCheck1)
        if self.checkCollideWithTail(directionCheck2):
            safe.remove(directionCheck2)

        return safe

    def checkCollideWithTail(self, check):
        """
        Checks if the given direction would cause a collision with the head of the snake

        Keyword Arguments: 
        check - the direction to check

        Return - True if the snake would collide, False otherwise
        """
        for block in self.tail:
            if Block(self.game.size, self.x + check.value[0] * self.game.size, self.y + check.value[1] * self.game.size).colliderect(block):
                return True
        return False

    def assist(self):
        """
        Assist the snake if it hits itself. Causes the snake to instead choose a random, safe direction to turn.
        """
        self.x -= self.dx
        self.y -= self.dy
        safeDirections = self.safeDirections()
        if len(safeDirections) == 0:
            self.die()
        elif len(safeDirections) == 1:
            self.changeDirection(safeDirections[0])
        else:
            if randint(1, 100) > 50:
                self.changeDirection(safeDirections[0])
            else:
                self.changeDirection(safeDirections[1])


def main():
    """
    Main entry into the program, creates a game and plays it
    """
    game = Game(40, 60, 600, 800, 10, True, True)
    game.play()


if __name__ == "__main__":
    main()
