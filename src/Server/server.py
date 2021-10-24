#! /usr/bin/python3

# Import the socket module
import socket, pickle
# Import multi-threading module
import threading
# Import the time module
import time
# Import command line arguments
from sys import argv
# Import logging
import logging
from collections import deque
from PacketOpcode import *
from PacketStructure import *
from DataBase import *
import Constants as const
import json

IP = '127.0.0.1'
PORT = 50008
BUFF_SIZE = 1024
global Myserver

# Set up logging to file 
logging.basicConfig(level=logging.DEBUG,
	format='[%(asctime)s] %(levelname)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S',
	filename='server.log')
# Define a Handler which writes INFO messages or higher to the sys.stderr
# This will print all the INFO messages or higer at the same time
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# Add the handler to the root logger
logging.getLogger('').addHandler(console)


class TServer:
	"""TServer deals with networking and communication with the TClient."""
	def __init__(self):
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	def bind(self, port_number):
		while True:
			try:
				self.server_socket.bind(("", int(port_number)))
				self.udp_server.bind(("", int(port_number)))
				logging.info("Reserved port " + str(port_number))
				self.server_socket.listen(1)
				logging.info("Listening to port " + str(port_number))
				break
			except:
				logging.warning("There is an error when trying to bind " + 
					str(port_number))
				# choice = input("[A]bort, [C]hange port, or [R]etry?")
				# if(choice.lower() == "a"):
				# 	exit()
				# elif(choice.lower() == "c"):
				# 	port_number = input("Please enter the port:")

	def close(self):
		self.server_socket.close()

class TServerGame(TServer):

	def __init__(self):
		TServer.__init__(self)
		self.waiting_pong_game_players = deque()
		self.pong_game_room = []
		self.db = DataBase()
		self.setAllUserLogout()
	def setAllUserLogout(self):
		self.db.setAllUserLogout()
	def start(self):
		threading.Thread(target=self.__cliend_upd_thread, args=()).start()
		self.conn_users = []
		self.lock_matching = threading.Lock()
		self.__main_loop()
	def __main_loop(self):
		while True:
			connection, client_address = self.server_socket.accept()
			logging.info("Received connection from " + str(client_address))

			new_user = User(connection)
			packet = PacketStructure(new_user.socket_id).getPacket()
			packet['action'] = PacketOpcode.INIT_SOCKET_ID.value
			new_user.send(packet)
			self.conn_users.append(new_user)

			try:
				threading.Thread(target=self.__client_thread, 
					args=(new_user,)).start()
			except:
				logging.error("Failed to create thread.")

	def __client_thread(self, user):
	
		try:
			while True:
				packet = user.recv(BUFF_SIZE)
				self.handlerPacket(packet, user)
		# except:
		except Exception as e:
			print("User " + str(user.socket_id) + " disconnected.")
			print(e)
		finally:
			self.updateAccountIsLogin(user)
			self.conn_users.remove(user)
			if(user.now_game != None):
				user.now_game._handle_user_exit(user, None)
			if user in self.waiting_pong_game_players:
				self.waiting_pong_game_players.remove(user)
	def __cliend_upd_thread(self):
		try:
			while True:
				packet, addr = self.udp_server.recvfrom(1024)
				packet = pickle.loads(packet)
				self.handlerUdpPacket(packet)
		except Exception as e:
			print(e)
	def send_all_chat(self, packet):
		for user in self.conn_users:
			user.send(packet)
	def handlerUdpPacket(self, packet):
		user = next((user for user in self.conn_users if user.socket_id == packet["socket_id"]))
		self.handlerPacket(packet, user)
	def handlerPacket(self, packet, user):
		action = packet['action']
		{
			PacketOpcode.PUBLIC_CHAT_MESSAGE.value : lambda: self.send_all_chat(packet),
			PacketOpcode.PONG_GAME_WAIT.value : lambda: self.match_pong_game(user),
			PacketOpcode.PONG_GAME_CANCEL_WAIT.value : lambda: self.waiting_pong_game_players.remove(user),
			PacketOpcode.PONG_GAME_PADDLE_RECT.value : lambda: user.now_game._send_update_paddles(user, packet),
			PacketOpcode.PONG_GAME_HIT_WALL.value : lambda: user.now_game._handle_hit_wall(user, packet),
			PacketOpcode.PONG_GAME_WINNER.value : lambda: user.now_game._handle_winner(user, packet),
			PacketOpcode.PONG_GAME_HIT_RED_BALL.value : lambda: user.now_game._handle_hit_red_ball(user, packet),
			PacketOpcode.PONG_GAME_EXIT.value : lambda: user.now_game._handle_user_exit(user, packet),
			PacketOpcode.DO_LOGIN.value : lambda: self.doLogin(user, packet),
			PacketOpcode.DO_REGISTER.value : lambda: self.doRegistered(user, packet),
			PacketOpcode.PONG_GAME_HIT_PADDLES.value : lambda: user.now_game._handle_hit_paddle(user, packet),
			PacketOpcode.PONG_GAME_ON_READY.value : lambda: user.now_game._handle_ready_game(user, packet),
			PacketOpcode.GET_GAME_RANK.value : lambda: self._handle_get_game_rank(user, packet)
		}.get(action, lambda: print('E'))()
	def match_pong_game(self, user):
		self.waiting_pong_game_players.append(user)
		if(len(self.waiting_pong_game_players) >= 2):
			users = []
			users.append(self.waiting_pong_game_players.popleft())
			users.append(self.waiting_pong_game_players.popleft())
			game = PongGameServer(users)
			for tmp_user in users:
				tmp_user.now_game = game
	def updateAccountIsLogin(self, user):
		try:
			self.lock_matching.acquire(True)
			self.db.updateAccount_isLogin(user.uid, 0)
		finally:
			self.lock_matching.release()
				
	def doRegistered(self, user, packet = None):
		account = packet['content']['account']
		new_packet = PacketStructure().getPacket()
		new_packet['action'] = PacketOpcode.DO_REGISTER_RESULT.value
		new_packet['content'] = {}
		check_account = self.db.check_has_account(account)
		data = {
			'account':account,
			'passwd':packet['content']['passwd'],
			'sex':packet['content']['sex'],
			'name':packet['content']['name']
		}

		if check_account:
			new_packet['content']['status'] = 'fail'
			new_packet['content']['msg'] = '此帳號已在此系統上'
		else :
			res = self.db.insertAccount(data)
			new_packet['content']['status'] = 'success'
			new_packet['content']['msg'] = '帳號註冊成功'
		user.send(new_packet)
	def doLogin(self, user, packet):
		account = packet['content']['account']
		passwd = packet['content']['passwd']
		result = self.db.getUserInfo_byAccount(account)
		new_packet = PacketStructure().getPacket()
		new_packet['action'] = PacketOpcode.DO_LOGIN_RESULT.value
		new_packet['content'] = {}
		if(not result) or (passwd != result['passwd']):
			new_packet['content']['status'] = 'fail'
			new_packet['content']['msg'] = '帳號或密碼錯誤'
		else:
			if result['is_login'] == 1:
				new_packet['content']['status'] = 'fail'
				new_packet['content']['msg'] = '此帳號目前連線中...'
			else:
				new_packet['content']['status'] = 'success'
				new_packet['content']['msg'] = '登入成功'
				new_packet['content']['uid'] = result['uid']
				new_packet['content']['name'] = result['name']
				user.uid = result['uid']
				user.name = result['name']
				user.is_login = True
				Myserver.db.updateAccount_isLogin(user.uid, 1)
		user.send(new_packet)
	def _handle_get_game_rank(self, user, packet):
		uid = user.uid
		game_type = int(packet['content']['game_type'])
		my_record = self.db.getGameRecord(game_type, uid)
		rank = self.db.getGameRank(game_type)
		new_packet = PacketStructure().getPacket()
		new_packet['action'] = PacketOpcode.GET_GAME_RANK_RESULT.value
		new_packet['content'] = {}
		new_packet['content']['my'] = my_record
		new_packet['content']['rank'] = rank
		user.send(new_packet)

class PongGameServer:
	def __init__(self, users):
		self.camps = [const.PONG_GAME_USER1, const.PONG_GAME_USER2]
		self.users = users
		self.is_ready_count = 0
		self.score = {const.PONG_GAME_USER1: 0, const.PONG_GAME_USER2: 0}
		self.level = 1
		self.max_level = 2
		self.max_score = {1:5, 2:10}
		self.users_camp = {const.PONG_GAME_USER1:None, const.PONG_GAME_USER2:None}
		self._send_open_packet()
	def _handle_ready_game(self, user, packet):
		self.is_ready_count += 1
		if(self.is_ready_count >= 2):
			self.is_ready_count = 0
			self._send_game_start()
	def _send_game_start(self):
		packet = PacketStructure().getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_START.value
		self.sendPongGameAll(packet)
	def _send_open_packet(self): # send open game packet to user
		for user in self.users:
			camp = self.camps[self.users.index(user)]
			packet = PacketStructure().getPacket()
			packet['action'] = PacketOpcode.PONG_GAME_OPEN.value
			packet['content'] = {}
			packet['content']['camp'] = camp
			packet['content']['max_score'] = self.max_score
			self.users_camp[camp] = user
			user.send(packet)
	def _send_update_paddles(self, user, packet):
		packet['action'] = PacketOpcode.PONG_GAME_UPDATE_PADDLES.value
		for tmp_user in self.users:
			if tmp_user != user:
				tmp_user.send(packet)
	def _handle_hit_wall(self, user, packet):
		hit_wall_camp = packet['content']['hit_camp']
		for camp in self.camps:
			if (hit_wall_camp != camp):
				add_score_camp = camp
				break
		self.updateScore(add_score_camp, 'ball')
	def _handle_winner(self, user, packet): #when have winner, insert game log to database
		for tmp_user in self.users:
			if user != tmp_user:
				loser = tmp_user
		winner = user
		data = {
			"game_type":const.PONG_GAME,
			"winner_uid":winner.uid,
			"loser_uid":loser.uid
		}
		Myserver.db.insertGameLog(data)
	def _handle_user_exit(self, user, packet): #user exit game,init server user status
		user.now_game = None
		game_flag = packet['content']['game_over_flag']
		if not game_flag: # if not game_over, send another user exit the game
			new_packet = PacketStructure().getPacket()
			new_packet['action'] = PacketOpcode.PONG_GAME_EXIT.value
			for tmp_user in self.users:
				if tmp_user != user:
					tmp_user.send(new_packet)
	def _handle_hit_paddle(self, user, packet): # when ball hit the paddle, update ball info
		packet['action'] = PacketOpcode.PONG_GAME_UPDATE_BALL_INFO.value
		for tmp_user in self.users:
			if user != tmp_user:
				tmp_user.send(packet)
	def _handle_hit_red_ball(self, user, packet):
		camp = packet['content']['camp']
		self.updateScore(camp, 'red_ball')
	def updateScore(self, camp, ball_type): # update score and send new score to user
		self.score[camp] += 1
		new_packet = PacketStructure().getPacket()
		new_packet['action'] = PacketOpcode.PONG_GAME_UPDATE_SCORE.value
		new_packet['content'] = {}
		new_packet['content']['score'] = self.score
		new_packet['content']['ball_type'] = ball_type
		self.sendPongGameAll(new_packet)
		self.checkLevel()
	def sendPongGameAll(self, packet): # send this game all user
		for user in self.users:
			user.send(packet)
	def checkLevel(self): # check score has achieve max score to enter next level
		if self.level != self.max_level:
			for camp in self.camps:
				if self.score[camp] >= self.max_score[self.level]:
					self.level += 1
					self._send_new_level()
		else:
			self.checkWinner()
	def _send_new_level(self):
		packet = PacketStructure().getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_NEW_LEVEL.value
		packet['content'] = {}
		packet['content']['level'] = self.level
		self.sendPongGameAll(packet)
	def checkWinner(self):
		if(self.level == self.max_level):
			for camp in self.score:
				if self.score[camp] >= self.max_score[self.level]:
					self._send_game_over(camp)
					self._handle_winner(self.users_camp[camp], None)
	def _send_game_over(self, winner_camp):
		packet = PacketStructure().getPacket()
		packet['action'] = PacketOpcode.PONG_GAME_GAME_OVER.value
		packet['content'] = {}
		packet['content']['winner_camp'] = winner_camp
		self.sendPongGameAll(packet)

class User:
	count = 0

	def __init__(self, connection):
		User.count = User.count + 1
		self.socket_id = User.count
		self.is_login = False
		self.uid = None
		self.name = None
		self.connection = connection
		self.now_game = None

	def send(self, packet):
		try:
			self.connection.send(pickle.dumps(packet))

		except:
			self.__connection_lost()
	def sendAll(self, packet):
		try:
			self.connection.sendall(pickle.dumps(packet))
		except:
			self.__connection_lost()
	def recv(self, size):
		try:
			packet = pickle.loads(self.connection.recv(size))
			return packet
		except:
			self.__connection_lost()
		return None

	def __connection_lost(self):
		logging.warning("user " + str(self.socket_id) + " connection lost.")
		# Raise an error so that the client thread can finish
		raise Exception

def main():
	global Myserver
	try:
		Myserver = TServerGame()
		Myserver.bind(PORT)
		Myserver.start()
		Myserver.close()
	except BaseException as e:
		logging.critical("Server critical failure.\n" + str(e))

if __name__ == "__main__":
	main()
	

