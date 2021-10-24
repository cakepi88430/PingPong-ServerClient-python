import pygame, sys, time
from pygame.locals import *
import threading

# Set up the colours
BLACK = (0,0,0)
WHITE = (255,255,255)
GREEN = (0,255,0)
RED = (255,0,0)
YELLOW = (255,255,0)

window_width = 500
window_height = 350

USER1 = 'user1'
USER2 = 'user2'
BACKGROUNG_SOUND_PATH = 'assets/music/background2.mp3'
GAMEOVER_SOUND_PATH = 'assets/music/gameover.wav'
VICTORY_SOUND_PATH = 'assets/music/victory.wav'
HIT_SOUND = 'assets/music/ball.wav'
global display_surf
MY_FONT = 'assets/font/msjh.ttf'

class PongGame():
    def __init__(self, line_thickness=10, speed=5, camp=None, max_score = None):
        self.line_thickness = line_thickness
        self.speed = speed
        self.score = {USER1: 0, USER2: 0}
        self.countdown = 3
        self.game_over = False
        self.game_run = False
        self.camp = camp
        self.max_score = max_score
        self.ready = False
        self.opponent_is_exit = False
        self.level = 1
        self.winner_camp = None
        ball_x = int(window_width/2 - self.line_thickness/2)
        ball_y = int(window_height/2 - self.line_thickness/2)
        paddle_height = 50
        paddle_width = self.line_thickness
        user1_paddle_x = 5
        user2_paddle_x = window_width - paddle_width - 5
        self.ball = Ball(ball_x,ball_y,self.line_thickness, self.line_thickness,self.speed, YELLOW)
        self.red_ball = Ball(ball_x,ball_y,self.line_thickness, self.line_thickness,self.speed, RED)
        self.paddles = {}
        self.left = user1_paddle_x + paddle_width
        self.right = user2_paddle_x
        self.paddles[USER1] = Paddle(user1_paddle_x, paddle_width, paddle_height)
        self.paddles[USER2] = Paddle(user2_paddle_x, paddle_width, paddle_height)
        self.ball_x = ball_x
        self.ball_y = ball_y
        user1_scoreboard_x = 20
        user1_scoreboard_y = 25
        user2_scoreboard_x = window_width-150
        user2_scoreboard_y = 25
        self.scoreboard = {
            USER1:Scoreboard(0, user1_scoreboard_x, user1_scoreboard_y),
            USER2:Scoreboard(0, user2_scoreboard_x, user2_scoreboard_y)
        }

    def draw_arena(self):
        display_surf.fill((0,0,0))
        pygame.draw.rect(display_surf, WHITE,
                         ((0,0),(window_width,window_height)),
                         self.line_thickness*2)
        pygame.draw.line(display_surf, WHITE,
                         (int(window_width/2),0),
                         (int(window_width/2),window_height),
                         int(self.line_thickness/4))

    def update(self):
        self.ball.move()
        if self.ball.hit_paddle(self.paddles[USER1]):
            self.ball.bounce('x')
        elif self.ball.hit_paddle(self.paddles[USER2]):
            self.ball.bounce('x')
        self.draw_arena()
        self.ball.draw()
        if(self.level == 2):
            self.red_ball.move()
            if self.red_ball.hit_paddle(self.paddles[USER1]):
                self.red_ball.bounce('x')
            elif self.red_ball.hit_paddle(self.paddles[USER2]):
                self.red_ball.bounce('x')
            self.red_ball.draw()
        self.paddles[USER1].draw()
        self.paddles[USER2].draw()
        self.scoreboard[USER1].display(self.score[USER1])
        self.scoreboard[USER2].display(self.score[USER2])
        self.display_countdown()
        
    def check_ball_hit_wall(self):
        hit = self.ball.hit_walls(self.left, self.right)
        if hit:
            return hit
        return False
    def check_red_ball_hit_wall(self):
        hit = self.red_ball.hit_walls(self.left, self.right)
        if hit:
            return hit
        return False
    def countdown_start(self, countdown = None):
        if countdown != None:
            self.countdown = countdown
        if(self.countdown <= 0):
            ball_dir_x = self.ball.getBallInfo()['dir_x'] * -1
            ball_dir_y = self.ball.getBallInfo()['dir_y'] * -1
            self.red_ball.setBallDir(ball_dir_x, ball_dir_y) 
            self.ball.setBallMoveFlag(True)
            self.red_ball.setBallMoveFlag(True)
        else:
            self.ball.setBallMoveFlag(False)
            self.red_ball.setBallMoveFlag(False)
            self.countdown -= 1
            threading.Timer(1.0, self.countdown_start).start()
    def display_countdown(self):
        if self.countdown > 0:
            font = pygame.font.Font(MY_FONT, 24)
            result_surf = font.render('%s' %(self.countdown), True, WHITE)
            rect = result_surf.get_rect()
            rect.topleft = (self.ball_x - 5, self.ball_y)
            display_surf.blit(result_surf, rect)
    def display_leve1_not_ready_screen(self):
        display_surf.fill((0,0,0))
        font = pygame.font.Font(MY_FONT, 18)
        txt0 = "關卡一"
        txt1 = "遊戲規則:請使用鍵盤的'上'與'下'來移動你的盤子"
        txt2 = "將球打到對方陣營，如沒打到球，對方即得一分"
        txt3 = "任一方分數達到" + str(self.max_score[1]) + "分，即可進行下一個關卡"
        txt4 = "現在請按下'空白鍵'來準備開始遊戲"
        if(self.camp == USER1):
            txt5 = "你的陣營在左方"
        else:
            txt5 = "你的陣營在右方"
        txt6 = "注意:如在遊戲中途離開，會給予敗場紀錄"
        text0 = font.render(txt0 , True, (255, 255, 255))
        text1 = font.render(txt1 , True, (255, 255, 255))
        text2 = font.render(txt2 , True, (255, 255, 255))
        text3 = font.render(txt3 , True, (255, 255, 255))
        text4 = font.render(txt4 , True, (255, 255, 255))
        text5 = font.render(txt5 , True, (255, 255, 255))
        text6 = font.render(txt6 , True, (255, 0, 0))
        display_surf.blit(text0, (0, window_height/2 - 25))
        display_surf.blit(text1, (0, window_height/2))
        display_surf.blit(text2, (0, window_height/2 + 25))
        display_surf.blit(text3, (0, window_height/2 + 50))
        display_surf.blit(text4, (0, window_height/2 + 75))
        display_surf.blit(text5, (0, window_height/2 + 100))
        display_surf.blit(text6, (0, window_height/2 + 125))
    def display_leve2_not_ready_screen(self):
        display_surf.fill((0,0,0))
        font = pygame.font.Font(MY_FONT, 18)
        txt0 = "關卡二"
        txt1 = "遊戲規則:與上個關卡一樣"
        txt2 = "多了一顆紅球，打到紅球即可得一分，就算沒打到也沒關係"
        txt3 = "延續上一關的分數，累加到任一方分數達到" + str(self.max_score[2]) + "分，即獲勝"
        txt4 = "現在請按下'空白鍵'來準備開始遊戲"
        if(self.camp == USER1):
            txt5 = "你的陣營在左方"
        else:
            txt5 = "你的陣營在右方"
        txt6 = "注意:如在遊戲中途離開，會給予敗場紀錄"
        text0 = font.render(txt0 , True, (255, 255, 255))
        text1 = font.render(txt1 , True, (255, 255, 255))
        text2 = font.render(txt2 , True, (255, 255, 255))
        text3 = font.render(txt3 , True, (255, 255, 255))
        text4 = font.render(txt4 , True, (255, 255, 255))
        text5 = font.render(txt5 , True, (255, 255, 255))
        text6 = font.render(txt6 , True, (255, 0, 0))
        display_surf.blit(text0, (0, window_height/2 - 25))
        display_surf.blit(text1, (0, window_height/2))
        display_surf.blit(text2, (0, window_height/2 + 25))
        display_surf.blit(text3, (0, window_height/2 + 50))
        display_surf.blit(text4, (0, window_height/2 + 75))
        display_surf.blit(text5, (0, window_height/2 + 100))
        display_surf.blit(text6, (0, window_height/2 + 125))
    def display_on_ready_screen(self):
        display_surf.fill((0,0,0))
        font = pygame.font.Font(MY_FONT, 20)
        txt1 = "等待對手準備.."
        text1 = font.render(txt1 , True, (255, 255, 255))
        display_surf.blit(text1, (0, window_height/2))
    def display_game_over_screen(self):
        display_surf.fill((0,0,0))
        font = pygame.font.Font(MY_FONT, 20)
        txt1 = "遊戲結束"
        text1 = font.render(txt1 , True, (255, 255, 255))
        display_surf.blit(text1, (window_width / 2 - 50, window_height/2))
        if self.opponent_is_exit:
            # gameover_sound = pygame.mixer.Sound(GAMEOVER_SOUND_PATH)
            # pygame.mixer.music.stop()
            # gameover_sound.play(0)
            txt3 = "對方因中途離開"
            txt4 = "系統判定你獲勝!!"
            text3 = font.render(txt3 , True, (255, 255, 255))
            text4 = font.render(txt4 , True, (255, 255, 255))
            display_surf.blit(text3, (window_width / 2 - 50, window_height/2+25))
            display_surf.blit(text4, (window_width / 2 - 50, window_height/2+50))
        else:
            if(self.winner_camp == self.camp):
                txt2 = "你贏了!!!"
            else:
                txt2 = "你輸了!!!"
            text2 = font.render(txt2 , True, (255, 255, 255))
            display_surf.blit(text2, (window_width / 2 - 50, window_height/2+25))
        


class Paddle(pygame.sprite.Sprite):
    def __init__(self,x,w,h):
        self.x = x
        self.w = w
        self.h = h
        self.y = int(window_height / 2 - self.h / 2)
        #Creates Rectangle for paddle.
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.speed = 4
        self.direction = 0
    #Draws the paddle
    def draw(self):
        self.move()
        #Stops paddle moving too low
        if self.rect.bottom > window_height - self.w:
            self.rect.bottom = window_height - self.w
        #Stops paddle moving too high
        elif self.rect.top < self.w:
            self.rect.top = self.w
        #Draws paddle
        pygame.draw.rect(display_surf, GREEN, self.rect)

    #Moves the paddle
    def move(self):
        self.rect.y += self.direction * self.speed

    def update(self, rect):
        self.rect = rect

class Ball(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,speed, color):
        self.init_x = x
        self.init_y = y
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.dir_x = -1  ## -1 = left 1 = right
        self.dir_y = -1 ## -1 = up 1 = down
        self.flag_move = False
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.color = color

    def init_ball_pos(self):
        self.flag_move = False
        self.rect.x = self.init_x
        self.rect.y = self.init_y
    #draws the ball
    def draw(self):
        pygame.draw.rect(display_surf, self.color, self.rect)

    #moves the ball returns new position
    def move(self):
        if self.flag_move:
            self.rect.x += (self.dir_x * self.speed)
            self.rect.y += (self.dir_y * self.speed)

            #Checks for a collision with a wall, and 'bounces' ball off it.
            if self.hit_ceiling() or self.hit_floor():
                self.bounce('y')
            if self.hit_wall():
                self.bounce('x')
    def hit_wall(self):
        if ((self.dir_x == -1 and self.rect.left <= self.w) or
            (self.dir_x == 1 and self.rect.right >= window_width - self.w)):
            return True
        else:
            return False
    def bounce(self,axis):
        if axis == 'x':
            self.dir_x *= -1
        elif axis == 'y':
            self.dir_y *= -1

    def hit_paddle(self,paddle):
        if pygame.sprite.collide_rect(self,paddle):
            hit_sound = pygame.mixer.Sound(HIT_SOUND)
            hit_sound.play()
            return True
        else:
            return False

    def hit_ceiling(self):
        if self.dir_y == -1 and self.rect.top <= self.w:
            hit_sound = pygame.mixer.Sound(HIT_SOUND)
            hit_sound.play()
            return True
        else:
            return False

    def hit_floor(self):
        if self.dir_y == 1 and self.rect.bottom >= window_height - self.w:
            hit_sound = pygame.mixer.Sound(HIT_SOUND)
            hit_sound.play()
            return True
        else:
            return False

    def hit_walls(self, left, right):
        if (self.dir_x == -1 and self.rect.left <= left):
            return USER1
        elif (self.dir_x == 1 and self.rect.right >= right):
            return USER2
        else:
            return False
    def setBallMoveFlag(self, toggle):
        self.flag_move = toggle
    def getBallInfo(self):
        data = {
            "rect":self.rect,
            "dir_x":self.dir_x,
            "dir_y":self.dir_y,
            "flag_move":self.flag_move
        }
        return data
    def setBallInfo(self, data):
        self.rect = data['rect']
        self.dir_x = data['dir_x']
        self.dir_y = data['dir_y']
        self.flag_move = data['flag_move']
    def setBallDir(self, dir_x, dir_y):
        self.dir_x = dir_x
        self.dir_y = dir_y

class Scoreboard():
    def __init__(self,score=0,x=window_width-150,y=25,font_size=20):
        self.score = score
        self.x = x
        self.y = y
        self.font = pygame.font.Font(MY_FONT, 24)

    #Displays the current score on the screen
    def display(self,score):
        self.score = score
        result_surf = self.font.render('Score = %s' %(self.score), True, WHITE)
        rect = result_surf.get_rect()
        rect.topleft = (self.x, self.y)
        display_surf.blit(result_surf, rect)

class PongGameWindows():
    def __init__(self, camp, max_score):
        global display_surf
        display_surf = pygame.display.set_mode((window_width,window_height))
        pygame.init()
        pygame.display.set_caption('Pong')
        pygame.mouse.set_visible(0) # make cursor invisible
        pygame.mixer.music.load(BACKGROUNG_SOUND_PATH)
        pygame.mixer.music.play(-1, 0.0)
        self.fps_clock = pygame.time.Clock()
        self.fps = 40 # Number of frames per second
        self.game = PongGame(speed=4, camp = camp, max_score = max_score)
        self.red_f = False
    def exit(self):
        pygame.quit()
        sys.exit()
    def getCamp(self):
        return self.game.camp
    def updatePaddles(self, camp, rect):
        self.game.paddles[camp].update(rect)
    def setPaddleDirection(self, camp, direction):
        self.game.paddles[camp].direction = direction
    def getPaddleDirection(self, camp):
        return self.game.paddles[camp].direction
    def setGameOver(self, toggle):
        self.game.game_over = toggle
    def getGameOver(self):
        return self.game.game_over
    def setGameRun(self, toggle):
        self.game.game_run = toggle
    def getGameRun(self):
        return self.game.game_run
    def setReady(self, toggle):
        self.game.ready = toggle
    def getReady(self):
        return self.game.ready
    def getBaddleRect(self, camp):
        return self.game.paddles[camp].rect
    def CheckHitBaddle(self, camp):
        return self.game.ball.hit_paddle(self.game.paddles[camp])
    def CheckRedBallHitBaddle(self, camp):
        return self.game.red_ball.hit_paddle(self.game.paddles[camp])
    def getBallInfo(self, ball_type):
        if ball_type == 'ball':
            return self.game.ball.getBallInfo()
        elif ball_type == 'red_ball':
            return self.game.red_ball.getBallInfo()
    def setBallInfo(self, ball_type, data):
        if ball_type == 'ball':
            self.game.ball.setBallInfo(data)
        elif ball_type == 'red_ball':
            self.game.red_ball.setBallInfo(data)
    def showNotReadyScreen(self):
        if self.getLevel() == 1:
            self.game.display_leve1_not_ready_screen()
        elif self.getLevel() == 2:
            self.game.display_leve2_not_ready_screen()
    def showOnReadyScreen(self):
        self.game.display_on_ready_screen()
    def showGameOverScreen(self):
        self.game.display_game_over_screen()
    def setOpponent_is_exit(self, toggle):
        self.game.opponent_is_exit = toggle
    def getLevel(self):
        return int(self.game.level)
    def setLevel(self, level):
        self.game.level = level
    def updateScore(self, score):
        self.game.score = score
    def game_over(self, winner_camp):
        self.setGameRun(False)
        self.setGameOver(True)
        self.game.winner_camp = winner_camp
        if (winner_camp == self.getCamp()):
            gameover_sound = pygame.mixer.Sound(VICTORY_SOUND_PATH)
            pygame.mixer.music.stop()
            gameover_sound.play()
        else:
            gameover_sound = pygame.mixer.Sound(GAMEOVER_SOUND_PATH)
            pygame.mixer.music.stop()
            gameover_sound.play()
    def setBallInit(self):
        self.game.ball.init_ball_pos()
    def setRedBallInit(self):
        self.game.red_ball.init_ball_pos()
                        

#Main function
def main():
    game = PongGameWindows(USER1)

if __name__=='__main__':
    main()
