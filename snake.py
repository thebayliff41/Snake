#! /usr/bin/env python3
from enum import Enum
from random import randint
from math import floor
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #Don't show the pygame startup message
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

    def __init__(self, size=40, fps=60, windowHeight=600, windowWidth=960, gameHeight=600, gameWidth=800, speed=10, noBoundry = False, assist = False):
        pygame.init()
        self.size = size
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.gameHeight = gameHeight
        self.gameWidth = gameWidth
        self.leftBoundry = windowWidth - gameWidth
        self.rightBoundry = self.leftBoundry + gameWidth

        # - 1 so the the shape doesn't start at at the edge (meaning the rest of the shape is drawn out of the window)
        self.cols = floor(gameHeight/size - 1)
        self.rows = floor(gameWidth/size - 1)
        self.done = False
        self.screen = pygame.display.set_mode((windowWidth, windowHeight))
        self.snake = Snake(self)
        self.food = Food(self)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.speed = speed
        self.wait = False
        self.score = Score(self.screen, (10, 10))
        self.noBoundry = noBoundry
        self.assist = assist
        self.text = [self.score]

    def userInput(self, key):
        """
        Converts key press into action

        Available keys: 
        UP_ARROW, DOWN_ARROW, LEFT_ARROW, RIGHT_ARROW - movement
        J - end game

        Arguments:
        key - the key that was pressed
        """
        if key == pygame.K_UP or key == pygame.K_w:
            self.snake.changeDirection(Direction.UP)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.snake.changeDirection(Direction.DOWN)
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self.snake.changeDirection(Direction.LEFT)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.snake.changeDirection(Direction.RIGHT)
        elif key == pygame.K_j:
            self.snake.die()
        elif key == pygame.K_p:
            self.speed = 1
        elif key == pygame.K_o:
            self.speed = 10

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

            if timer * self.speed  > 1:  # Controls the speed of the snake
                timer = 0
                self.snake.move()
                moved = True

            if inputBuffer and moved:  # Empty buffer
                self.userInput(inputBuffer.pop(0))
                moved = False

            self.drawBoard()
            timer += self.clock.tick(self.fps) / 1000
  
    def drawBoard(self):
        """
        Draws the board drawing the snake, food, and score to the screen and updating the screen
        accordingly
        """
        self.screen.fill((0, 0, 0))  # black
        self.screen.fill((128, 0, 128), (0, 0, self.leftBoundry, self.windowHeight))

        for block in self.snake.tail[::-1]:  # draw tail backwards so the tail is rendered on top of any possible block 
            pygame.draw.rect(self.screen, block.color, block)
            pygame.draw.rect(self.screen, block.border_color, block.border, 1)

        pygame.draw.rect(self.screen, self.snake.color,
                            self.snake)  # draw head then food
        pygame.draw.rect(self.screen, self.food.color, self.food)

        for text in self.text:
            text.draw()
        pygame.display.flip()  # update display


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

    def flips(self):
        return Direction([-self.value[0], -self.value[1]])


class Block(pygame.Rect):
    """
    Object used to represent all squares in the game

    Instance Variables:
    color - color of the snake body (blue)
    """

    def __init__(self, size, x, y, color=(0, 128, 255)):
        self.width = size
        self.height = size
        self.x = x
        self.y = y
        # attach another rectanlge to the block in order to create a border
        self.border = pygame.Rect(self.x, self.y, size+1, size+1).clamp(self)
        self.border_color = (0, 0, 0)
        self.safe = False
        self.color = color

    def resetColor(self):
        self.color = (0, 128, 255)

class DisplayText():
    """
    Represents pygame Text

    Public Methods:
    draw() - draws the text to the screen
    reset() - resets the text to whatever is supplied
    """
    def __init__(self, screen,location, baseString, displayString=""):
        self.font = pygame.font.Font(None, 36)
        self.displayString = displayString
        self.location = location
        self.screen = screen
        self.baseString = baseString

    def draw(self):
        text = self.font.render(self.baseString + self.displayString, 1, (255, 255, 255))
        self.screen.blit(text, self.location)

    def reset(self, displayString="", baseString=""):
        self.displayString = displayString if displayString else self.displayString
        self.baseString = baseString if baseString else self.baseString

class Score(DisplayText):
    """
    Represents the score of the game

    Public Methods:
    draw() - draws the score on the screen
    changeScore() - changes the score by the given number (positive or negative)
    """
    def __init__(self, screen,location):
        self.value = 0
        super().__init__(screen, location, "Score: ", str(self.value))

    def changeScore(self, change):
        self.value += change
        self.displayString = str(self.value)

    def reset(self, displayString="", baseString=""):
        self.value = 0
        super().reset(displayString=str(self.value))

class Food(Block):
    """
    Object used to represent the food that the snake is after

    Public Methods:
    relocate()
    isSafe(rect)
    """

    def __init__(self, game):
        Block.__init__(self, game.size, 0, 0, (255, 0, 100))
        self.game = game
        self.relocate()

    def relocate(self):
        """Move the food to a random spot in the grid"""
        self.x, self.y = randint(self.game.leftBoundry/self.game.size, self.game.rows), randint(0, self.game.cols)
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
    def __init__(self, game):
        super().__init__(game.size, floor(game.rows + game.leftBoundry/game.size/2) *
                       game.size, floor(game.cols/2) * game.size, (124, 252, 0))
        self.game = game
        self.dx = 0
        self.dy = 0
        self.changeDirection(Direction.UP)
        self.tail = []
        self.hit_wall = False
        self.hit_self = False

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

    def changeDirection(self, direction, avoidFlip=True):
        """Change the direction of the snake"""
        # You can't go backwards into yourself, and don't do anything if you're already going that direction
        # If you're just a head, you can go backwards
        if (direction == self.getDirection() or (avoidFlip and direction == self.getDirection().flip()) and not len(self.tail) == 0):
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
            for block in self.tail[1:]:
                block.resetColor()
            self.tail[0].color = (255, 250, 205)
        self.y += self.dy # Move head
        self.x += self.dx 

        self.hitWall()
        if self.hit_wall:
            if self.game.noBoundry:
                self.__goThroughWall()
            elif self.game.assist:
                self.assist()
            else:
                self.die()

        if not self.checkEat():  # Only check if the snake hits itself if it didn't eat, eating causes another block to be placed exactly where the snake is
            self.hitSelf()
            if self.hit_self:
                if self.game.assist:
                    self.assist()
                else:
                    self.die()
                self.hit_self = False

    def hitWall(self):
        """Check if the snake hit the wall"""
        if self.x < self.game.leftBoundry or self.y < 0 or self.x > self.game.rightBoundry - self.game.size or self.y > self.game.gameHeight - self.game.size:  # hit edge of screen
            self.hit_wall = True
        else:
            self.hit_wall = False

    def hitSelf(self):
        """Check if the snake head hit part of it's tail"""
        for block in self.tail:
            if self.colliderect(block):
                self.hit_self = True
                return
        self.hit_self = False

    def die(self):
        """Kill the snake, end the game"""
        self.game.done = True
        print("You have died! Game Over")
        print(f"Final score = {self.game.score.value}")

    def safeDirections(self):
        """
        Returns a list of the safe directions that the snake can go at the given spot. 
        """
        safe = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        safe.remove(Direction(self.getDirection())) # remove the unsafe direction
        if self.game.assist:
            self.checkCollideWithTail(safe)

        if not self.game.noBoundry: #Check walls if they can kill you
            self.checkCollideWithWall(safe)

        return safe

    def checkCollideWithWall(self, list):
        """
        Checks if the directions in the given list would cause a collision with a wall

        Arguments:
        list - a list of directions
        """
        for item in list:
            if self.x + item.value[0] < self.game.leftBoundry or self.y + item.value[1] < 0 or self.x + item.value[0] > self.game.rightBoundry - self.game.size or self.y + item.value[1] > self.game.gameHeight - self.game.size:
                list.remove(item)

    def checkCollideWithTail(self, list):
        """
        Checks if the given direction would cause a collision with the tailof the snake

        Keyword Arguments: 
        list - a list of the current safe directions, will update the list in place
        """
        for block in self.tail:
            if block == self.tail[1]:
                continue
            for item in list:
                if Block(self.game.size, self.x + item.value[0] * self.game.size, self.y + item.value[1] * self.game.size).colliderect(block):
                    list.remove(item)

    def __unmove(self):
        """
        Undo the last move
        """
        self.x -= self.dx
        self.y -= self.dy

        self.hitWall()
        if self.hit_wall:
            if self.game.noBoundry:
                self.__goThroughWall()
            elif self.game.assist:
                self.assist()
            else:
                self.die()

        self.checkEat()

    def __goThroughWall(self):
        """
        Transport through the wall
        """
        if self.x < self.game.leftBoundry:
            self.x = self.game.rightBoundry - self.game.size
        elif self.y < 0:
            self.y = self.game.gameHeight - self.game.size
        elif self.x > self.game.rightBoundry - self.game.size:
            self.x = self.game.leftBoundry
        elif self.y > self.game.gameHeight - self.game.size:
            self.y = 0
        else:
            raise RunTimeError("Position invalid")
            

    def assist(self):
        """
        Assist the snake if it hits itself. Causes the snake to instead choose a random, safe direction to turn.
        """
        #Move snake back from bad move
        self.__unmove()
        safeDirections = self.safeDirections()
        if len(safeDirections) == 0:
            self.die()
        else:
            self.changeDirection(safeDirections[randint(0, len(safeDirections)-1)], avoidFlip=False)
            self.move()

    def distanceToFood(self):
        """
        Computes the distance from the head of the snake to the food

        returns that distance
        """
        x = abs(self.x - self.game.food.x)
        y = abs(self.y - self.game.food.y)
        return x + y


def main():
    """
    Main entry into the program, creates a game and plays it
    """
    game = Game(assist=True, noBoundry=True)
    game.play()


if __name__ == "__main__":
    main()
