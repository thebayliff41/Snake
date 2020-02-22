#! /usr/bin/env python3
import snake
import pygame
import constant
import numpy as np
import pandas as pd
from random import randint
import bitmap
import itertools


class QGame(snake.Game):
    """
    Snake Game using Q-Learning Algorithm in place of user input.

    Inherits from snake.Game
    """

    def __init__(self, learning_rate=.1, discount_factor=.9):
        snake.Game.__init__(self, noBoundry=True, assist=True)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.current_state = QTable.enocodeState(self.snake, self.food)
        self.qTable = QTable(self)

    def play(self):
        """
        Main game loop. Handles movement and updating screen
        """
        timer = 0
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

            if timer * self.speed > 1:  # Controls the speed of the snake
                timer = 0
                action_to_take = self.qTable.chooseAction()
                self.snake.changeDirection(snake.Direction[action_to_take])
                self.snake.move()
                old_state = self.current_state
                self.current_state = QTable.enocodeState(self.snake, self.food)
                self.qTable.updateQValue(
                    old_state, self.current_state, action_to_take, self.snake.getReward())

            self.drawBoard()
            timer += self.clock.tick(self.fps) / 1000


class QTable(pd.DataFrame):
    """
    QTable to hold all of the data during the iterations of the game. 

    Inherits from pandas.DataFrame

    Instance Methods:
    addRow()
    getRow() 
    chooseAction()

    private Methods:
    __etAvailableDirections()

    Static Methods:
    findIndiciesOfOccurences()
    """

    def __init__(self, game, learning_rate=.1, discount_factor=.9):
        pd.DataFrame.__init__(self, columns=constant.COLUMNS, dtype=np.float32)
        self.game = game
        self.learning_rate = discount_factor
        self.discount_factor = learning_rate

        # Should initialize with a large dataframe to avoid having to recopy data
        # over and over again?

    @staticmethod
    def findIndiciesOfOccurences(row, check_value):
        """
        Finds the indexes of the given value in the given row.

        Arguments:
        row - pandas.Series
        value - value held in row. 

        returns - list of indexes that hold the value, empty list if no values are found.
        """
        return [index for index, value in row.items() if value == check_value]

    def __addRow(self, index):
        """
        Adds a blank row to the QTable and updates the instance of self. 

        Arguments:
        index - the name for the row that will be added.
        """
        newQTable = self.append(
            pd.DataFrame(
                [[0, 0, 0, 0]], index=[index], columns=constant.COLUMNS))
        # Changing self doesn't work, must change self this way
        self.__dict__.update(newQTable.__dict__)

    def getRow(self, index):
        """
        Returns the row of the QTable in index. If the index doesn't exist, it is created and returned. 

        Arguments:
        index - the state mapping to check if it already exists. If it doesn't exist, it is added. 

        return - the row of the QTable related to the state that was passed. 
        """
        try:
            return self.loc[index]
        except KeyError:
            self.__addRow(index)
            # Recursive call to get the location after it has been added
            return self.getRow(index)

    def chooseAction(self):
        """
        Chooses the next action for the actor to take. 

        Looks up the available actions and chooses the best action based on the learning_rate

        returns the action for the actor to take by the name value of the Direction enum.
        """
        if randint(0, 10) * .1 < self.game.learning_rate:  # *.1 in order to convert the int to a decimal and 0,10 for 0, 100%
            available_directions = self.__getAvailableDirections()
            next_action = available_directions[randint(
                0, len(available_directions)-1)]
        else:
            possible_actions = QTable.findIndiciesOfOccurences(self.getRow(
                self.game.current_state), self.getRow(self.game.current_state).max())
            next_action = possible_actions[randint(0, len(possible_actions)-1)]
        return next_action

    def __getAvailableDirections(self):
        """
        Returns a list of all the available direction names.

        Filters out the current direction and the flip direction (because the snake can't go further forward or back into itself)
        """
        # Can the snake keep going forward? If this is updated every frame then the actor can definitely continue going straight.
        return [direction.name for direction in snake.Direction
                if direction != self.game.snake.getDirection()
                and direction != self.game.snake.getDirection().flip()
                and direction != self.game.snake.getDirection() == snake.Direction.NONE]

    def updateQValue(self, current_state, next_state, action, reward):
        """
        Update the Qvalue for the current state using the QLearning algorithm
        Q(current) = Q(current) + learning_rate * (reward + discount * max(Q(current)) - Q(current))

        Arguments:
        current_state - the state to update
        next_state - the state the actor will be in choosing the action from the current state
        action - the action that has been chosen
        reward - The reward received for moving into the new state
        """
        currentRow = self.getRow(current_state)
        nextRow = self.getRow(next_state)
        value = currentRow.at[action]

        newValue = reward + self.discount_factor * nextRow.max() - value
        currentRow.at[action] = value + self.learning_rate * newValue

    @staticmethod
    def enocodeState(snake_obj, food):
        """
        Encodes a state into the following format: 
        relativeFruitx,relativeFruity:nearestObsUP:nearestObsDOWN:nearestObsLEFT:nearestObsRIGHT

        Each of the following are bits, 0 for safe, 1 for obstacle
        Left,BottomLeft,Bottom,BottomRight,Right,TopRight,Top,TopLeft
        TopLeft,Left,BottomLeft,Top,Bottom,TopRight,Right,BottomRight

        returns the encoded string as a bitmap
        """
        # Note, in range() the stop parameter is set as x + width * 2 because the end value is not inclusive
        # Here, we are Getting the 8 blocks surrounding the head (in the order of the encoding) and for each of
        # the 8 blocks we are attaching every piece of the tail. This will give 8 * len(tail) values to compare. 
        surrounding = [(x, y, block) for x in range(snake_obj.x - snake_obj.width, snake_obj.x + snake_obj.width * 2, snake_obj.width)
                       for y in range(snake_obj.y + snake_obj.width, snake_obj.y - snake_obj.width * 2, -snake_obj.width)
                       for block in snake_obj.tail
                       if (x, y) != (snake_obj.x, snake_obj.y)]

        encoded_map = bitmap.BitMap(8)

        # Checks each block in the surrounding and checks if it is near a wall, or near a piece of the tail
        bit_position = 0
        for (index, (x, y, block)) in enumerate(surrounding):
            if index % len(snake_obj.tail) == 0 and index != 0: #Don't increment immediately
                bit_position += 1
            if (x == 0 or y == 0 or x == constant.WINDOW_WIDTH or y == constant.WINDOW_HEIGHT
                or (block != None and block.colliderect(snake.Block(constant.BLOCK_SIZE, x, y))) 
                and not encoded_map.test(bit_position-1)):

                encoded_map.set(bit_position)

        return encoded_map.tostring()


def main():
    # 14 cols, 19 rows
    game = QGame()
    # game.play()


if __name__ == "__main__":
    main()