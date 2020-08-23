import pygame
import sys
import math
import random
import copy
from collections import deque
import time

# Tips:
# Shift - Sprint
# Move mouse - Move Camera

def find_slope(agl):  # Converts angle into a slope with dx and dy
    agl = agl % 360
    if agl == 90:
        return [1, 0]
    elif agl == 270:
        return [-1, 0]
    elif agl == 180:
        return [0, 1]
    if agl == 0:
        return [0, -1]

    elif agl <= 90:
        dy = -1
        dx = math.tan(math.radians(agl))
    elif agl <= 180:
        dy = 1
        dx = 1 / math.tan(math.radians(agl - 90))
    elif agl <= 270:
        dy = 1
        dx = math.tan(math.radians(agl - 180)) * -1
    elif agl <= 360:  # Error
        dy = -1
        dx = 1 / math.tan(math.radians(agl - 270)) * -1

    return [dx, dy]


def intersection(r_px, r_py, r_dx, r_dy, s_px, s_py, s_dx,
                 s_dy):  # Finds the T1 value which correponds to the length the input ray travels in order to hit the input wall

    if r_dx == 0 and s_dx == 0:  # Same slope specifically to avoid "ZERODIVISIONERROR"
        if r_px == s_px:
            if abs(s_py - r_py) < abs(s_py + s_dy - r_py):
                T1 = (s_py - r_py) / r_dy
            else:
                T1 = (s_py + s_dy - r_py) / r_dy
            x, y = r_px + r_dx * T1, r_py + r_dy * T1
            T2 = (y - s_py) / s_dy
        else:
            return "parallel", "_"
    elif r_dy == 0 and s_dy == 0:  # Same slope specifically to avoid "ZERODIVISIONERROR"
        if r_py == s_py:
            if abs(s_px - r_px) < abs(s_px + s_dx - r_px):
                T1 = (s_px - r_px) / r_dx
            else:
                T1 = (s_px + s_dx - r_px) / r_dx
            x, y = r_px + r_dx * T1, r_py + r_dy * T1
            T2 = (x - s_px) / s_dx
        else:
            return "parallel", "_"
    elif r_dx == 0 and s_dy == 0:
        T1 = (s_py - r_py) / r_dy
        x, y = r_px + r_dx * T1, r_py + r_dy * T1
        T2 = (x - s_px) / s_dx
    elif s_dx == 0 and r_dy == 0:
        T1 = (s_px - r_px) / r_dx
        x, y = r_px + r_dx * T1, r_py + r_dy * T1
        T2 = (y - s_py) / s_dy
    elif s_dy == 0:
        T1 = (s_py - r_py) / r_dy
        x, y = r_px + r_dx * T1, r_py + r_dy * T1
        T2 = (x - s_px) / s_dx
    elif s_dx == 0:
        T1 = (s_px - r_px) / r_dx
        x, y = r_px + r_dx * T1, r_py + r_dy * T1
        T2 = (y - s_py) / s_dy

    elif r_dx == 0:
        T2 = (r_px - s_px) / s_dx
        x, y = s_px + s_dx * T2, s_py + s_dy * T2
        T1 = (y - r_py) / r_dy

    elif r_dy == 0:
        T2 = (r_py - s_py) / s_dy
        x, y = s_px + s_dx * T2, s_py + s_dy * T2
        T1 = (x - r_px) / r_dx

    # Check to see to make sure that the ray is actually shooting towards and not opposite of walls
    if abs(s_px + s_dx * T2 - x) > .000000001 or abs(s_py + s_dy * T2 - y) > .000000001: return "no", "collision"
    if abs(r_px + r_dx * T1 - x) > .000000001 or abs(r_py + r_dy * T1 - y) > .000000001:
        return "no", "collision"

    # Make sure Ray (T1) goes in assigned direction (Doesn't go down while being shot up) and
    # make sure that wall (T2) is within the wall boundaries
    elif 0 <= T1 and -0.000001 <= T2 <= 1.000001:  # Slightly adjusted for minor calculation errors
        return T1, T2
    # Base-case break
    else:
        return "no", "collision"

class Window:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.screen = pygame.display.set_mode((self.w, self.h))

    def fill(self):
        self.screen.fill((0, 0, 0))

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            sys.exit()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()


class Player:
    def __init__(self, x, y, w, h, ray_cnt, ray_gap, speed, max_stamina):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.agl = 0
        self.ray_cnt = ray_cnt
        self.ray_gap = ray_gap
        self.speed = speed
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.torchBool = False
        self.torchFuel = 100
        self.collectCnt = 0
        self.walking = True
        self.hearingFuel = max_stamina
        self.dead = False

    def draw(self, screen):
        pygame.draw.rect(screen, (70, 70, 240), (self.x - self.w / 2, self.y - self.h / 2, self.w, self.h))

    def drawStamina(self, screen):
        pygame.draw.rect(screen, (150, 50, 255), (50, 50, self.stamina * 2, 50))

    def torchUpdate(self):
        if self.torchBool:
            self.torchFuel = max(0, self.torchFuel - 0.05)
            if self.torchFuel == 0: self.torchBool = False

    def hearingUpdate(self):
        if not self.walking:
            self.hearingFuel = max(0, self.hearingFuel - 0.1)


    def torchDraw(self, screen):
        screen.blit(pygame.transform.scale(torch, (500, 500)), (250, 375))

    def drawHearingBar(self, screen):
        pygame.draw.rect(screen, (150, 255, 50), (400, 50, self.hearingFuel * 2, 50))

    def update(self, grid, mx, my):
        flag = False  # Used to flag whether or not the player has moved
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()
        speed = self.speed

        # Sprint toggle
        if keys[pygame.K_LSHIFT] and self.stamina > 0:
            speed += 1
            self.stamina -= self.max_stamina * 0.01
            if not self.walking:
                footStepRun.play()

        # Movement checks
        if keys[pygame.K_d]:
            dx += math.sin(math.radians((self.agl - 270) + self.ray_gap * self.ray_cnt / 2)) * speed
            dy += math.cos(math.radians((self.agl - 270) + self.ray_gap * self.ray_cnt / 2)) * speed * -1
            flag = True
        if keys[pygame.K_a]:
            dx += math.sin(math.radians((self.agl - 90) + self.ray_gap * self.ray_cnt / 2)) * speed
            dy += math.cos(math.radians((self.agl - 90) + self.ray_gap * self.ray_cnt / 2)) * speed * -1
            flag = True
        if keys[pygame.K_s]:
            dx += math.sin(math.radians((self.agl - 180) + self.ray_gap * self.ray_cnt / 2)) * speed
            dy += math.cos(math.radians((self.agl - 180) + self.ray_gap * self.ray_cnt / 2)) * speed * -1
            flag = True
        if keys[pygame.K_w]:
            # The idea behind finding dx and dy is that you are supposed to move in the direction of the player angle
            # The reason dy is multiplied by -1 is because a cartesian plane has positive y above the origin and negative y below
            # The coord system for this has it the other way around where positive y is below origin while negative y is above
            # However, dx doesn't need to change since this coord system follows that of a standard cartesian plane
            # Work on HERE
            dx += math.sin(math.radians(self.agl + self.ray_gap * self.ray_cnt / 2)) * speed
            dy += math.cos(math.radians(self.agl + self.ray_gap * self.ray_cnt / 2)) * speed * -1
            flag = True

        # Using key input to rotate
        if keys[pygame.K_RIGHT]:
            self.agl += 3
        elif keys[pygame.K_LEFT]:
            self.agl -= 3

        # Using mouse input to rotate
        # temp_mx, temp_my = mouse.position
        # if temp_mx > mx:
        #     self.agl += 2.5
        #     mouse.position = (mx, my)
        # elif temp_mx < mx:
        #     self.agl -= 2.5
        #     mouse.position = (mx, my)

        if flag:
            # Movement has occurred an we must check to see if player still in boundaries
            self.x, self.y = grid.collision_detect(self.x, self.y, dx, dy)

    def ray_cast(self, grid, screen):
        wall_limit = screen.h * 2 / 3
        temp_agl = self.agl
        wall_jump = screen.w / self.ray_cnt
        wall_x, wall_y = 0, screen.h / 2
        for i in range(self.ray_cnt):
            dx, dy = find_slope(temp_agl)
            # Begin collision detecting
            # Process works by checking all intercepts between ray and the vertical and horizontal walls
            # Start by checking intersections with vertical walls (Break when collision found)
            # Then check all horizontal walls (Break when collision found)
            # Take the closest intersections between vertical and horizontal walls

            bestcase_t1 = 10 ** 7  # Basically a place-holder

            # Vertical walls
            try:
                if dx > 0:
                    for i in range(1, len(grid.grid[0])):
                        s_px, s_py = i * grid.w, 0
                        t1, wall = intersection(self.x, self.y, dx, dy, s_px, s_py, 0, grid.w * len(grid.grid))
                        if t1 + wall != "nocollision" and [t1, wall] != ["parallel", "_"]:
                            # Find the x and y collision point
                            x_int, y_int = s_px, self.y + dy * t1 # Note that I'm using s_px in order to remove the rounding errors from "self.x + dx * t1"
                            idx_x, idx_y = int(x_int // grid.w), int(y_int // grid.w)
                            if grid.grid[idx_y][idx_x] == 1 and bestcase_t1 > t1:  # Check to see if wall exists here
                                bestcase_t1 = min(bestcase_t1, t1)
                                break
                            elif grid.grid[idx_y][idx_x] == 2 and bestcase_t1 > t1:  # Check to see if wall exists here
                                bestcase_t1 = min(bestcase_t1, t1)
                                break

                elif dx < 0:
                    for i in range(len(grid.grid[0]), 0,-1):
                        s_px, s_py = i * grid.w, 0
                        t1, wall = intersection(self.x, self.y, dx, dy, s_px, s_py, 0, grid.w * len(grid.grid))
                        if t1 + wall != "nocollision" and [t1, wall] != ["parallel", "_"]:

                            # Find the x and y collision point
                            x_int, y_int = s_px, self.y + dy * t1
                            idx_x, idx_y = int(x_int // grid.w) - 1, int(y_int // grid.w)

                            if grid.grid[idx_y][idx_x] == 1 and bestcase_t1 > t1:  # Check to see if wall exists here
                                bestcase_t1 = min(bestcase_t1, t1)
                                break
                            elif grid.grid[idx_y][idx_x] == 2 and bestcase_t1 > t1:  # Check to see if wall exists here
                                bestcase_t1 = min(bestcase_t1, t1)
                                break

            except IndexError:
                print(self.x, self.y)

            # Horizontal walls:

            if dy < 0:
                for i in range(len(grid.grid), 0, -1):
                    s_px, s_py = 0, i * grid.w
                    t1, wall = intersection(self.x, self.y, dx, dy, s_px, s_py, grid.w * len(grid.grid[0]), 0)
                    if t1 + wall != "nocollision" and [t1, wall] != ["parallel", "_"]:
                        x_int, y_int = self.x + dx * t1, s_py # Using s_py to remove rounding imperfections
                        idx_x, idx_y = int(x_int // grid.w), int(y_int // grid.w) - 1
                        if grid.grid[idx_y][idx_x] == 1:  # Check to see if wall exists here
                            bestcase_t1 = min(bestcase_t1, t1)
                            break
                        elif grid.grid[idx_y][idx_x] == 2 and bestcase_t1 > t1:  # Check to see if wall exists here
                            bestcase_t1 = min(bestcase_t1, t1)
                            break
            elif dy > 0:
                for i in range(1, len(grid.grid)):
                    s_px, s_py = 0, i * grid.w
                    t1, wall = intersection(self.x, self.y, dx, dy, s_px, s_py, grid.w * len(grid.grid[0]), 0)
                    if t1 + wall != "nocollision" and [t1, wall] != ["parallel", "_"]:
                        x_int, y_int = self.x + dx * t1, s_py
                        idx_x, idx_y = int(x_int // grid.w), int(y_int // grid.w)
                        if grid.grid[idx_y][idx_x] == 1:  # Check to see if wall exists here
                            bestcase_t1 = min(bestcase_t1, t1)
                            break
                        elif grid.grid[idx_y][idx_x] == 2 and bestcase_t1 > t1:  # Check to see if wall exists here
                            bestcase_t1 = min(bestcase_t1, t1)
                            break

            dist = math.sqrt(abs(self.x + dx * bestcase_t1 - self.x) ** 2 + abs(self.y + dy * bestcase_t1 - self.y)**2)  # Distance from the player to the wall

            try:
                wall_h = grid.w / dist * ((screen.w / 2) / math.tan(math.radians(self.ray_cnt / 2))) * .5
                wall_h = min(wall_h, wall_limit)
            except ZeroDivisionError:
                wall_h = wall_limit  # Case where we directly touching front of wall

            diagnol = math.sqrt(grid.width ** 2 + grid.height ** 2)
            # color = 255 - (diagnol - dist) / diagnol * 255
            # color = min(int((diagnol - dist) / diagnol * 255), 254)
            if p.torchBool: color = min(dist*2.5, 255)
            else: color = min(dist*4.5, 255)
            # print(color, dist, diagnol)

            hitX = self.x + dx * bestcase_t1
            hitY = self.y + dy * bestcase_t1
            if grid.grid[int(hitY // grid.w)][int(hitX // grid.w)] == 2: gameDisplay.blit(pygame.transform.scale(door, (int(wall_jump), int(wall_h))), (wall_x - wall_jump / 2, wall_y - wall_h / 2))
            else: gameDisplay.blit(pygame.transform.scale(wallImg, (int(wall_jump), int(wall_h))), (wall_x - wall_jump / 2, wall_y - wall_h / 2))

            # pygame.draw.rect(screen.screen, (color, color, color), (wall_x - wall_jump / 2, wall_y - wall_h / 2, wall_jump, wall_h))
            # gameDisplay.blit(pygame.transform.scale(door, (int(wall_jump), int(wall_h))), (wall_x - wall_jump / 2, wall_y - wall_h / 2))
            # print(color)
            # pygame.draw.rect(screen.screen, (100,100,100, 100), (wall_x - wall_jump / 2, wall_y - wall_h / 2, wall_jump, wall_h))
            # pygame.draw.aaline(screen.screen, (200,200,150), (self.x, self.y),
            #                     (self.x + dx * bestcase_t1, self.y + dy * bestcase_t1))

            # For Alpha shading
            rect = pygame.Surface((wall_jump, wall_h), pygame.SRCALPHA, 32)
            if self.walking: rect.fill((0, 0, 0, color))
            else: rect.fill((0, 0, 0, 255))
            screen.screen.blit(rect, (wall_x - wall_jump / 2, wall_y - wall_h / 2))



            temp_agl += self.ray_gap
            wall_x += wall_jump


class Ghost():
    def __init__(self, idx_x, idx_y, sound):
        self.idx_x = idx_x
        self.idx_y = idx_y
        self.scream = sound

    def wander(self, gridW, gridH, grid):
        while True:
            dx = random.randrange(-1, 2)
            dy = random.randrange(-1, 2)
            idx_x = dx + self.idx_x
            idx_y = dy + self.idx_y
            idx_x = min(max(0, idx_x), gridW)
            idx_y = min(max(0, idx_y), gridH)
            if grid[idx_y][idx_x] == 0:
                self.idx_x = idx_x
                self.idx_y = idx_y
                return

    def playScream(self):
        self.scream.play()

class Grid():
    def __init__(self, grid, w):
        self.grid = grid
        self.w = w
        self.width = len(grid[0]) * w
        self.height = len(grid) * w

    def draw(self, screen):
        y_pos = 0
        for y in range(len(self.grid)):
            x_pos = 0
            for x in range(len(self.grid[0])):
                sqr = self.grid[y][x]
                if sqr:
                    pygame.draw.rect(screen, (150, 150, 150), (x_pos, y_pos, self.w, self.w))
                x_pos += self.w
            y_pos += self.w

    def collision_detect(self, x, y, d_x, d_y):
        # NOTE THAT PREV AND NEW X ARE INDEXES ON THE GRID AND NOT THE COORDINATES OF VARIABLES X AND Y
        new_x = int((x + d_x) // self.w)
        new_y = int((y + d_y) // self.w)
        prev_x = int(x // self.w)
        prev_y = int(y // self.w)
        x_flag, y_flag = True, True  # True = No collision | False = Collision
        if self.grid[new_y][prev_x]:
            # Collision with wall (y component)
            if new_y > prev_y:
                y_flag = False
                y = new_y * self.w - 0.0001 # Needs to be slightly adjusted due to errors raised using "//" or integer division
            elif prev_y > new_y:
                y_flag = False
                y = prev_y * self.w

        if self.grid[prev_y][new_x]:
            # Collision with wall (x component)
            if new_x > prev_x:
                x_flag = False
                x = new_x * self.w - 0.0001  # Needs to be slightly adjusted due to errors raised using "//" or integer division
            elif prev_x > new_x:
                x_flag = False
                x = prev_x * self.w

        if x_flag: x += d_x
        if y_flag: y += d_y

        if not x_flag or not y_flag:
            # Check to see if we have collected a totem (Totem disappears if we do)
            if self.grid[new_y][new_x] == 2:
                p.collectCnt += 1
                self.grid[new_y][new_x] = 0

        return x, y  # Sends it either adjusted or the same

    def findOpening(self):
        while True:
            i = random.randrange(1, len(self.grid) - 1)
            j = random.randrange(1, len(self.grid[0]) - 1)
            if self.grid[i][j] == 0:
                return [j, i]

    def ghostCollide(self, px, py, ghosts):
        idx_x = px // self.w
        idx_y = py // self.w
        for ghost in ghosts:
           if ghost.idx_x == idx_x and ghost.idx_y == idx_y:
               if p.torchBool:
                    # Killed and now takes a new position
                    print("killed")
                    pIdxX = int(p.x // grid.w)
                    pIdxY = int(p.y // grid.w)
                    grid.grid[pIdxY][pIdxX] = 1
                    g.idx_x, g.idx_y = self.findOpening()
                    grid.grid[pIdxY][pIdxX] = 0
               else:
                   print("dead")


    def placeTotems(self):
        placed = 0
        while placed < 3:
            i = random.randrange(1, len(self.grid) - 1)
            j = random.randrange(1, len(self.grid[0]) - 1)
            if self.grid[i][j] == 1:
                self.grid[i][j] = 2
                placed += 1

def shortestDist(start, end, grid):
    map = copy.deepcopy(grid)
    dist = 0
    q = deque([start])
    while True:
        for i in range(len(q)):
            x, y = q.popleft()
            map[y][x] = 1
            if [x, y] == end: return dist
            if map[y][x + 1] == 0:
                q.append([x + 1, y])
            if map[y][x - 1] == 0:
                q.append([x - 1, y])
            if map[y + 1][x] == 0:
                q.append([x, y + 1])
            if map[y - 1][x] == 0:
                q.append([x, y - 1])
        dist += 1

pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

screen = Window(1000, 700)
map = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1], [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1], [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1], [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1], [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1], [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1], [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1], [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], [1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1], [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
sx, sy = 0, 5

gameDisplay = pygame.display.set_mode((screen.w, screen.h))
door = pygame.image.load('Images/door-clipart-004.png')
wallImg = pygame.image.load("Images/platformPack_tile034p.png")
torch = pygame.image.load('Images/flail_goldp.png')

pygame.font.init() # you have to call this at the start,
myfont = pygame.font.SysFont('Comic Sans MS', 30)

grid = Grid(map, 32)
grid.placeTotems()

footStepRun = pygame.mixer.Sound("Sounds/footstep04.ogg")
footStepWalk = pygame.mixer.Sound("Sounds/footstep00.ogg")

sx, sy = grid.findOpening()
p = Player(sx * grid.w + grid.w / 2, sy * grid.w + grid.w / 2, 9, 9, 60, 1, 0.4, 100)

ghosts = []
screams = [pygame.mixer.Sound("Sounds/AAAGH1.wav"), pygame.mixer.Sound("Sounds/nmh_scream1.wav"), pygame.mixer.Sound("Sounds/woscream4.wav")]
for i in range(3):
    idx_x, idx_y = grid.findOpening()
    if [idx_x, idx_y] != [sx, sy]:
        g = Ghost(idx_x, idx_y, screams[i])
        ghosts.append(g)

mx, my = 2000,1050
frame_cnt = 0
timeLeft = 300
while True:
    screen.update()
    screen.fill()
    # grid.draw(screen.screen)
    p.update(grid, mx, my) # Collision detection between player and walls
    # We have just checked for wall collision. Now we check for collisions with ghosts
    grid.ghostCollide(p.x, p.y, ghosts)

    # p.draw(screen.screen)
    p.ray_cast(grid, screen)
    frame_cnt += 1

    if frame_cnt % 15 == 0:
        p.stamina = min(0.01 * p.max_stamina + p.stamina, p.max_stamina)
    p.drawStamina(screen.screen)

    if p.walking:
        pygame.draw.rect(screen.screen, (255, 100, 150), (400, 50, p.torchFuel * 2,50))  # Draw torch fuel
    else:
        p.drawHearingBar(screen.screen)

    if frame_cnt % 60 == 0: timeLeft -= 1
    textsurface = myfont.render('Time left = ' + str(timeLeft), False, (200, 200, 200))
    screen.screen.blit(textsurface, (700, 50))

    if frame_cnt % 200 == 0:
        for ghost in ghosts:
            ghost.wander(len(grid.grid[0]), len(grid.grid), grid.grid)

    # Check inputs
    # print("working")
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if p.walking:
                    if not p.torchBool:
                        p.torchBool = True
                    else: p.torchBool = False
                elif p.hearingFuel > 0:
                    for g in ghosts:
                        pIdxX = int(p.x // grid.w)
                        pIdxY = int(p.y // grid.w)
                        dist = shortestDist([pIdxX, pIdxY], [g.idx_x, g.idx_y],grid.grid)
                        g.scream.set_volume(max(0.1, (10 - dist)/10))
                        print(max(0.01, (10 - dist)/10))
                        time.sleep(0.2)
                        g.playScream()

            if event.key == pygame.K_r:
                p.torchBool = False
                p.walking = not p.walking

    p.torchUpdate()
    p.hearingUpdate()
    if p.torchBool: p.torchDraw(screen.screen)

    if timeLeft == 0:
        print("You Lose")
        sys.exit()

    pygame.display.update()
    clock.tick(61)  # Fps (Don't know why/how it does it)
