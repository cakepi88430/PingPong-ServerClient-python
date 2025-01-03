﻿from enum import Enum
class PacketOpcode(Enum):
	# def __str__(self):
	# 	return str(self.value)
	PUBLIC_CHAT_MESSAGE = 1
	DO_REGISTER = 2
	DO_REGISTER_RESULT = 3
	DO_LOGIN = 4
	DO_LOGIN_RESULT = 5
	INIT_USER = 6
	PONG_GAME_WAIT = 7
	PONG_GAME_CANCEL_WAIT = 8
	PONG_GAME_OPEN = 9
	PONG_GAME_START = 10
	PONG_GAME_PADDLE_RECT = 11
	PONG_GAME_UPDATE_PADDLES = 12
	PONG_GAME_HIT_WALL = 13
	PONG_GAME_HIT_PADDLES = 14
	PONG_GAME_UPDATE_BALL_INFO = 15
	PONG_GAME_UPDATE_SCORE = 16
	PONG_GAME_WINNER = 17
	PONG_GAME_EXIT = 18
	PONG_GAME_ON_READY = 19
	PONG_GAME_HIT_RED_BALL = 20
	PONG_GAME_NEW_LEVEL = 21
	PONG_GAME_GAME_OVER = 22
	INIT_SOCKET_ID = 23
	GET_GAME_RANK = 24
	GET_GAME_RANK_RESULT = 25
