class PacketStructure:
	def __init__(self, socket_id = None):
		self.packet_arr = {}
		self.packet_arr['socket_id'] = socket_id
		self.packet_arr['from'] = ''
		self.packet_arr['action'] = ''
		self.packet_arr['to'] = ''
		self.packet_arr['content'] = ''
	def getPacket(self):
		return self.packet_arr