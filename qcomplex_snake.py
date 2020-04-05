#! /usr/bin/env python3

import qsnake
import complex_snake
import snake
import pygame
import constant

redirection_blocks = None

class QGame(complex_snake.Game):
    def __init__(self, training=False, watchTraining=False):
        global redirection_blocks
        super().__init__(windowWidth=1280, noBoundry=False, assist=False, screen=watchTraining)
        redirection_blocks = self.redirection_blocks
        self.snake = complex_snake.Snake(self)
        self.current_state = QTable.encodeState(self.snake, self.food)
        self.qTable = QTable(self)
        self.current_action = self.qTable.chooseAction()
        self.speedOfUpdate = 1.5
        self.pause = False
        self.training = training
        self.watchTraining = watchTraining if training else True
        self.initText()

    def initText(self):
        if self.watchTraining:
            self.text.append(snake.DisplayText(self.screen, (10, 30), "Learning Rate: ", self.font, str(.1)))
            self.text.append(snake.DisplayText(self.screen, (10, 50), "Discount Factor: ", self.font, str(.9)))
            self.text.append(snake.DisplayText(self.screen, (10, 70), "Current Encoded State: ", self.font, self.current_state))
            self.text.append(snake.DisplayText(self.screen, (10, 90), "Current Action: ", self.font, self.current_action))
            self.text.append(snake.DisplayText(self.screen, (10, 110), "Current Reward: ", self.font, str(self.snake.getReward(self.current_state))))
            self.text.append(snake.DisplayText(self.screen, (10, 130), "Current Q-Table entry: ", self.font))
            self.text.append(snake.DisplayText(self.screen, (20, 150), "UP: ", self.font))
            self.text.append(snake.DisplayText(self.screen, (20, 170), "DOWN: ", self.font))
            self.text.append(snake.DisplayText(self.screen, (20, 190), "LEFT: ", self.font))
            self.text.append(snake.DisplayText(self.screen, (20, 210), "RIGHT: ", self.font))
            self.text.append(snake.DisplayText(self.screen, (20, 230), "Training: ", self.font, str(self.training)))

    def userInput(self, key):
        """
        Allow the user to speed up, slow down, or pause the game to better view
        the AI
        """
        if key == pygame.K_DOWN:
            self.speedOfUpdate += .1
        elif key == pygame.K_UP:
            self.speedOfUpdate -= .1
        elif key == pygame.K_SPACE and self.watchTraining:
            self.pause = ~self.pause
        elif key == pygame.K_s and self.pause and self.watchTraining:
            self.step()
            self.drawBoard()
            pygame.display.flip()
        elif key == pygame.K_d: 
            if not self.watchTraining:
                pygame.display.init()
                self.watchTraining = True
                self.screen = pygame.display.set_mode((1280, 600))
                for text in self.text:
                    text.setScreen(self.screen)
                self.drawBoard()
            else:
                self.watchTraining = False
                pygame.display.quit()
                pygame.display.init()

    def step(self):
        """
        Takes a full step into the execution of the algorithm. The snake moves and the text on the screen is updated
        """
        action_to_take = self.qTable.chooseAction()
        self.snake.changeDirection(snake.Direction[action_to_take])
        self.snake.move()
        old_state = self.current_state
        self.current_state = QTable.encodeState(self.snake, self.food)
        reward = self.snake.getReward(self.current_state)
        self.qTable.updateQValue(old_state, self.current_state, action_to_take, reward)
        self.current_action = action_to_take

        if self.watchTraining:
            self.resetText(reward)

    def resetText(self, reward):
        """
        Sets all of the text values to the correct value
        """
        self.text[3].reset(displayString=self.current_state)
        self.text[4].reset(displayString=self.current_action)
        self.text[5].reset(displayString=str(reward))
        self.text[7].reset(displayString=str(self.qTable.getRow(self.current_state, self.snake).at["UP"]))
        self.text[8].reset(displayString=str(self.qTable.getRow(self.current_state, self.snake).at["DOWN"]))
        self.text[9].reset(displayString=str(self.qTable.getRow(self.current_state, self.snake).at["LEFT"]))
        self.text[10].reset(displayString=str(self.qTable.getRow(self.current_state, self.snake).at["RIGHT"]))

    def play(self):
        """
        Main game loop. Handles movement and updating screen
        """
        timer = 0
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    quit()
                if event.type == pygame.KEYDOWN:
                    self.userInput(event.key)

            if self.pause:
                continue

            if self.training and not self.watchTraining:
                self.step()
                self.clock.tick()
                continue
            elif timer * self.speed > self.speedOfUpdate:  # Controls the speed of the snake
                timer = 0
                self.step()

            self.drawBoard()
            pygame.display.flip()  # update display
            timer += self.clock.tick(self.fps) / 1000

    def reset(self, learning_rate=None, discount_factor=None, assist=None, noBoundry=None, training=None, newQ=False):
        """
        Resets the game without resetting the Q-Table
        """
        self.snake = complex_snake.Snake(self)
        self.score = 0
        self.current_action = self.qTable.chooseAction()
        self.food = complex_snake.Food(self)
        self.done = False
        self.qTable = QTable(self) if newQ else self.qTable
        if hasattr(self, "scoreText"):
            self.scoreText.reset()
        learning = learning_rate if learning_rate != None else self.qTable.learning_rate
        discount_factor = discount_factor if discount_factor != None else self.qTable.discount_factor
        assist = assist if assist != None else self.assist
        noBoundry = noBoundry if noBoundry != None else self.noBoundry
        self.watchTraining = False if training and \
        self.watchTraining else self.watchTraining
        self.training = training if training != None else self.training
        self.qTable.setLearning(learning)
        self.qTable.setDiscount(discount_factor)
        self.assist = assist
        self.noBoundry = noBoundry

class QTable(qsnake.QTable):
    @classmethod
    def __encodeSurrounding(cls, bmap, minimum_value, snake_obj, bit_start = 0):
        global redirection_blocks
        surrounding = cls.__mapSurrounding(snake_obj, minimum_value)
        encoded_map = bmap
        # Checks each block in the surrounding and checks if it is near a wall, or near a piece of the tail
        bit_position=bit_start
        for (index, (x, y, block)) in enumerate(surrounding):
            if index % minimum_value == 0 and index != 0:  # Don't increment immediately
                bit_position += 1

            if (x < snake_obj.game.leftBoundry or y < 0 or x == snake_obj.game.rightBoundry or y == constant.WINDOW_HEIGHT
                or snake.Block(snake_obj.width, x, y) in redirection_blocks
                or (block != None and block.colliderect(snake.Block(constant.BLOCK_SIZE, x, y)))
                and not encoded_map.test(bit_position)):

                encoded_map.set(bit_position)

class Snake(complex_snake.Snake):
    def __init__(self, game):
        super().__init__(game)
        self.last_distance = self.distanceToFood()

    def getReward(self, state):
        """
        Returns the reward of the state

        Arguments:
        state - the state that the snke is in
        """
        new_distance = self.distanceToFood()
        if len(self.tail) > self.last_length:  # An apple was eaten
            self.last_length=len(self.tail)
            reward = 1
        elif self.hit_wall or self.hit_self or self.hit_redirect:
            reward = -100
        elif new_distance < self.last_distance:
            reward = .1
        else:
            reward = -.2

        self.last_distance = new_distance

        return reward
        

def main():
    #game = QGame(training = True, watchTraining = True)
    #for i in range(10):
    #    game.play()
    #    game.reset()

    #game.play()
        
    #qsnake.train(10, QGame, [i for i in range(10, 20, 10)], "complex_train_file.txt")
    qsnake.train(100, QGame, [i for i in range(10, 200 + 10, 10)], "complex_train_file.txt")

if __name__ == "__main__":
    main()
