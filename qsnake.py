#! /usr/bin/env python3
import snake
import constant
import numpy as np
import pandas as pd
from random import randint
columns = ["Up", "Down", "Left", "Right"]

class QGame(snake.Game):
    """
    Snake Game using Q-Learning Algorithm in place of user input.

    Inherits from snake.Game
    """

    def __init__(self, learning_rate = .1, discount_factor = .9):
        snake.Game.__init__(self, 40, 60, 800, 600, 10, True, True)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.current_state
        self.qTable = QTable(self)


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
    def __init__(self, game):
        pd.DataFrame.__init__(self, columns=constant.COLUMNS, dtype=np.float32)
        self.game = game
        #Should initialize with a large dataframe to avoid having to recopy data 
        #over and over again?

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

    def addRow(self, index):
        """
        Adds a blank row to the QTable and updates the instance of self. 

        Arguments:
        index - the name for the row that will be added.
        """
        newQTable = self.append(constant.INITIAL_DATAFRAME, index=[index])
        self.__dict__.update(newQTable.__dict__) #Changing self doesn't work, must change self this way

    def getRow(self, index):
        """
        Returns the row of the QTable in index. If the index doesn't exist, it is created and returned. 

        Arguments:
        index - the state mapping to check if it already exists. If it doesn't exist, it is added. 

        return - the row of the QTable related to the state that was passed. 
        """
        try:
            self.loc[index]
        except KeyError:
            addRow(index)
            #Check if possible to update DF in place instead of copying over?

        return self.loc[index]

    def chooseAction(self):
        """
        Chooses the next action for the actor to take. 

        Looks up the available actions and chooses the best action based on the learning_rate

        returns the action for the actor to take.  
        """
        if randint(0,10) * .1 < self.game.learning_rate: #*.1 in order to convert the int to a decimal and 0,10 for 0, 100%
            available_directions = self.__getAvailableDirections()
            next_action = available_directions[randint(0, len(available_directions)-1)]
        else:
            possible_actions = QTable.findIndiciesOfOccurences(self.getRow(self.game.current_state), self.getRow(self.game.current_state).max())
            next_action = possible_actions[randint(0, len(possible_actions)-1)]
        return next_action

    def __getAvailableDirections(self):
        """
        Returns a list of all the available direction names.

        Filters out the current direction and the flip direction (because the snake can't go further forward or back into itself)
        """
        #Can the snake keep going forward? If this is updated every frame then the actor can definitely continue going straight. 
        return [direction.name for direction in snake.Direction 
            if direction != self.game.snake.getDirection() 
            and direction != self.game.snake.getDirection().flip()
            and direction != self.game.snake.getDirection() == snake.Direction.NONE]

def main():
    #14 cols, 19 rows
    game = QGame()

if __name__ == "__main__":
    main()