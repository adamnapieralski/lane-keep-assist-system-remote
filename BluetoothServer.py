import os
import time
from bluetooth import *
import select
import threading
import math
import cv2

from Camera import Camera

# os.system("sudo hciconfig hci0 piscan")
# os.system("sudo sdptool add SP")
#
# server = BluetoothSocket(RFCOMM)
# server.bind(("", PORT_ANY))
# server.listen(1)
#
# port = server.getsockname()[1]
# print(port)
#
# uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
# advertise_service(server, "RaspberryServer", uuid)
# print("Waiting for connection")
# client_sock, client_info = server.accept()
# print("Accepted connection from ", client_info)
#
# try:
# 	while True:
# 		data = client_sock.recv(1024)
# 		if len(data) == 0: break
# 		print("received [%s]" % data)
# except IOError:
# 	pass
#
# print("disconnected")
#
# client_sock.close()
# server.close()
# print("all done")


class BluetoothServer:

	uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

	STATE_CUSTOM_SENDING = 0
	STATE_IMAGE_SENDING = 1

	single_img_byte_packet_size = 400



	def __init__(self):
		os.system("sudo hciconfig hci0 piscan")
		os.system("sudo sdptool add SP")
		self.server = BluetoothSocket(RFCOMM)
		self.server.bind(("", PORT_ANY))
		self.server.listen(1)
		self.port = self.server.getsockname()[1]

		self.client_sock = None
		self.client_info = None
		self.sendFlag = False

		self.receive_thread = None
		self.send_thread = None
		self.camera = None

		self.image = None

		# with open("snap2.png", "rb") as image:
		# 	f = image.read()
		# 	self.byte_image = bytearray(f)


	def wait_for_client(self):
		advertise_service(self.server, "RaspberryServer", service_id=self.uuid)
		print("Waiting for connection")
		self.client_sock, self.client_info = self.server.accept()
		print("Accepted connection from: ", self.client_info)
		return True

	def get_client_socket(self):
		return self.client_sock

	def initialize_communication_threads(self):
		self.receive_thread = self.ReceiveThread(self)
		# self.send_thread = self.SendThread(self)

	def start_communication_threads(self):
		self.receive_thread.start()
		# self.send_thread.start()

	def send(self, obj, state):
		if state == self.STATE_CUSTOM_SENDING:
			self.client_sock.send(obj)

		elif state == self.STATE_IMAGE_SENDING:
			print("sending length", str(len(obj)))
			time.sleep(0.1)
			self.client_sock.send(" ")
			self.client_sock.send(str(len(obj)))
			time.sleep(0.1)
			print("sent")
			print("range", math.ceil(len(obj) / self.single_img_byte_packet_size))
			for i in range(math.ceil(len(obj) / self.single_img_byte_packet_size)):
				print("sending part", i)
				self.client_sock.send(bytes(obj[i * self.single_img_byte_packet_size : (i+1) * self.single_img_byte_packet_size]))
			time.sleep(0.1)

	def set_camera(self, camera):
		self.camera = camera

	def set_image(self, image):
		self.image = image

	def get_image_bytes(self):
		return bytearray(cv2.imencode(".png", self.image)[1])

	class ReceiveThread(threading.Thread):
		receive_decoding = 'utf-8'

		def __init__(self, bluetooth_server):
			threading.Thread.__init__(self)
			# threading.Thread.setDaemon(self, True)
			self.bluetooth_server = bluetooth_server
			self.socket = bluetooth_server.client_sock

		def run(self):
			try:
				while True:
					data = self.socket.recv(1024)
					if len(data) == 0:
						break
					data = data.decode(self.receive_decoding)
					vals = data.split(" ")
					print(vals)
					if vals[0] == "save_settings":
						self.bluetooth_server.camera.set_perspective_src_points_from_str(vals[1:])
					elif vals[0] == "open_settings":
						self.bluetooth_server.send(self.bluetooth_server.get_image_bytes(), BluetoothServer.STATE_IMAGE_SENDING)
						self.bluetooth_server.send("settings " + self.bluetooth_server.camera.get_perspective_src_points_to_str(),
											   		BluetoothServer.STATE_CUSTOM_SENDING)

			except IOError:
				pass

	class SendThread(threading.Thread):
		def __init__(self, bluetooth_server):
			threading.Thread.__init__(self)
			# threading.Thread.setDaemon(self, True)
			self.socket = bluetooth_server.client_sock

		def run(self):
			i = 1
			while True:
				# time.sleep(5)
				# self.socket.send(str(len(b)))
				# for i in range(math.ceil(len(b) / single_img_byte_packet_size)):
				#     self.socket.send(bytes(b[i * single_img_byte_packet_size : (i+1) * single_img_byte_packet_size]))
				#     print("Sending ", i)

				self.socket.send(str(i))
				i += 1
				time.sleep(5)