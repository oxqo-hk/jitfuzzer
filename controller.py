import pty
import os
import time
import select
import logging


class Controller:
	def __init__(self,logger=logging, merge_err=True):
		self.merge_err = merge_err
		self.mosi = None
		self.miso = None
		self.mise = None
		self.logger = logger
		self.pty_mosi  = None
		self.pty_miso = None
		self.pty_mese = None

	def new_child(self):
		master_out, slave_in = pty.openpty()
		master_in, slave_out = pty.openpty()
		master_err, slave_err = pty.openpty()

		self.pty_mosi  = (master_out, slave_in)
		self.pty_miso = (master_in, slave_out)
		self.pty_mese = (master_err, slave_err)

		pid = os.fork()
		if pid == 0:
			#child
			if self.merge_err:
				os.dup2(1, 2)
			else:
				os.dup2(slave_err, 2)
			
			os.dup2(slave_in, 0)
			os.dup2(slave_out, 1)
			


			#os.execve(self.executable, self.args, self.env)

		elif pid == -1:
			self.logger.error("Faild to open child")
			return -1

		else:
			#parent
			self.mosi = os.fdopen(master_out, 'w+b')
			self.miso = os.fdopen(master_in, 'r+b')
			self.mise = os.fdopen(master_err, 'r+b')
			
		return pid

	def is_recvable(self, timeout):
		if timeout == None:
			return select.select([self.miso.fileno()], [], [])  == ([self.miso.fileno()], [], [])

		else:
			return select.select([self.miso.fileno()], [], [], timeout) == ([self.miso.fileno()], [], [])


	def is_sendable(self, timeout):
		if timeout == None:
			return select.select([], [self.mosi.fileno()], []) == ([], [self.mosi.fileno()], [])
		elif type(timout) == int or type(timeout) == long:
			return select.select([], [self.mosi.fileno()], [], timeout) == ([], [self.mosi.fileno()], [])
		else:
			self.logger.error('timeout type error')

	def recv(self, size=4096, timeout=None, *args):
		if len(args) > 0:
			size, _ = zip(args)[0]
			if type(size) != int:
				self.logger.error("recv argument error")
				exit()

		if not self.is_recvable(timeout):
			self.logger.error('recv timeout')
			return ''
		return os.read(self.miso.fileno(), size)

	def recvuntil(self, eor, timeout=None):
		tmp = ''
		if type(eor) == str:
			eor = [eor]
		while True:
			res = self.recv(5, timeout=timeout)
			tmp += res
			for el in eor:
				if el in tmp or res == '':
					return tmp

		return tmp

	def recvline(self, timeout=None):
		if not self.is_recvable(timeout):
			self.logger.error('recv timeout')
			return ''

		return self.miso.readline()

	def send(self, data, timeout=None):
		if not self.is_sendable(timeout):
			self.logger.error('send timeout')
			return -1
		return self.mosi.write(data)

	def sendline(self, data, timeout=None):
		if not self.is_sendable(timeout):
			self.logger.error('send timeout')
			return -1
		return self.mosi.write(data + '\n')

	def cleanup(self):
		for master, slave in [self.pty_mosi, self.pty_miso, self.pty_mese]:
			os.close(master)
			os.close(slave)
		return None




