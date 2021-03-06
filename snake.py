#! /usr/bin/env python3
from enum import Enum
from random import randint, choice
from math import floor
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #Don't show the pygame startup message
import pygame
import sys

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

    def __init__(self, size=40, fps=60, windowHeight=600, windowWidth=960, gameHeight=600, gameWidth=800, speed=10, noBoundry = False, assist = False, screen=True):
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
        self.score = 0
        self.done = False
        self.text = []
        if screen:
            self.screen = pygame.display.set_mode((windowWidth, windowHeight))
        else:
            self.watchTraining = False
            self.screen = None

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.scoreText = Score(self.screen, (10, 10), self.font)
        self.text.append(self.scoreText)
 
        self.snake = Snake(self)
        self.food = Food(self)

        self.fps = fps
        self.speed = speed
        self.wait = False
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
            self.speed = 0
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
            pygame.display.flip()  # update display
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

    def __invert__(self):
        return Direction(list(map(lambda x: -x, self.value)))


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
    def __init__(self, screen,location, baseString, font, displayString=""):
        self.font = font
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

    def setScreen(self, screen):
        self.screen = screen

class Score(DisplayText):
    """
    Represents the score of the game

    Public Methods:
    draw() - draws the score on the screen
    changeScore() - changes the score by the given number (positive or negative)
    """
    def __init__(self, screen,location, font):
        self.value = 0
        super().__init__(screen, location, "Score: ", font, str(self.value))

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
        for block in self.game.snake.tail + [self.game.snake]: #Must include head
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

    def checkEat(self, newX, newY):
        """
        Checks if the snake is colliding with the food object.
        Updates the score if the food is eaten.

        returns True if colliding and False otherwise
        """
        newBlock = Block(self.width, newX, newY)
        if newBlock.colliderect(self.game.food):
            self.game.food.relocate()
            self.tail.append(newBlock)
            self.game.score += 1
            if hasattr(self.game, 'scoreText'):
                self.game.scoreText.changeScore(1)
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

        self.hit_self = False
        self.hit_wall = False

        if self.tail:
            self.tail = self.tail[1:]
            self.tail.append(Block(self.game.size, self.x, self.y))
            for block in self.tail[1:]:
                block.resetColor()
            self.tail[0].color = (255, 250, 205)

        newY = self.dy + self.y
        newX = self.dx + self.x

        self.hitWall(newX, newY)
        if self.hit_wall:
            if self.game.noBoundry:
                self.__goThroughWall(newX, newY)
                self.checkEat(self.x, self.y)
            elif self.game.assist:
                self.assist()
            else:
                self.die()
            return

        if not self.checkEat(newX, newY):  # Only check if the snake hits itself if it didn't eat, eating causes another block to be placed exactly where the snake is
            self.hitSelf(newX, newY)
            if self.hit_self:
                if self.game.assist:
                    self.assist()
                else:
                    self.die()
                self.hit_self = False
                return #Don't update the snake if bad move

        self.y = newY
        self.x = newX

    def hitWall(self, newX, newY):
        """Check if the snake hit the wall"""
        if newX < self.game.leftBoundry or newY < 0 or newX > self.game.rightBoundry - self.game.size or newY > self.game.gameHeight - self.game.size:  # hit edge of screen
            self.hit_wall = True

    def hitSelf(self, newX, newY):
        """Check if the snake head hit part of it's tail"""
        newBlock = Block(self.width, newX, newY)
        for block in self.tail:
            if newBlock.colliderect(block):
                self.hit_self = True
                return

    def die(self):
        """Kill the snake, end the game"""
        self.game.done = True
        print("You have died! Game Over")
        print(f"Final score = {self.game.score}")
        exit()

    def safeDirections(self, walls, tail):
        """
        Returns a list of the safe directions that the snake can go at the given spot. 
        """
        safe = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        safe.remove(Direction(self.getDirection())) # remove the unsafe direction

        if self.game.assist or tail:
            self.checkCollideWithTail(safe)

        if not self.game.noBoundry or walls: #Check walls if they can kill you
            self.checkCollideWithWall(safe)

        return safe

    def checkCollideWithWall(self, directions):
        """
        Checks if the directions in the given list would cause a collision with a wall

        Arguments:
        list - a list of directions
        """
        for item in directions:
            if (self.x + item.value[0] * self.width < self.game.leftBoundry or
                self.y + item.value[1] * self.width == 0 or self.x + item.value[0] >
                self.game.rightBoundry - self.game.size or self.y + item.value[1] >
                self.game.gameHeight - self.game.size
                ):
                directions.remove(item)
                break

    def checkCollideWithTail(self, directions):
        """
        Checks if the given direction would cause a collision with the tailof the snake

        Keyword Arguments: 
        list - a list of the current safe directions, will update the list in place
        """
        dx, dy = map(lambda x: x * self.width, self.getDirection().value)
        cur_block = Block(self.width, self.x + dx, self.y + dy)
        for block in self.tail:
            for item in directions:
                dx, dy = map(lambda x: x * self.width, item.value)
                if Block(self.game.size, cur_block.x + dx,
                    cur_block.y + dy).colliderect(block):
                    directions.remove(item)
                    break

    def __goThroughWall(self, newX, newY):
        """
        Transport through the wall
        """
        if newX < self.game.leftBoundry:
            self.x = self.game.rightBoundry - self.game.size
        elif newY < 0:
            self.y = self.game.gameHeight - self.game.size
        elif newX > self.game.rightBoundry - self.game.size:
            self.x = self.game.leftBoundry
        elif newY > self.game.gameHeight - self.game.size:
            self.y = 0
        else:
            raise RunTimeError("Position invalid")
            

    def assist(self, walls = False, tail = False):
        """
        Assist the snake if it hits itself. Causes the snake to instead choose a random, safe direction to turn.
        """
        safeDirections = self.safeDirections(walls, tail)
        if safeDirections:
            self.changeDirection(choice(safeDirections), avoidFlip=False)
            self.move()
        else:
            self.die()

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

    noBoundry = False
    assist = False
    if len(sys.argv) == 3:
        noBoundry = bool(int(sys.argv[2]))
        assist = bool(int(sys.argv[2]))
    game = Game(assist=assist, noBoundry=noBoundry)
    game.play()


if __name__ == "__main__":
    main()
