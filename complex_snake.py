#! /usr/bin/env python3

import snake
import qsnake
import random
import pygame
import bitmap

class Game(snake.Game):
    def __init__(self, size=40, fps=60, windowHeight=600, windowWidth=960,
    gameHeight=600, gameWidth=800, speed=10, noBoundry = False, assist = False,
    screen=True, watchTraining = False):
        super().__init__(size, fps, windowHeight, windowWidth, gameHeight,
        gameWidth, speed, noBoundry, assist, screen)
        self.redirection_blocks = self.__createBlocks()
        self.snake = Snake(self)
        self.food = Food(self)
        self.watchTraining = watchTraining

    def __sortBlocksBottomL(self, blocks):
        """
        Sorts blocks based on the lowest left block first
        """
        blocks.sort(key=lambda block: (block.x, -block.y))

    def __findGaps(self, blocks, current_index = 0, current_gap = 0):
        # Finds the gaps in the blocks. There must be at least two blocks in 
        # the shape.
        sorted_blocks = blocks
        self.__sortBlocksBottomL(sorted_blocks)
        seen = []
        for start_block in sorted_blocks:
            gaps = 0
            if start_block in seen:
                continue
            else:
                seen += [start_block]

            for end_block in sorted_blocks:
                if start_block == end_block:
                    continue

                    seen += [start_block]
                if start_block.x == end_block.x:
                    gaps += start_block.y - end_block.y // self.size - 1
                elif start_block.y == end_block.y:
                    gaps += start_block.x - end_block.x // self.size - 1

    def __touchingOtherBlock(self, block, blocks):
        """
        Retruns a list of blocks that are touching the given block

        Argument List:
        blocks - List of blocks on the board
        """
        directions = [snake.Direction.UP, snake.Direction.DOWN,
            snake.Direction.LEFT, snake.Direction.RIGHT]

        blocks_touching = []
        for direction in directions:
            dx, dy = map(lambda x: x*block.width, direction.value)
            newBlock = snake.Block(block.width, block.x + block.dx, block.y + block.dy)
            if newBlock in blocks:
              blocks_touching += [newBlock] 
                
        return blocks_touching

    def __gridDistanceBetweenBlocks(self, start, end):
        """
        Retruns the number of grid squares between two blocks. 
        Note: Distance is always >= 1
        """
        if start == end:
           raise ValueError("The blocks are the same!") 

        return abs(start.x - end.x) + abs(start.y - end.y) / self.size

    def __shareAxis(self, start, end):
        """
        Determines if two blocks share an axis on the board
        """
        if start == end:
           raise ValueError("The blocks are the same!") 

        return self.__shareYAxis(start, end) or self.__shareXAxis(start, end)

    def __shareXAxis(self, start, end):
        """
        Determines if two blocks share the same x-axis on the board
        """
        if start == end:
           raise ValueError("The blocks are the same!") 

        return start.x == end.x

    def __shareYAxis(self, start, end):
        """
        Determines if two blocks share the same y-axis on the board"
        """
        if start == end:
           raise ValueError("The blocks are the same!") 

        return start.y == end.y

    def __closest2Walls(self, block):
        """
        Returns the two closest walls to the given point on the grid
        """

        #Add error checking
        walls = [snake.Block(block.width, block.x, 0), snake.Block(block.width,
            self.leftBoundry, block.x), snake.Block(block.width, block.x,
            self.gameHeight), snake.Block(block.width, block.rightBoundry, block.y)]

        distances = sorted([self.__gridDistanceBetweenBlocks(block, x) for x in walls])

        return distances[:2]

    def __searchEdge(self, origin, blocks, last_direction = None, block = None,
        distance_travelled = 0):

        if block == origin: 
            return True

        if distance_travelled >= 2:
            return block

        if block == None:
            block = origin

        directions = [snake.Direction.UP, snake.Direction.DOWN,
        snake.Direction.LEFT, snake.Direction.RIGHT]

        if last_direction: #We won't undo the last move
            directions.remove(~last_direction)

        for direction in directions:
            dx, dy = map(lambda x: x * block.width, direction.value)
            newBlock = snake.Block(block.width, block.x + dx, block.y + dy)

            if newBlock in blocks:
                further=self.__searchEdge(origin, blocks, direction, newBlock, distance_travelled)
            else:
                further = self.__searchEdge(origin, blocks, direction, newBlock, distance_travelled + 1)

        return False

    def __isEdge(self, blocks, block):
        return self.__searchEdge(block, blocks)

    def __findEdges(self, blocks):
        """
        Finds the edges of shapes in the board

        Argument List:
        blocks: All of the blocks on the board
        """
        edges = []
        for block in blocks:
            if self.__isEdge(blocks, block):
                edges += [block]

        # Remove edges that aren't a part of a shape
        true_edges = []
        count = 0
        for start_edge in edges:
            count = 0
            for end_edge in edges:
                if start_edge == end_edge:
                    continue

                if self.__shareAxis(start_edge, end_edge):
                    count += 1
                    if count >= 2:
                        true_edges += [start_edge]
                        break

        return true_edges

    def __addCorners(self, blocks):
        temp_blocks = []
        for block in blocks:
            # We have to take into account the new blocks we have added so we 
            # Don't double add
            encoded_map = self.__mapBlockSurrounding((block.x, block.y), blocks + temp_blocks)
            if encoded_map[1] and encoded_map[3] and not encoded_map[0]:
                temp_blocks += [snake.Block(
                    block.width, block.x - block.width, block.y - block.width)]
                encoded_map.set(0)

            if encoded_map[1] and encoded_map[4] and not encoded_map[3]:
                temp_blocks += [snake.Block(
                    block.width, block.x - block.width, block.y + block.width)]
                encoded_map.set(3)

            if encoded_map[6] and encoded_map[3] and not encoded_map[5]:
                temp_blocks += [snake.Block(
                    block.width, block.x + block.width, block.y - block.width)]
                encoded_map.set(5)

            if encoded_map[6] and encoded_map[4] and not encoded_map[7]:
                temp_blocks += [snake.Block(
                    block.width, block.x + block.width, block.y + block.width)]
                encoded_map.set(7)

            if encoded_map[0]: 
                if not encoded_map[1]:
                    temp_blocks += [snake.Block(
                        block.width, block.x - block.width, block.y)]
                    encoded_map.set(1)

                if not encoded_map[3]:
                    temp_blocks += [snake.Block(
                        block.width, block.x, block.y - block.width)]
                    encoded_map.set(3)

            if encoded_map[2]:
                if not encoded_map[1]:
                    temp_blocks += [snake.Block(
                        block.width, block.x - block.width, block.y)]
                    encoded_map.set(1)

                if not encoded_map[4]:
                    temp_blocks += [snake.Block(
                        block.width, block.x, block.width + block.y)]
                    encoded_map.set(4)

            if encoded_map[5]:
                if not encoded_map[3]:
                    temp_blocks += [snake.Block(
                        block.width, block.x, block.y - block.width)]
                    encoded_map.set(3)

                if not encoded_map[6]:
                    temp_blocks += [snake.Block(
                        block.width, block.x + block.width, block.y)]
                    encoded_map.set(6)

            if encoded_map[7]:
                if not encoded_map[4]:
                    temp_blocks += [snake.Block(
                        block.width, block.x, block.width + block.y)]

                if not encoded_map[6]:
                    temp_blocks += [snake.Block(
                        block.width, block.x + block.width, block.y)]
                    encoded_map.set(6)

        return temp_blocks
        

    def __mapBlockSurrounding(self, block, blocks):
        """
        Maps the surrounding of the 
        """
        encoded_map = bitmap.BitMap(8) #8 Surrounding blocks
        total_walls = 0

        #Make list of all surrounding blocks in board
        bx, by = block
        surrounding = [(sur_x, sur_y) for sur_x in
            range(bx - self.size, bx + self.size * 2, self.size) 
            for sur_y in range(by - self.size, by + self.size * 2, self.size)
            if sur_x != bx or sur_y != by]

        #Encode the surroundings into the bitmap
        for index, (x, y) in enumerate(surrounding):
            if (snake.Block(self.size, x, y) in blocks or x <= self.leftBoundry
                or y <= 0 or x >= self.rightBoundry or y >= self.gameHeight
                ):
                
                encoded_map.set(index)

        return encoded_map

    def __distanceInEdges(self, edges, blocks):
        sorted_edges = sorted(edges, key=lambda e: (e.x, e.y))
        same_x = [[sorted_edges[:2]], [sorted_edges[2:]]]
        same_y = [[sorted_edges[::2]], [sorted_edges[1::1]]]

        total_distance = 0
        distance_between_x = self.__gridDistanceBetweenBlocks(*same_x)
        for x in range(distance_between_x):
            check_block = snake.Block(x.width, same_x[0].x + x * self.size, same_x[1])
            if check_block not in blocks:
                total_distance += 1

        distance_between_y = self.__gridDistanceBetweenBlocks(*same_y)
        for y in range(distance_between_y):
            check_block = snake.Block(x.width, same_x[0].x, same_x[1] + y * self.size)
            if check_block not in blocks:
                total_distance += 1

        return total_distance

    def __blockSafety(self, block, blocks):
        """
        Examines if the block is safely placed
        """
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

        #Add the corners so we can find the edges
        #Doesn't get corners that don't exist (ie: "fake" corner)
        #   ### <- This   ##
        #   #  #         #  #
        #              ->   #
        #   #            # ##
        #                   #
        #  # #
        #    
        #Thought: if we have 3 corners we can find the 4th
        corner_blocks = self.__addCorners(blocks) 
        blocks_with_corners = blocks + corner_blocks

        #if len(blocks) >= 3:
        if False: #This isn't working 
            edges = self.__findEdges(blocks_with_corners)

            if len(edges) == 3:
                x_values = [x.x for x in edges]
                y_values = [x.y for x in edges]


                missing_x = [m for m in x_values if x_values.count(m) == 1]
                missing_y = [m for m in y_values if y_values.count(m) == 1]

                edges += [snake.Block(self.size, missing_x, missing_y)]

            elif len(edges) > 4:
                raise RunTimeError("More than 4 edges")
            elif len(edges) < 4:
                return True

            return self.__distanceInEdges(edges, blocks) < 2
        else:
            return True

    def __isSafe(self, blocks):
        """
        Checks if the current lst of blocks is valid and isn't blocking areas
        """
        for block in blocks:
            if not self.__blockSafety(block, blocks):
                return False
            
        return True

    def __createBlocks(self):
        """
        Creates the blocks that will push away and place them on the baord.

        TODO: Place the blocks, randomly, but check that they don't limit an
        area? Or place the blocks in the same place every time?
        """
        block_coordinates = []
        for i in range(10):
            safe = False
            while not safe:
                block_coordinates.append(
                    snake.Block(self.size, 
                        random.randint(self.leftBoundry/self.size, self.rows) * self.size, 
                        random.randint(0, self.cols) * self.size, 
                        color=(220, 220, 220)))

                if self.__isSafe(block_coordinates):
                    safe = True
                else:
                    block_coordinates.pop()

        return block_coordinates

    def drawBoard(self):
        """
        Draws the board.
        Inherits from snake.DrawBoard()

        Change - Also draw the gray redirection blocks
        """
        super().drawBoard()
        for block in self.redirection_blocks:
            pygame.draw.rect(self.screen, block.color, block)
            
class Snake(qsnake.Snake):
    def __init__(self, game):
        super().__init__(game)
        self.hit_redirect = False

    def move(self):
        """
        Move the snake.

        The snake moves by shifting the entire array of the tail to the left (removing the last
        element) and putting a new Block where the head used to be. 
        """

        self.hit_self = False
        self.hit_wall = False
        self.hit_redirect = False

        if self.tail:
            self.tail = self.tail[1:]
            self.tail.append(snake.Block(self.game.size, self.x, self.y))
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

        self.hitRedirect(newX, newY)
        if self.hit_redirect:
            self.assist(tail=True)
            self.checkEat(self.x, self.y)
            return

        if not self.checkEat(newX, newY):  
        # Only check if the snake hits itself if it didn't eat, 
        # eating causes another block to be placed exactly where the snake is
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

    def hitRedirect(self, newX, newY):
        """
        Checks if the move about to be made will collide with any of the blocks
        that will redirect the snake.
        """
        newBlock = snake.Block(self.width, newX, newY)
        for block in self.game.redirection_blocks:
            if block.colliderect(newBlock):
                self.hit_redirect = True
                break
        
class Food(snake.Food):
    def __init__(self, game):
        super().__init__(game)

    def isSafe(self):
        """
        Determine if the food is in a reachable location

        OVERRIDE
        """
        return (super().isSafe() and snake.Block(self.width, self.x, self.y) not
            in self.game.redirection_blocks)
        
def main():
    game = Game()
    game.play()

if __name__ == "__main__":
    main()
