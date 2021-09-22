#! /usr/bin/env python3

import blog_2
import pygame
import random
import bitmap

class Game(blog_2.Game):
    def __init__(self, fps, width, height):
        super().__init__(fps, width, height)
        self.block_width = self.snake.width
        self.width = width
        self.height = height
        self.blocks = self.__create_blocks()
        self.snake = Snake(self, self.block_width)

    def __create_blocks(self):
        block_coordinates = []
        for i in range(10):
            safe = False
            while not safe:
                block = blog_2.Block(self.snake.width, 
                        random.randint(0, self.height/self.snake.width) * self.snake.width, 
                        random.randint(0, self.width/self.snake.width) *
                        self.snake.width) 

                if block in block_coordinates:
                    safe = False

                block_coordinates.append(block)

                if self.__isSafe(block_coordinates):
                    safe = True
                else:
                    block_coordinates.pop()

        return block_coordinates

    def __isSafe(self, blocks):
        for block in blocks:
            if not self.__blockSafety(block, blocks):
                return False
        return True

    def __mapBlockSurrounding(self, block, blocks):
        encoded_map = bitmap.BitMap(8) #8 Surrounding blocks
        total_walls = 0

        #Make list of all surrounding blocks in board
        bx, by = block
        surrounding = [(sur_x, sur_y) for sur_x in
            range(bx - self.block_width, bx + self.block_width * 2, self.block_width) 
            for sur_y in range(by - self.block_width, by + self.block_width * 2,
            self.block_width)
            if sur_x != bx or sur_y != by]

        #Encode the surroundings into the bitmap
        for index, (x, y) in enumerate(surrounding):
            if (blog_2.Block(self.block_width, x, y) in blocks or x <= 0
                or y <= 0 or x >= self.width or y >= self.height 
                ):
                
                encoded_map.set(index)

        return encoded_map

    def __blockSafety(self, block, blocks):
        #Check blocks L R U and D from current block and enocde that area
        all_surroundings = [(block.x - block.width, block.y), (block.x +
            block.width, block.y), (block.x, block.y - block.width), (block.x,
            block.y + block.width)]

        #Encode each surrounding
        for surrounding in all_surroundings:
            encoded_map = self.__mapBlockSurrounding(surrounding, blocks)
            #Check for conflict
            if encoded_map.count() >= 3: #If it's less, theres no possibility of conflict
                #Check for -_- shape (impossible to escape)
                if ((encoded_map[3] and encoded_map[4]
                    and (encoded_map[1] or encoded_map[6]))
                    or ((encoded_map[1] and encoded_map[6]) 
                    and (encoded_map[3] or encoded_map[4]))
                    ):
                    return False #Not valid, conflict exists

        return True

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
            pygame.draw.rect(self.screen, blog_2.Snake.color, self.snake)
            pygame.draw.rect(self.screen, blog_2.Food.color, self.food)

            for block in self.snake.tail:
                pygame.draw.rect(self.screen, blog_2.Block.color, block)

            ###Added Lines
            for block in self.blocks:
                pygame.draw.rect(self.screen, ((220, 220, 220)), block)
            ###End Added Lines
            timer += self.clock.tick(self.fps) / 1000
            pygame.display.flip()

class Snake(blog_2.Snake):

    def __init__(self, game, size):
        super().__init__(game, size)
        self.hit_block = False

    def move(self):
        super().move()
        self.hitBlock()

    def hitBlock(self):
        for block in self.game.blocks:
            if self.colliderect(block):
                self.hit_block = True
                break
        else:
            self.hit_block = False

    def checkDead(self):
        if self.hit_self or self.hit_wall or self.hit_block:
            return True
        else:
            return False

def main():
    game = Game(60, 800, 600)
    game.play()
    
if __name__ == "__main__":
    main()
