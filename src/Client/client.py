from tkinter import *
import socket, pickle, time, json
import threading
import ctypes, sys
import tkinter.ttk as ttk

from PacketStructure import *
from PacketOpcode import *
from PongGame import *
import Constants as const

HOST = '127.0.0.1'
PORT = 50008
MAX_WIDTH = 800
MAX_HEIGHT = 400

global app
global Mysocket
Mysocket = None
global login_windows
LOCK = threading.Lock()
class PongGameClient():
	def __init__(self, packet):
		camp = packet['content']['camp']
		max_score = packet['content']['max_score']
		self.PongGame = PongGameWindows(camp, max_score)
		self.ball_is_send = False
		self.recvT = threading.Thread (target=Mysocket.recv_loop_thread)
		self.recvT.start()
	def main_loop(self):
		i = 0
		while True:
			for event in pygame.event.get():
				if event.type == QUIT:
					self.game_exit()
				if (event.type == pygame.KEYDOWN):
					if (event.key == pygame.K_SPACE):
						if not self.PongGame.getReady():
							self.PongGame.setReady(True)
							self.send_on_ready()
			while self.PongGame.getGameRun():
				camp = self.PongGame.getCamp()
				for event in pygame.event.get():
					if event.type == QUIT:
						self.game_exit()
					elif event.type == KEYDOWN:
						if event.key == K_UP:
							self.PongGame.setPaddleDirection(camp, -1)
						elif event.key == K_DOWN:
							self.PongGame.setPaddleDirection(camp, 1)
					elif event.type == KEYUP: 
						if event.key == K_UP and self.PongGame.getPaddleDirection(camp) == -1:
							self.PongGame.setPaddleDirection(camp, 0)
						elif event.key == K_DOWN and self.PongGame.getPaddleDirection(camp) == 1:
							self.PongGame.setPaddleDirection(camp, 0)
				i = i % 3
				if i == 0:
					self.send_paddle_rect()
				i += 1
				self.check()
				self.PongGame.game.update()
				pygame.display.update()
				self.PongGame.fps_clock.tick(30)

			if self.PongGame.getReady():
				self.PongGame.showOnReadyScreen()
			else:
				self.PongGame.showNotReadyScreen()

			if self.PongGame.getGameOver():
				self.PongGame.showGameOverScreen()

			pygame.display.update()
			self.PongGame.fps_clock.tick(30)
	def game_exit(self):
		app.now_frame.now_game = None
		app.now_frame.start_game_flag = False
		self.send_exit_game(self.PongGame.getGameOver())
		self.PongGame.exit()
	def send_paddle_rect(self):
		camp = self.PongGame.getCamp()
		if(self.PongGame.getPaddleDirection(camp) != 0):
			rect = self.PongGame.getBaddleRect(camp)
			packet = PacketStructure(Mysocket.socket_id).getPacket()
			packet['action'] = PacketOpcode.PONG_GAME_PADDLE_RECT.value
			packet['content'] = {}
			packet['content']['rect'] = rect
			packet['content']['camp'] = camp
			Mysocket.udp_send(packet)
	def send_on_ready(self):
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_ON_READY.value
		packet['content'] = {}
		packet['content']['camp'] = self.PongGame.getCamp()
		Mysocket.send(packet)
	def game_start(self, packet):
		self.PongGame.setGameRun(True)
		self.PongGame.game.countdown_start(3)
	def update_paddles(self, packet):
		camp = packet['content']['camp']
		rect = packet['content']['rect']
		self.PongGame.updatePaddles(camp, rect)
	def send_hit_wall(self, hit_camp):
		self.ball_is_send = True
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_HIT_WALL.value
		packet['content'] = {}
		packet['content']['hit_camp'] = hit_camp
		if self.PongGame.getCamp() == hit_camp and self.ball_is_send:
			Mysocket.send(packet)
	def update_score(self, packet):
		score = packet['content']['score']
		self.PongGame.updateScore(score)
		if(packet['content']['ball_type'] == 'ball'):
			self.PongGame.setBallInit()
			self.PongGame.setRedBallInit()
			self.ball_is_send = False
			self.PongGame.game.countdown_start(3)
	def check(self):
		hit_ball = self.PongGame.game.check_ball_hit_wall()
		if hit_ball == self.PongGame.getCamp():
			self.send_hit_wall(hit_ball)
			self.PongGame.setBallInit()
			self.PongGame.setRedBallInit()
			self.send_ball_info('ball')
			self.send_ball_info('red_ball')
		hit_red_ball = self.PongGame.CheckRedBallHitBaddle(self.PongGame.getCamp())
		if hit_red_ball:
			self.send_ball_info('red_ball')
			self.send_hit_red_ball()
		# red_ball_hit_wall = self.PongGame.game.check_red_ball_hit_wall()
		# if red_ball_hit_wall == self.PongGame.getCamp():
		# 	self.send_ball_info('red_ball')
		
		hit_paddle = self.PongGame.CheckHitBaddle(self.PongGame.getCamp())
		if hit_paddle:
			self.send_ball_info('ball')
	def send_winner(self, winner_camp):
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_WINNER.value
		packet['content'] = {}
		packet['content']['camp'] = winner_camp
		Mysocket.send(packet)
	def send_exit_game(self, game_over_flag):
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_EXIT.value
		packet['content'] = {}
		packet['content']['camp'] = self.PongGame.getCamp()
		packet['content']['game_over_flag'] = game_over_flag
		Mysocket.send(packet)
	def handle_user_exit(self, packet): #處理從伺服器送來的封包-對手離開
		self.PongGame.setGameRun(False)
		self.PongGame.setGameOver(True)
		self.PongGame.setOpponent_is_exit(True)
		self.send_winner(self.PongGame.getCamp())
	def send_ball_info(self, ball_type):
		ball_info = self.PongGame.getBallInfo(ball_type) 
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_HIT_PADDLES.value
		packet['content'] = {}
		packet['content']['ball'] = ball_info
		packet['content']['ball_type'] = ball_type
		Mysocket.send(packet)
	def update_ball(self, packet):
		ball_info = packet['content']['ball']
		ball_type = packet['content']['ball_type']
		self.PongGame.setBallInfo(ball_type, ball_info)
	def send_hit_red_ball(self):
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_HIT_RED_BALL.value
		packet['content'] = {}
		packet['content']['camp'] = self.PongGame.getCamp()
		Mysocket.send(packet)
	def update_level(self, packet):
		level = packet['content']['level']
		self.PongGame.setLevel(level)
		self.PongGame.setGameRun(False)
		self.PongGame.setReady(False)
		self.send_ball_info('ball')
		self.send_ball_info('red_ball')
	def game_over(self, packet):
		winner_camp = packet['content']['winner_camp']
		self.PongGame.game_over(winner_camp)
		

class TClient:
	def __init__(self):
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.connect(HOST, PORT)
		recvT = threading.Thread (target=self.recv_loop_thread)
		recvT.start()
		self.socket_id = None
		self.uid = None
		self.name = None
	def recv_loop_thread(self):
		while True:
			try:
				packet = self.recv(1024)
				if not packet: break
				self.handlerPacket(packet)
			except socket.error:
				print("error")

	def connect(self, address, port_number):
		while True:
			try:
				print("Connecting to the server...");
				# Connection time out 10 seconds
				# self.client_socket.settimeout(10)
				self.client_socket.connect((address, int(port_number)));

				return True;
			except:
				ctypes.windll.user32.MessageBoxW(0, "主機端無法連線", "連線錯誤", 0)
				exit();
		return False;

	def send(self, packet):
		try:
			self.client_socket.send(pickle.dumps(packet))
		except:
			self.__connection_lost(self)

	def recv(self, size):
		try:
			packet = pickle.loads(self.client_socket.recv(size))
			return packet
		except:
			self.__connection_lost()
		# except Exception as e:
		# 	print(e)
		return None
	def udp_send(self, packet):
		self.udp_server.sendto(pickle.dumps(packet), (HOST, int(PORT)))
	def __connection_lost(self):
		print("Error: connection lost.")
		try:
			# ctypes.windll.user32.MessageBoxW(0, "主機端無法連線", "連線錯誤", 0)
			app.client_exit()
		except:
			pass
		raise Exception

	def close(self):	
		self.client_socket.close()
	def handlerPacket(self, packet):
		try:
			action = packet['action']
			{
				PacketOpcode.PUBLIC_CHAT_MESSAGE.value : lambda: app.now_frame.chat_insrt_line(packet),
				PacketOpcode.PONG_GAME_OPEN.value : lambda: app.now_frame.open_pong_game(packet),
				PacketOpcode.PONG_GAME_UPDATE_PADDLES.value : lambda: app.now_frame.now_game.update_paddles(packet),
				PacketOpcode.PONG_GAME_UPDATE_SCORE.value : lambda: app.now_frame.now_game.update_score(packet),
				PacketOpcode.PONG_GAME_EXIT.value : lambda: app.now_frame.now_game.handle_user_exit(packet),
				PacketOpcode.DO_LOGIN_RESULT.value : lambda: app.now_frame.doLogin(packet),
				PacketOpcode.DO_REGISTER_RESULT.value : lambda: app.now_frame.register_result(packet),
				PacketOpcode.INIT_SOCKET_ID.value : lambda: Mysocket.init_socket_id(packet),
				PacketOpcode.PONG_GAME_UPDATE_BALL_INFO.value : lambda: app.now_frame.now_game.update_ball(packet),
				PacketOpcode.PONG_GAME_START.value : lambda: app.now_frame.now_game.game_start(packet),
				PacketOpcode.PONG_GAME_NEW_LEVEL.value : lambda: app.now_frame.now_game.update_level(packet),
				PacketOpcode.PONG_GAME_GAME_OVER.value : lambda: app.now_frame.now_game.game_over(packet),
				PacketOpcode.GET_GAME_RANK_RESULT.value : lambda: app.now_frame.handle_game_rank(packet)

			}.get(action, lambda: print('Error'))()
		except Exception as e:
			print(e)
	def init_socket_id(self, packet):
		self.socket_id = packet['socket_id']
		
class Myapp(Tk):
	def __init__(self):
		Tk.__init__(self)
		self.frames = {}
		self.resizable(0, 0)
		self.protocol("WM_DELETE_WINDOW", self.client_exit)
		container = Frame(self)
		container.pack(side="top", fill="both", expand=True)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)
		self.now_frame = None
		for F in (ConnectWindows, LoginWindwos, RegisterWindwos, MainWindows):
			page_name = F.__name__
			frame = F(parent=container, controller=self)
			self.frames[page_name] = frame

			frame.grid(row=0, column=0, sticky="nsew")

		self.show_frame("ConnectWindows")

	def show_frame(self, page_name):
		frame = self.frames[page_name]
		self.now_frame = frame
		frame.init_windows()
		frame.tkraise()
	def client_exit(self):
		if Mysocket != None:
			Mysocket.close()
		self.quit()
		exit(1)

class ConnectWindows(Frame):
	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.controller = controller
		self.ip = StringVar()
		self.ip.set(HOST)
		self.port = StringVar()
		self.port.set(PORT)
	def init_windows(self):
		self.changeWindows()
		Forms = Frame(self, width=300, height=450)
		Forms.pack(side=TOP)
		txt_IP = Label(Forms, text="IP:", font=('arial', 16), bd=15)
		txt_IP.grid(row=0, stick="e")
		txt_port = Label(Forms, text="Port:", font=('arial', 16), bd=15)
		txt_port.grid(row=1, stick="e")
		ip_input = Entry(Forms, textvariable=self.ip, width=20)
		ip_input.grid(row=0, column=1)
		port_input = Entry(Forms, textvariable=self.port, width=20)
		port_input.grid(row=1, column=1)
		Buttons = Button(self, width=20, text="連線", command=self.connect)
		Buttons.pack(side=BOTTOM)
	def connect(self):
		global HOST
		global PORT
		HOST = str(self.ip.get())
		PORT = int(self.port.get())
		connect_to_server()
		self.controller.show_frame("LoginWindwos")
		# self.controller.show_frame("MainWindows")
	def changeWindows(self):
		self.controller.title('連線設定')
		screen_width = self.controller.winfo_screenwidth()
		screen_height = self.controller.winfo_screenheight()
		x = (screen_width/2) - (MAX_WIDTH/2)
		y = (screen_height/2) - (MAX_HEIGHT/2)
		self.controller.geometry('%dx%d+%d+%d' % (300, 150, x, y))

class LoginWindwos(Frame):
	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.controller = controller
		self.account = StringVar()
		self.passwd = StringVar()
	def init_windows(self):
		self.changeWindows()
		Forms = Frame(self, width=300, height=450)
		Forms.pack(side=TOP)
		txt_account = Label(Forms, text="帳號:", font=('arial', 16), bd=15)
		txt_account.grid(row=0, stick="e")
		txt_passwd = Label(Forms, text="密碼:", font=('arial', 16), bd=15)
		txt_passwd.grid(row=1, stick="e")
		account_input = Entry(Forms, textvariable=self.account, width=20)
		account_input.grid(row=0, column=1)
		passwd_input = Entry(Forms, textvariable=self.passwd, width=20, show="*")
		passwd_input.grid(row=1, column=1)

		Buttons = Frame(self, width=300, height=100, bd=1, relief="raise")
		Buttons.pack(side=BOTTOM)
		btn_login = Button(Buttons, width=20, text="登入", command=self.send_do_login_request)
		btn_login.pack(side=LEFT)
		btn_register = Button(Buttons, width=20, text="註冊", command=lambda: self.controller.show_frame("RegisterWindwos"))
		btn_register.pack(side=LEFT)
	def send_do_login_request(self):
		check = self.check()
		if check:
			packet = PacketStructure(Mysocket.socket_id).getPacket()
			packet['action'] = PacketOpcode.DO_LOGIN.value
			packet['content'] = {}
			packet['content']['account'] = self.account.get().lower()
			packet['content']['passwd'] = self.passwd.get()
			Mysocket.send(packet)
	def check(self):
		if self.account.get() == "" or self.passwd.get() == "":
			ctypes.windll.user32.MessageBoxW(0, "請輸入帳號密碼", "登入錯誤", 0)
			return False
		return True
	def doLogin(self, packet):
		status = packet['content']['status']
		if(status == 'success'):
			Mysocket.uid = packet['content']['uid']
			Mysocket.name = packet['content']['name']
			self.controller.show_frame("MainWindows")
		else:
			ctypes.windll.user32.MessageBoxW(0, packet['content']['msg'], "登入錯誤", 0)
	def changeWindows(self):
		self.controller.title('登入')
		screen_width = self.controller.winfo_screenwidth()
		screen_height = self.controller.winfo_screenheight()
		x = (screen_width/2) - (MAX_WIDTH/2)
		y = (screen_height/2) - (MAX_HEIGHT/2)
		self.controller.geometry('%dx%d+%d+%d' % (300, 150, x, y))
class RegisterWindwos(Frame):
	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.controller = controller
		self.account = StringVar()
		self.passwd = StringVar()
		self.passwd2 = StringVar()
		self.username = StringVar()
		self.sex = StringVar()
		self.sex.set('M')
	def init_windows(self):
		self.changeWindows()
		Forms = Frame(self, width=300, height=100)
		Forms.pack(side=TOP)
		txt_account = Label(Forms, text="帳號:", font=('arial', 16), bd=15)
		txt_account.grid(row=0, stick="e")
		txt_passwd = Label(Forms, text="密碼:", font=('arial', 16), bd=15)
		txt_passwd.grid(row=1, stick="e")
		txt_passwd2 = Label(Forms, text="確認密碼:", font=('arial', 16), bd=15)
		txt_passwd2.grid(row=2, stick="e")
		txt_username = Label(Forms, text="暱稱:", font=('arial', 16), bd=15)
		txt_username.grid(row=3, stick="e")
		txt_sex = Label(Forms, text="性別:", font=('arial', 16), bd=15)
		txt_sex.grid(row=4, stick="e")
		account_input = Entry(Forms, textvariable=self.account, width=20)
		account_input.grid(row=0, column=1)
		passwd_input = Entry(Forms, textvariable=self.passwd, width=20, show="*")
		passwd_input.grid(row=1, column=1)
		passwd2_input = Entry(Forms, textvariable=self.passwd2, width=20, show="*")
		passwd2_input.grid(row=2, column=1)
		username_input = Entry(Forms, textvariable=self.username, width=20)
		username_input.grid(row=3, column=1)
		RadioGroup = Frame(Forms)
		Male = Radiobutton(RadioGroup, text="男", variable=self.sex, value="M", font=('arial', 16)).pack(side=LEFT)
		Female = Radiobutton(RadioGroup, text="女", variable=self.sex, value="F", font=('arial', 16)).pack(side=LEFT)
		RadioGroup.grid(row=4, column=1)
		Buttons = Frame(self, width=300, height=100, bd=1, relief="raise")
		Buttons.pack(side=BOTTOM)
		btn_login = Button(Buttons, width=15, text="註冊", command=self.send_do_register_request)
		btn_login.pack(side=LEFT)
		btn_reset = Button(Buttons, width=15, text="清除", command=self.do_reset)
		btn_reset.pack(side=LEFT)
		btn_back = Button(Buttons, width=15, text="返回登入", command=lambda:self.controller.show_frame("LoginWindwos"))
		btn_back.pack(side=LEFT)
	def send_do_register_request(self):
		status = self.check()
		if(status):
			packet = PacketStructure().getPacket()
			packet['action'] = PacketOpcode.DO_REGISTER.value
			packet['content'] = {}
			packet['content']['account'] = self.account.get().lower()
			packet['content']['passwd'] = self.passwd.get()
			packet['content']['name'] = self.username.get()
			packet['content']['sex'] = self.sex.get()
			Mysocket.send(packet)
	def do_reset(self):
		self.account.set('')
		self.passwd.set('')
		self.passwd2.set('')
		self.username.set('')
		self.sex.set('M')
	def check(self):
		if (self.account.get() == "" or self.passwd.get() == "" or self.passwd2.get() == "" or self.username.get() == ""):
			ctypes.windll.user32.MessageBoxW(0, "請填滿空格", "註冊錯誤", 0)
			return False
		elif self.passwd.get() != self.passwd2.get():
			ctypes.windll.user32.MessageBoxW(0, "您輸入的兩次密碼不一樣", "註冊錯誤", 0)
			return False
		return True
	def register_result(self, packet):
		status = packet['content']['status']
		msg = packet['content']['msg']
		if(status == 'fail'):
			ctypes.windll.user32.MessageBoxW(0, msg, "註冊錯誤", 0)
		else:
			ctypes.windll.user32.MessageBoxW(0, msg, "註冊成功", 0)
			self.controller.show_frame("LoginWindwos")
	def changeWindows(self):
		self.controller.title('註冊')
		screen_width = self.controller.winfo_screenwidth()
		screen_height = self.controller.winfo_screenheight()
		x = (screen_width/2) - (MAX_WIDTH/2)
		y = (screen_height/2) - (MAX_HEIGHT/2)
		self.controller.geometry('%dx%d+%d+%d' % (380, 320, x, y))

class MainWindows(Frame):
	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.controller = controller
		self.wait_game_flag = False
		self.start_game_flag = False
		self.wait_windows = None
		self.now_game = None
	def init_windows(self):
		self.changeWindows()
		self.socket = Mysocket
		menu = Menu(self.controller)
		self.controller.config(menu = menu)

		game = Menu(menu, tearoff=0)
		game.add_command(label = '乒乓球', command = self.wait_pong_game)
		menu.add_cascade(label = 'Game' , menu = game)

		rank = Menu(menu, tearoff=0)
		rank.add_command(label = '乒乓球', command = lambda:self.send_game_rank_request(const.PONG_GAME))
		menu.add_cascade(label = 'Rank', menu = rank)

		file = Menu(menu, tearoff=0)
		file.add_command(label = '離開', command = self.controller.client_exit)
		menu.add_cascade(label = 'File', menu = file)

		self._create_chat_textarea()
	def handle_game_rank(self, packet):
		data = packet['content']
		RankWindow(Toplevel(self.controller), data)
	def send_game_rank_request(self, game_type):
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.GET_GAME_RANK.value
		packet['content'] = {
			'game_type': game_type,
			'uid': Mysocket.uid	
		}
		Mysocket.send(packet)

	def _create_chat_textarea(self):
		Top = Frame(self, width=MAX_WIDTH, height=50, bd=1, relief="raise")
		Top.pack(side=TOP)
		chat_area = Text(Top, height=27, width=110)
		scroll = Scrollbar(Top, command=chat_area.yview)
		chat_area.configure(yscrollcommand=scroll.set)
		chat_area.config(state=DISABLED)
		chat_area.pack(side=LEFT)
		scroll.pack(side=RIGHT, fill=Y)

		Bottom = Frame(self, width=MAX_WIDTH, height=50, bd=1, relief="raise")
		Bottom.pack(side=TOP)
		chat_str = StringVar()
		chat_input = Entry(Bottom, textvariable = chat_str, width=100)
		chat_input.pack(side=LEFT)
		
		btn_chat_submit = Button(Bottom, width=20, text="送出", command = lambda:self.chat_submit(chat_str))
		btn_chat_submit.pack(side=RIGHT)
		self.chat_area = chat_area
	def wait_pong_game(self):
		if(self.wait_game_flag == False):
			self.wait_game_flag = True
			# self.wait_windows = WaitWindow()
			self.wait_windows = WaitWindow(Toplevel(self.controller))
			packet = PacketStructure().getPacket()
			packet['action'] = PacketOpcode.PONG_GAME_WAIT.value
			self.socket.send(packet)
			self.wait_windows.master.mainloop()
	def chat_submit(self, text):
		content = text.get()
		if content != '':
			text.set('')
			packet = PacketStructure().getPacket()
			packet['from'] = self.socket.name
			packet['action'] = PacketOpcode.PUBLIC_CHAT_MESSAGE.value
			packet['content'] = content
			self.socket.send(packet)
	def chat_insrt_line(self, packet):
		msg_from = packet['from']
		msg = packet['content']
		text = msg_from + ":" + msg
		self.chat_area.config(state=NORMAL)
		self.chat_area.insert(END, text + "\n")
		self.chat_area.config(state=DISABLED)
	def open_pong_game(self, packet):
		self.wait_windows.start_game()
		self.wait_windows = None
		self.start_game_flag = True
		self.now_game = PongGameClient(packet)
		self.now_game.main_loop()
	def changeWindows(self):
		self.controller.title('final')
		screen_width = self.controller.winfo_screenwidth()
		screen_height = self.controller.winfo_screenheight()
		x = (screen_width/2) - (MAX_WIDTH/2)
		y = (screen_height/2) - (MAX_HEIGHT/2) - 50
		self.controller.geometry('%dx%d+%d+%d' % (MAX_WIDTH, MAX_HEIGHT, x, y))
class WaitWindow():
	def __init__(self, master):
		self.master = master
		self.frame = Frame(self.master)
		screen_width = self.master.winfo_screenwidth()
		screen_height = self.master.winfo_screenheight()
		x = (screen_width/2) - (MAX_WIDTH/2)
		y = (screen_height/2) - (MAX_HEIGHT/2)
		self.master.geometry('%dx%d+%d+%d' % (150, 100, x, y))
		self.master.title("遊戲等待...")
		self.master.resizable(0, 0)
		self.master.protocol("WM_DELETE_WINDOW", self.cancel_wait)
		self.init_window()
	def init_window(self):
		time_label = Label(self.master, text = '排隊中....')
		time_label.pack()
		self.time_label = time_label
		button = Button(self.master, text="取消", command = self.cancel_wait)
		button.pack()  # 顯示元件
	def update_clock(self):
		now = time.strftime("%H:%M:%S")
		self.time_label.configure(text=now)
		self.master.after(1000, self.update_clock)
	def cancel_wait(self):
		packet = PacketStructure(Mysocket.socket_id).getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_CANCEL_WAIT.value
		Mysocket.send(packet)
		app.now_frame.wait_game_flag = False
		self.master.destroy()
	def start_game(self):
		app.now_frame.wait_game_flag = False
		self.master.destroy()

class RankWindow():
	def __init__(self, master, data = None):
		self.master = master
		self.frame = Frame(self.master)
		screen_width = self.master.winfo_screenwidth()
		screen_height = self.master.winfo_screenheight()
		x = (screen_width/2) - (MAX_WIDTH/2)
		y = (screen_height/2) - (MAX_HEIGHT/2)
		self.master.geometry('%dx%d+%d+%d' % (400, 400, x, y))
		self.master.title("排行榜")
		self.master.resizable(0, 0)
		self.frame.pack()
		self.data = data
		self.init_window()
		self.ReadRank()
	def init_window(self):
		label_f = Frame(self.frame, width=600, height=100, bd=1, relief="raise")
		label_f.pack(side=TOP)
		if self.data['my'] != None:
			my_txt = "你目前排名在第" + str(self.data['my']['rank']) + "名，勝場:" + str(self.data['my']['win_count']) + "，敗場:" + str(self.data['my']['lost_count'])
		else:
			my_txt = "你目前沒有在排行榜上"
		my_rank = Label(label_f, width=900, font=('arial', 16), text = my_txt)
		my_rank.pack()
		Top = Frame(self.frame, width=600, height=500, bd=1, relief="raise")
		Top.pack(side=TOP)
		scrollbary = Scrollbar(Top, orient=VERTICAL)
		scrollbarx = Scrollbar(Top, orient=HORIZONTAL)
		tree = ttk.Treeview(Top, columns=("rank", "UserName", "win_count", "lost_count"), selectmode="extended", height=500, yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)
		scrollbary.config(command=tree.yview)
		scrollbary.pack(side=RIGHT, fill=Y)
		scrollbarx.config(command=tree.xview)
		scrollbarx.pack(side=BOTTOM, fill=X)
		tree.heading('rank', text="名次", anchor=W)
		tree.heading('UserName', text="玩家名稱", anchor=W)
		tree.heading('win_count', text="勝場", anchor=W)
		tree.heading('lost_count', text="敗場", anchor=W)
		tree.column('#0', stretch=NO, minwidth=0, width=0)
		tree.column('#1', stretch=NO, minwidth=0, width=50)
		tree.column('#2', stretch=NO, minwidth=0, width=150)
		tree.column('#3', stretch=NO, minwidth=0, width=100)
		tree.column('#4', stretch=NO, minwidth=0, width=100)
		tree.pack()
		self.tree = tree
	def ReadRank(self):
		rank = self.data['rank']
		self.tree.delete(*self.tree.get_children())
		if len(rank) > 0:
			for r in rank:
				self.tree.insert('', 'end', values=(r["rank"], r["name"], r["win_count"], r["lost_count"]))

def connect_to_server():
	global Mysocket
	Mysocket = TClient()

if __name__ == '__main__':
	global app
	app = Myapp()
	app.mainloop()
	

	
