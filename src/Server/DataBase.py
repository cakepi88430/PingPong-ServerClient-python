import sqlite3
import datetime
class DataBase():
	def __init__(self, db_name = 'db_final.db'):
		self.conn = sqlite3.connect(db_name, check_same_thread=False)
		self.conn.row_factory = self.dict_factory
		self.cursor = self.conn.cursor()
		
		self.init_table()
	def init_table(self):
		self.cursor.execute("CREATE TABLE IF NOT EXISTS `accounts` (uid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, account TEXT NOT NULL, passwd TEXT NOT NULL, sex TEXT NOT NULL, name TEXT NOT NULL, is_login INTEGER NOT NULL DEFAULT 0, register_time DATETIME NOT NULL)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS `game_log` (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, game_type INTEGER NOT NULL, winner_uid INTEGER NOT NULL, loser_uid INTEGER NOT NULL, game_time DATETIME)")

	def close(self):
		self.conn.close()
	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def updateAccount_isLogin(self, uid, is_login):
		self.cursor.execute("UPDATE `accounts` SET `is_login`=? WHERE `uid`=?" , (is_login, uid))
		self.conn.commit()
		if self.cursor.rowcount > 0:
			return True
		else:
			return False
	def setAllUserLogout(self):
		self.cursor.execute("UPDATE `accounts` SET `is_login`=0")
		self.conn.commit()
	def insertAccount(self, data):
		account = data['account']
		passwd = data['passwd']
		sex = data['sex']
		name = data['name']
		register_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		
		self.cursor.execute("INSERT INTO `accounts` (account, passwd, sex, name, register_time) VALUES(?, ?, ?, ?, ?)", (str(account), str(passwd), str(sex), str(name), register_time))
		self.conn.commit()
		uid = self.cursor.lastrowid
		if uid > 0:
			return True
		else:
			return False
		
	def check_has_account(self, account):
		self.cursor.execute("SELECT * FROM `accounts` WHERE `account`=?", (account,))
		result = self.cursor.fetchall()
		if len(result) > 0:
			return True
		else:
			return False

	def getUserInfo_byAccount(self, account):
		self.cursor.execute("SELECT * FROM `accounts` WHERE `account`=?", (account,))
		result = self.cursor.fetchone()
		return result

	def insertGameLog(self, data):
		game_type = data['game_type']
		winner_uid = data['winner_uid']
		loser_uid = data['loser_uid']
		game_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		self.cursor.execute("INSERT INTO `game_log` (game_type, winner_uid, loser_uid, game_time) VALUES(?, ?, ?, ?)", (game_type, winner_uid, loser_uid, game_time))
		self.conn.commit()

	def getGameWinnerLog(self, game_type, uid):
		self.cursor.execute("""SELECT winner_account.name as winner_name, loser_account.name as loser_name
			FROM `game_log`
			INNER JOIN `accounts` as `winner_account`
			ON winner_account.uid = game_log.winner_uid
			INNER JOIN `accounts` as `loser_account`
			ON loser_account.uid = game_log.loser_uid
			WHERE `game_type` = ? AND `winner_uid` = ? """
			, (game_type, uid))

		result = self.cursor.fetchall()
		return result
	def getGameRank(self, game_type):
		self.cursor.execute(
				"""
				SELECT winner.win_count, ifnull(loser.lost_count,'0') as lost_count, accounts.uid, accounts.name, COUNT (winner2.win_count) as rank 
				FROM accounts
				LEFT JOIN (
					SELECT COUNT(winner_uid) AS win_count, winner_uid as uid
					FROM game_log
					WHERE game_type = ?
					GROUP BY game_log.winner_uid 
				) as winner
				ON winner.uid = accounts.uid
				LEFT JOIN (
					SELECT COUNT(winner_uid) AS win_count, winner_uid as uid
					FROM game_log
					WHERE game_type = ?
					GROUP BY game_log.winner_uid 
				) as winner2
				LEFT JOIN (
					SELECT COUNT(loser_uid) AS lost_count, loser_uid as uid
					FROM game_log
					WHERE game_type = ?
					GROUP BY game_log.loser_uid 
				) as loser
				ON accounts.uid = loser.uid
				WHERE ((winner.win_count < winner2.win_count)
					OR (winner.win_count = winner2.win_count AND winner.uid = winner2.uid))
				GROUP BY winner.uid, winner.win_count 
				ORDER BY winner.win_count DESC
				""", (game_type, game_type, game_type,)
			)

		result = self.cursor.fetchall()
		return result
	def getGameRecord(self, game_type, uid):
		self.cursor.execute(
				"""
				SELECT winner.win_count, ifnull(loser.lost_count,'0') as lost_count , accounts.uid, accounts.name, COUNT (winner2.win_count) as rank 
				FROM accounts
				LEFT JOIN (
					SELECT COUNT(winner_uid) AS win_count, winner_uid as uid
					FROM game_log
					WHERE game_type = ?
					GROUP BY game_log.winner_uid 
				) as winner
				ON winner.uid = accounts.uid
				LEFT JOIN (
					SELECT COUNT(winner_uid) AS win_count, winner_uid as uid
					FROM game_log
					WHERE game_type = ?
					GROUP BY game_log.winner_uid 
				) as winner2
				LEFT JOIN (
					SELECT COUNT(loser_uid) AS lost_count, loser_uid as uid
					FROM game_log
					WHERE game_type = ?
					GROUP BY game_log.loser_uid 
				) as loser
				ON accounts.uid = loser.uid
				WHERE ((winner.win_count < winner2.win_count)
					OR (winner.win_count = winner2.win_count AND winner.uid = winner2.uid))
					AND winner.uid = ?
				GROUP BY winner.uid, winner.win_count 
				ORDER BY winner.win_count DESC
				""", (game_type, game_type, game_type, uid,)
			)

		result = self.cursor.fetchone()
		return result