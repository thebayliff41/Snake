#! /usr/bin/env python3
import blog_2
import pygame
import pandas as pd
import bitmap
import random
import numpy as np
from scipy.stats import describe
import json
import multiprocessing

class QGame(blog_2.Game):
    def __init__(self, training=False):
        super().__init__(60, 800, 600)
        self.table = QTable()
        self.snake = Snake(self, 40)
        self.current_state = self.table.encodeState(self.snake, self.food)
        self.training = training

    def reset(self):
        self.food = blog_2.Food(self, 40)
        self.snake = Snake(self, 40)
        self.current_state = self.table.encodeState(self.snake, self.food)
        self.score.reset()
        self.done = False

    def getDistanceBetweenFoodAndSnake(self):
        x = abs(self.food.x - self.snake.x)
        y = abs(self.food.y - self.snake.y)

        return x + y

    def gameOver(self):
        super().gameOver()

    def play(self):
        timer = 0
        speed = 10
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
                        if event.key == pygame.K_SPACE:
                            self.pause = False
                    elif event.type == pygame.QUIT:
                        self.done = True
                        self.pause = False

            if self.training:
                timer = 0
                old_state = self.current_state
                new_action = self.table.chooseAction(self.current_state, self.snake.direction)
                self.snake.changeDirection(blog_2.Direction[new_action])
                self.snake.move()
                self.snake.checkEat()
                if self.snake.checkDead():
                                self.gameOver()
                self.current_state = self.table.encodeState(self.snake, self.food)
                reward = self.snake.getReward()
                self.table.updateQValue(old_state, self.current_state, new_action, reward)
                self.clock.tick()
            else:
                if timer * speed > 1:
                    timer = 0
                    old_state = self.current_state
                    new_action = self.table.chooseAction(self.current_state, self.snake.direction)
                    self.snake.changeDirection(blog_2.Direction[new_action])
                    self.snake.move()
                    self.snake.checkEat()
                    if self.snake.checkDead():
                        self.gameOver()
                    self.current_state = self.table.encodeState(self.snake, self.food)
                    reward = self.snake.getReward()
                    self.table.updateQValue(old_state, self.current_state, new_action, reward)

                self.screen.fill((0, 0, 0))
                self.score.draw()
                pygame.draw.rect(self.screen, blog_2.Snake.color, self.snake)
                pygame.draw.rect(self.screen, blog_2.Food.color, self.food)

                for block in self.snake.tail:
                    pygame.draw.rect(self.screen, blog_2.Block.color, block)

                pygame.display.flip()
                timer += self.clock.tick(self.fps) / 1000


    #def play(self):
    #    timer = 0
    #    speed = 10
    #    input_buffer = []
    #    moved = False
    #    while not self.done:
    #        for event in pygame.event.get():
    #            if event.type == pygame.QUIT:
    #                self.done = True

    #            if event.type == pygame.KEYDOWN:
    #                if moved:
    #                    self.userInput(event.key)
    #                    moved = False
    #                else:
    #                    input_buffer.append(event.key)

    #        while self.pause:
    #            for event in pygame.event.get():
    #                if event.type == pygame.KEYDOWN:
    #                    if event.key == pygame.K_SPACE:
    #                        self.pause = False
    #                elif event.type == pygame.QUIT:
    #                    self.done = True
    #                    self.pause = False

    #        #if timer * speed > 1:
    #        timer = 0
    #        old_state = self.current_state
    #        new_action = self.table.chooseAction(self.current_state, self.snake.direction)
    #        self.snake.changeDirection(blog_2.Direction[new_action])
    #        self.snake.move()
    #        self.snake.checkEat()
    #        if self.snake.checkDead():
    #            self.gameOver()
    #        self.current_state = self.table.encodeState(self.snake, self.food)
    #        reward = self.snake.getReward()
    #        self.table.updateQValue(old_state, self.current_state, new_action, reward)
    #        self.clock.tick()

    #        #self.screen.fill((0, 0, 0))
    #        #self.score.draw()
    #        #pygame.draw.rect(self.screen, blog_2.Snake.color, self.snake)
    #        #pygame.draw.rect(self.screen, blog_2.Food.color, self.food)

    #        #for block in self.snake.tail:
    #        #    pygame.draw.rect(self.screen, blog_2.Block.color, block)

    #        #pygame.display.flip()
    #        #timer += self.clock.tick(self.fps) / 1000

class Snake(blog_2.Snake):
    def __init__(self, game, size):
        super().__init__(game, size)
        self.distance = self.game.getDistanceBetweenFoodAndSnake()

    def move(self):
        super().move()

    def getReward(self):
        new_distance = self.game.getDistanceBetweenFoodAndSnake()
        if self.ate:
            reward = 1
            self.distance = new_distance
        elif self.checkDead():
            reward = -100
        else:
            if new_distance < self.distance:
                reward = .1
            else:
                reward = -.2 

        self.distance = new_distance

        return reward
    
class QTable(pd.DataFrame):
    def __init__(self, learning_rate=.1, discount_factor=.9):
        super().__init__(columns=["UP", "DOWN", "LEFT", "RIGHT"])
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def getRow(self, index):
        try:
            self.loc[index]
        except KeyError:
            self.loc[index] = [0, 0, 0, 0] 
        finally:
            return self.loc[index]

    def updateQValue(self, current_state, next_state, action, reward):
        currentRow = self.getRow(current_state)
        nextRow = self.getRow(next_state)
        value = currentRow.at[action] #Q_old

        newValue = reward + self.discount_factor * nextRow.max() - value
        toInsert = value + self.learning_rate * newValue
        self.loc[current_state].at[action] = toInsert

    def chooseAction(self, current_state, current_direction):
        currentRow = self.getRow(current_state)
        opposite_direction = ~current_direction
        #List comprehension gives every index (action) that equals the max of the row of the current state we are in.
        otherActions = [[index, value] for index, value in currentRow.items() if index != opposite_direction.name]
        max_actions = [index for index, value in otherActions if value == max(otherActions, key=lambda x:x[1])[1]]
        next_action = max_actions[random.randint(0, len(max_actions) - 1)]
        return next_action
    
    def encodeState(self, snake_obj, food):
        encoded_map = bitmap.BitMap(12)
        bit_position = 0
        leftBoundry = 0
        rightBoundry = 800
        bottomBoundry = 600
        topBoundry = 0

        #Encode the surrounding
        #Go over the columns from left to right
        for x in range(snake_obj.x - snake_obj.width, snake_obj.x + snake_obj.width * 2, snake_obj.width):
            #Go over the squares from top to bottom
            for y in range(snake_obj.y - snake_obj.width, snake_obj.y + snake_obj.width * 2, snake_obj.width):
                if (x, y) == (snake_obj.x, snake_obj.y):
                    continue
                #Loop over the tail
                for block in [snake_obj] + snake_obj.tail:
                    #Check if that square has a tail block or hits a wall
                    if blog_2.Block(snake_obj.width, x, y).colliderect(block) or y == bottomBoundry or \
                        y == topBoundry or x == leftBoundry or x == rightBoundry:
                        encoded_map.set(bit_position)
                        break
                bit_position += 1

        #Enocde Quadrants
        #food is on the right of the head and above or equal to the head
        if food.x > snake_obj.x and food.y <= snake_obj.y:
            bit_position += 2 #00
        #Food is on the left or equal to the head and above the head
        elif food.x <= snake_obj.x and food.y < snake_obj.y:
            encoded_map.set(bit_position)
            bit_position += 2
        #Food is on the left of the head and below or equal to the head
        elif food.x < snake_obj.x and food.y >= snake_obj.y:
            bit_position += 1
            encoded_map.set(bit_position)
            bit_position += 1
        #Food is on the right of or equal to the head and below the head
        else:
            encoded_map.set(bit_position)
            encoded_map.set(bit_position + 1)
            bit_position += 2

        #Encode Direction
        if snake_obj.direction.name == "UP":
            bit_position += 2
        elif snake_obj.direction.name == "LEFT":
            encoded_map.set(bit_position)
            bit_position += 2
        elif snake_obj.direction.name == "DOWN":
            bit_position += 1
            encoded_map.set(bit_position)
            bit_position += 1
        else:
            encoded_map.set(bit_position)
            encoded_map.set(bit_position + 1)
            bit_position += 2

        return encoded_map.tostring()[4:] #We only need 12 bits, but the bitmap defaults to hold bytes (16 bits).

def __experiment(replications, trials):
    final_scores = []
    for replication in range(replications):
        print(f"replication = {replication}")
        game = QGame(training=True)
        for trial in range(trials):
            print(f"trial = {trial}")
            game.play()
            game.reset()
        game.play()
        final_scores += [game.score.value]

    return final_scores

def train(replications, trial_set, out_file_name=None):
    records = []
    formatted_input = []

    for trial in trial_set:
        formatted_input.append([replications, trial])

    with multiprocessing.Pool() as pool:
        results = pool.starmap(__experiment, formatted_input)

    for final_scores, trial in zip(results, trial_set):
        record = {
                'trials': trial,
                'replications': replications,
                'final_scores': final_scores
        }
        records += [record]

    if out_file_name:
        with open(out_file_name, 'a') as out_file:
            json.dump(records, out_file)
            out_file.write('\n')
    else:
        for record in records:
            print(f"Trials: {record['trials']}; Replications: {replications}")
            print(describe(record['final_scores']))

def main():
    train(100, [10, 20], "training_data.txt")

if __name__ == "__main__":
    main()
