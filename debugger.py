from ctypes import *
from capstone import *
import os
import sys
import logging
import struct
import copy
import controller
import signal
import mmap


"""
/usr/include/x86_64-linux-gnu/sys/ptrace.h
/usr/include/x86_64-linux-gnu/asm/ptrace.h
"""
MEM_SEARCH_SIZE_DEFAULT = 16
MEM_SEARCH_SIZE_QUICK = 4

libc = CDLL('')
ptrace = libc.ptrace

#__ptrace_request
PTRACE_TRACEME = 0
PTRACE_PEEKTEXT = 1
PTRACE_PEEKDATA = 2
PTRACE_PEEKUSER = 3
PTRACE_POKETEXT = 4
PTRACE_POKEDATA = 5
PTRACE_POKEUSER = 6
PTRACE_CONT = 7
PTRACE_KILL = 8
PTRACE_SINGLESTEP = 9
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13
PTRACE_GETFPREGS = 14
PTRACE_SETFPREGS = 15
PTRACE_ATTACH = 16
PTRACE_DETACH = 17
PTRACE_GETFPXREGS = 18
PTRACE_SETFPXREGS = 19
PTRACE_SYSCALL = 24
PTRACE_SYSEMU = 31
PTRACE_SETOPTIONS = 0x4200
PTRACE_GETEVENTMSG = 0x4201
PTRACE_GETSIGINFO = 0x4202
PTRACE_SETSIGINFO = 0x4203

#__ptrace_setoptions
PTRACE_O_TRACESYSGOOD = 0x00000001
PTRACE_O_TRACEFORK = 0x00000002
PTRACE_O_TRACEVFORK = 0x00000004
PTRACE_O_TRACECLONE = 0x00000008
PTRACE_O_TRACEEXEC = 0x00000010
PTRACE_O_TRACEVFORKDONE = 0x00000020
PTRACE_O_TRACEEXIT = 0x00000040
PTRACE_O_MASK = 0x0000007f

#__ptrace_eventcodes
PTRACE_EVENT_FORK=  1
PTRACE_EVENT_VFORK = 2
PTRACE_EVENT_CLONE = 3
PTRACE_EVENT_EXEC = 4
PTRACE_EVENT_VFORK_DONE = 5
PTRACE_EVENT_EXIT = 6

#syscalls
SYS_OPENAT = 257
SYS_MMAP = 9

#OPCODES
OPCODE_SYSCALL = '\x0f\x05'

pointer_of = lambda x: c_void_p(addressof(x))

str_ref = lambda x: x.r15

class user_regs_struct(Structure):
	_fields_ = [
		("r15", c_ulonglong),
		("r14", c_ulonglong),
		("r13", c_ulonglong),
		("r12", c_ulonglong),
		("rbp", c_ulonglong),
		("rbx", c_ulonglong),
		("r11", c_ulonglong),
		("r10", c_ulonglong),
		("r9", c_ulonglong),
		("r8", c_ulonglong),
		("rax", c_ulonglong),
		("rcx", c_ulonglong),
		("rdx", c_ulonglong),
		("rsi", c_ulonglong),
		("rdi", c_ulonglong),
		("orig_rax", c_ulonglong),
		("rip", c_ulonglong),
		("cs", c_ulonglong),
		("eflags", c_ulonglong),
		("rsp", c_ulonglong),
		("ss", c_ulonglong),
		("fs_base", c_ulonglong),
		("gs_base", c_ulonglong),
		("ds", c_ulonglong),
		("es", c_ulonglong),
		("fs", c_ulonglong),
		("gs", c_ulonglong)
	]

	def str_get(self, key):
		ref = {
			"r15" : self.r15,
			"r14" : self.r14,
			"r13" : self.r13,
			"r12" : self.r12,
			"rbp" : self.rbp,
			"rbx" : self.rbx,
			"r11" : self.r11,
			"r10" : self.r10,
			"r9" : self.r9,
			"r8" : self.r8,
			"rax" : self.rax,
			"rcx" : self.rcx,
			"rdx" : self.rdx,
			"rsi" : self.rsi,
			"rdi" : self.rdi,
			"orig_rax" : self.orig_rax,
			"rip" : self.rip,
			"cs" : self.cs,
			"eflags" : self.eflags,
			"rsp": self.rsp,
			"ss" : self.ss,
			"fs_base" : self.fs_base,
			"gs_base" : self.gs_base,
			"ds" : self.ds,
			"es" : self.es,
			"fs" : self.fs,
			"gs" : self.gs
		}
		return ref[key]

	def str_set(self, key, val):
		val = c_ulonglong(val)
		if key == 'r15':
			self.r15=val
		elif key == 'r14':
			self.r14=val
		elif key == 'r13':
			self.r13=val
		elif key == 'r12':
			self.r12=val
		elif key == 'rbp':
			self.rbp=val
		elif key == 'rbx':
			self.rbx=val
		elif key == 'r11':
			self.r11=val
		elif key == 'r10':
			self.r10=val
		elif key == 'r9':
			self.r9=val
		elif key == 'r8':
			self.r8=val
		elif key == 'rax':
			self.rax=val
		elif key == 'rcx':
			self.rcx=val
		elif key == 'rdx':
			self.rdx=val
		elif key == 'rsi':
			self.rsi=val
		elif key == 'rdi':
			self.rdi=val
		elif key == 'orig_rax':
			self.orig_rax=val
		elif key == 'rip':
			self.rip=val
		elif key == 'cs':
			self.cs=val
		elif key == 'eflags':
			self.eflags=val
		elif key == 'rsp':
			self.rsp=val
		elif key == 'ss':
			self.ss=val
		elif key == 'fs_base':
			self.fs_base=val
		elif key == 'gs_base':
			self.gs_base=val
		elif key == 'ds':
			self.ds=val
		elif key == 'es':
			self.es=val
		elif key == 'fs':
			self.fs=val
		elif key == 'gs':
			self.gs=val
		else:
			pass
		"""
		ref = {
			"r15" : self.r15,
			"r14" : self.r14,
			"r13" : self.r13,
			"r12" : self.r12,
			"rbp" : self.rbp,
			"rbx" : self.rbx,
			"r11" : self.r11,
			"r10" : self.r10,
			"r9" : self.r9,
			"r8" : self.r8,
			"rax" : self.rax,
			"rcx" : self.rcx,
			"rdx" : self.rdx,
			"rsi" : self.rsi,
			"rdi" : self.rdi,
			"orig_rax" : self.orig_rax,
			"rip" : self.rip,
			"cs" : self.cs,
			"eflags" : self.eflags,
			"rsp": self.rsp,
			"ss" : self.ss,
			"fs_base" : self.fs_base,
			"gs_base" : self.gs_base,
			"ds" : self.ds,
			"es" : self.es,
			"fs" : self.fs,
			"gs" : self.gs
		}
		ref[key] = val
		"""



"""
long ptrace(enum __ptrace_request request, pid_t pid,
				   void *addr, void *data);
"""

def break_action_default(dbg):
	dbg.logger.info('this bp not being handled. ')
	return None

class Debugger:
	def __init__(self, path, args):
		self.path = path
		self.args = args
		self.pid = None
		self.threads = []
		self.breakpoints={}
		self.logger = self.set_logger()
		self.fd = {}
		self.lib = {}
		self.clone=0
		self.io = controller.Controller(logger=self.logger)
		self.signal_list = [signal.SIGILL, signal.SIGSEGV]
		#signal.SIGABRT, signal.SIGBUS]

	def set_logger(self):
		logger = logging.getLogger('Debugger')
		
		if len(logger.handlers) > 0:
			return logger # Logger already exists
		logger.setLevel(logging.DEBUG)
		logging.basicConfig(filename='example.log',level=logging.DEBUG)
		#logging.basicConfig(level=logging.DEBUG)
		handler = logging.StreamHandler()
		#formatter = logging.Formatter("%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s", 
		#	datefmt='%Y.%m.%d %H:%M:%S')
		formatter = logging.Formatter("%(relativeCreated)d - %(name)s (%(lineno)s) - %(levelname)s: %(message)s")
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		return logger


	def check_pid(self):
		if self.pid == None:
			logging.error("[!]no pid. run or attach first.")
			exit()

		return True

	def stop(self):
		self.check_pid()
		return os.kill(self.pid, signal.SIGTRAP)

	def cont(self):
		self.check_pid()
		return ptrace(PTRACE_CONT, self.pid, None, None)

	def trace_child(self):
		return ptrace( PTRACE_SETOPTIONS, self.pid, None, 
			PTRACE_O_TRACEFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC )

	def step(self):
		self.check_pid()
		return ptrace(PTRACE_SINGLESTEP, self.pid, None, None)

	def run(self):
		self.pid = self.io.new_child() #fork()
		#child
		if not self.pid:
			ptrace(PTRACE_TRACEME, 0, None, None)
			os.execv(self.path, self.args)

		#parent
		else:
			_, status = os.waitpid(self.pid, 0)
			if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
				return 0

			elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
				return 1

			else:
				return -1

	def attach(self, pid):
		res = ptrace(PTRACE_ATTACH, pid, None, None)
		if res == 0:
			self.pid = pid

		else:
			self.logger.error("[!]attach failed. %d: %s"%(res, os.strerror(res)))

		return res

	def detach(self, pid):
		return ptrace(PTRACE_DETACH, pid, None, None)


	def get_regs(self):
		self.check_pid()

		regs = user_regs_struct()
		res = ptrace(PTRACE_GETREGS, self.pid, None, byref(regs))
		if res == 0:
			return regs
		else:
			self.logger.error("[!]failed to get register. %d: %s"
				%(res, os.strerror(res)))
			return res

	def get_reg(self, reg):
		self.check_pid()

		regs = self.get_regs()
		return regs.str_get(reg)

	def get_mem(self, addr, size):
		self.check_pid()
		caddr = c_ulonglong(addr)
		mem = ''
		#can this function check error?? what if WORD[addr] == -1?
		for i in range(int(size/4)+1):
			res = ptrace(PTRACE_PEEKTEXT, self.pid, caddr, None)
			res &= 0xffffffff
			mem += struct.pack('<L', res)
			addr += 4
			caddr = c_ulonglong(addr)

		return mem[:size]

	def set_regs(self, regs):
		self.check_pid()
		res = ptrace(PTRACE_SETREGS, self.pid, None, byref(regs))
		if res != 0:
			self.logger.error("[!]failed to set registers. %d: %s"
				%(res, os.strerror(res)))
		return res

	def set_reg(self, reg, val):
		self.check_pid()
		regs = self.get_regs()
		regs.str_set(reg, val)
		return self.set_regs(regs)

	def set_mem(self, addr, data):
		self.check_pid()
		count = len(data)
		res = 0
		for i in range(int(count/8)):
			caddr = c_ulonglong(addr)
			cdata = c_ulonglong(struct.unpack('<Q', data[:8])[0])
			res = ptrace(PTRACE_POKEDATA, self.pid, caddr, cdata)
			addr += 8
			data = data[8:]


		if count %8 != 0:
			mem = self.get_mem(addr, 8)
			data += mem[len(data):]
			caddr = c_ulonglong(addr)
			cdata = c_ulonglong(struct.unpack('<Q', data[:8])[0])
			res = ptrace(PTRACE_POKEDATA, self.pid, caddr, cdata)

		return res

	def disable_break(self, addr):
		self.check_pid()
		_, opc_org = self.breakpoints[addr]
		return self.set_mem(addr, opc_org)

	def disable_break_all(self):
		self.check_pid()
		for addr in self.breakpoints.keys():
			self.disable_break(addr)
		return 0

	def enable_break(self, addr):
		self.check_pid()
		return self.set_mem(addr, '\xcc')

	def enable_break_all(self):
		self.check_pid()
		for addr in self.breakpoints.keys():
			self.enable_break(addr)
		return 0

	def break_handler(self):
		self.check_pid()
		rip = self.get_reg('rip') - 1
		if rip not in self.breakpoints.keys():
			self.logger.info('This sigstop is not intended maybe??: %x'%rip)
			return None, None
		self.set_reg('rip', rip)
		#self.logger.debug('hit bp at %08x'%rip)

		action, opc_org = self.breakpoints[int(rip)]
		ret = action()
		self.set_mem(rip, opc_org)
		
		self.step()
		_, status = os.waitpid(self.pid, 0)

		self.set_mem(rip, '\xcc')
		return ret

	def set_break_sw(self, addr, action=break_action_default):
		self.check_pid()
		opc_org = self.get_mem(addr, 1)
		if self.set_mem(addr, '\xcc') != 0:
			self.logger.error('[!]failed to set sw breakpoint.')

		self.breakpoints[addr] = action, opc_org

	def unset_break_sw(self, addr):
		self.check_pid()
		_, opc_org = self.breakpoints[addr]
		if self.set_mem(addr, opc_org) != 0:
			self.logger.error('[!]bp unset failed')

		del self.breakpoints[addr]
		self.logger.info('bp unseted')

	def syscall(self):
		self.check_pid()
		return ptrace(PTRACE_SYSCALL, self.pid, None, None);

	def syscall_num(self, arg1):
		if type(arg1 == int):
			sysnum = [arg1]
		elif type(arg1 == list):
			sysnum = arg1
		else:
			self.logger.error('arg type error')
			exit()

		self.check_pid()
		while True:
			self.syscall()
			_, status = os.waitpid(self.pid, 0)
			if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
				scn = self.get_reg('orig_rax')
				if scn in sysnum:
					return scn;
				else:
					continue

			elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
				return -1

	def get_str(self, addr):
		self.check_pid()
		ret = ''
		while True:
			tmp = self.get_mem(addr, MEM_SEARCH_SIZE_QUICK)
			eos = tmp.find('\x00')
			if eos < 0:
				ret += tmp
			else:
				ret += tmp[:eos]
				break
			addr += 4

		return ret

	def clone_breaks(self):
		#there is race issue.. but.. 
		pid_bu = self.pid
		self.pid = self.clone
		for addr in self.breakpoints.keys():
			self.set_mem(addr, '\xcc')
		self.pid = pid_bu
		return 0

	def call_func(self, start, end, arguments):
		self.check_pid()
		self.logger.info('start: %x, end: %x'%(start, end))
		regs = self.get_regs()
		regs_bu = copy.copy(regs)
		#info = regs.rdx
		self.set_break_sw(end)
		regs.rbp = regs_bu.rsp - 1024
		regs.rsp = regs_bu.rsp - 1024
		regs.rip = start
		self.set_regs(regs)
		for name, val in arguments:
			if name in map(lambda (x, y): x, user_regs_struct._fields_):
				self.set_reg(name, val)
			else:
				self.logger.error('currently only regiser arguments are avaliable')

		#wait until end
		#another breaks are gonna be ignored while calling arbitrary function
		while True:
			self.cont()
			w = self.wait_until_break()
			if w and self.get_regs().rip-1 ==end:
				break



		res = self.get_regs()

		self.unset_break_sw(end)
		self.set_regs(regs_bu)
		return res



	def wait_until_break(self):
		self.check_pid()
		evt=c_ulonglong(0)
		test = 0
		evt_p = c_void_p(addressof(evt))
		#print ptrace(PTRACE_GETEVENTMSG, self.pid, None, addressof(evt))
		#print "test", evt_p.value, evt
		while True:
			pid, status = os.waitpid(self.pid, 0x40000000)
			#pid, status = os.waitpid(self.pid, 0)
			ptrace(PTRACE_GETEVENTMSG, self.pid, 0, evt_p)
			if evt.value > 100 and evt.value != self.clone:
				self.clone = evt.value
				self.logger.info('new clone: %d'%self.clone)
				self.threads.append(pid)
				self.step()
				self.clone_breaks()
				#self.pid = self.clone
				#self.cont()
				return 123

			elif os.WIFSTOPPED(status) or os.WSTOPSIG(status):
				if os.WSTOPSIG(status) == signal.SIGTRAP:
					return 1
				elif os.WSTOPSIG(status) in self.signal_list:
					self.logger.error('CRASH!!! %d'%os.WSTOPSIG(status))
					self.logger.error('No handler now..')
					self.logger.error(hex(self.get_regs().rip))
					return 11
				else:
					print "unknown stop signal", os.WSTOPSIG(status)
					return 1

			
			elif os.WIFEXITED(status) or os.WIFSIGNALED(status) or os.WNOHANG(status):
				###exited
				self.logger.error('process %d no longer exists'%(self.pid))
				self.logger.error('exit status: %d singal: %d'%
					(os.WEXITSTATIS(status), os.WTERMSIG(status)))
				if os.WCOREDUMP(status):
					self.logger.error('core dumped')

				self.pid = None
				return -1

			elif  os.WIFCONTINUED(status):
				self.logger.error('process is running')
				continue

			else:
				#unreachable
				self.logger.error('unknown error waiting child')
				return -1

		#unreachable
		return -1

	def break_on_lib(self, lib_breaks):
		self.check_pid()
		while True:
			self.syscall()
			if not self.wait_until_break():
				return -1
			regs = self.get_regs()

			if regs.orig_rax == SYS_OPENAT:
				file_path = self.get_str(regs.rsi)
				file_name = file_path.split('/')[-1]
				self.logger.info('openat: %s'%file_path)
				self.step()
				if not self.wait_until_break():
					return -1
				regs = self.get_regs()
				if regs.rax > 1024:
					self.logger.info('openat failed %x'%regs.rax)
					continue

				self.fd[regs.rax] = file_path

			elif regs.orig_rax == SYS_MMAP:
				map_fd = regs.r8
				if not self.fd.has_key(map_fd):
					self.logger.error('mapping unknown fd %x'%map_fd)
					self.step()
					continue

				file_path = self.fd[map_fd]
				file_name = file_path.split('/')[-1]
				self.step()
				if not self.wait_until_break():
					return -1

				regs = self.get_regs()
				self.logger.info('mapping file [%s] on %x'%(file_path, regs.rax))
				self.lib[file_name] = regs.rax
				if file_name not in lib_breaks.keys():
					continue
				off_list = lib_breaks[file_name]
				for off, act in off_list:
					self.logger.info('setting bp at %x'%(regs.rax + off))
					self.logger.info('mem orig: %s'%(self.get_mem(regs.rax + off, 1).encode('hex')))
					self.set_break_sw(regs.rax + off, action=act)
					self.logger.info(self.get_mem(regs.rax + off, 1).encode('hex'))
				del lib_breaks[file_name]
				if len(lib_breaks) == 0:
					break	

		
		self.logger.info('successfully set all breakpoints in libs')

		return 0

	def _disassemble(self, base, code):
		md = Cs(CS_ARCH_X86, CS_MODE_64)
		ret = ''
		for address, size, mnemonic, op_str in md.disasm_lite(code, base):
			ret += '0x%x:\t%s\t%s\n'%(address, mnemonic, op_str)

		return ret

	def get_disassembly(self, st, size):
		self.check_pid()
		code = self.get_mem(st, size)
		if len(code) < size:
			self.logger.error('something went wrong while getting code memory')

		return self._disassemble(st, code)

	#def call_function(self, start, end)

	def parse_eflags(self, eflags):
		self.check_pid()
		ret = {}
		ret['CF'] = (eflags & (0b1 << 0) > 0)
		ret['PF'] = (eflags & (0b1 << 2) > 0)
		ret['AF'] = (eflags & (0b1 << 4) > 0)
		ret['ZF'] = (eflags & (0b1 << 6) > 0)
		ret['SF'] = (eflags & (0b1 << 7) > 0)
		ret['TF'] = (eflags & (0b1 << 8) > 0)
		ret['IF'] = (eflags & (0b1 << 9) > 0)
		ret['DF'] = (eflags & (0b1 << 10) > 0)
		ret['OF'] = (eflags & (0b1 << 11) > 0)
		ret['NT'] = (eflags & (0b1 << 14) > 0)
		ret['RF'] = (eflags & (0b1 << 16) > 0)
		ret['VM'] = (eflags & (0b1 << 17) > 0)
		ret['AC'] = (eflags & (0b1 << 18) > 0)
		ret['VIF'] = (eflags & (0b1 << 19) > 0)
		ret['VIP'] = (eflags & (0b1 << 20) > 0)
		ret['ID'] = (eflags & (0b1 << 21) > 0)
		return ret

	def get_parsed_eflags(self):
		self.check_pid()
		eflags = self.get_regs().eflags
		return self.parse_eflags(eflags)

	def do_child_mmap(self, addr, length, prot=(mmap.PROT_WRITE | mmap.PROT_READ | mmap.PROT_EXEC), \
		flag=(mmap.MAP_SHARED | mmap.MAP_ANONYMOUS), fd=-1, offset=0):
		self.check_pid()
		regs = self.get_regs()
		regs_bu = copy.copy(regs)
		op_backup = self.get_mem(regs.rip, len(OPCODE_SYSCALL))
		self.set_mem(regs.rip, OPCODE_SYSCALL)
		regs.rax = 9
		regs.rdi = addr
		regs.rsi = length
		regs.rdx = prot
		regs.r10 = flag
		regs.r8 = fd 
		regs.r9 = offset 
		self.set_regs(regs)
		self.step()
		os.waitpid(self.pid, 0x40000000)
		ret = self.get_regs()

		self.set_regs(regs_bu)
		self.set_mem(regs_bu.rip, op_backup)
		return ret.rax

	def print_regs(self):
		regs = self.get_regs()
		self.logger.info('################################')
		self.logger.info("r15: " + hex(regs.r15))
		self.logger.info("r14: " + hex(regs.r14))
		self.logger.info("r13: " + hex(regs.r13))
		self.logger.info("r12: " + hex(regs.r12))
		self.logger.info("rbp: " + hex(regs.rbp))
		self.logger.info("rbx: " + hex(regs.rbx))
		self.logger.info("r11: " + hex(regs.r11))
		self.logger.info("r10: " + hex(regs.r10))
		self.logger.info("r9: " + hex(regs.r9))
		self.logger.info("r8: " + hex(regs.r8))
		self.logger.info("rax: " + hex(regs.rax))
		self.logger.info("rcx: " + hex(regs.rcx))
		self.logger.info("rdx: " + hex(regs.rdx))
		self.logger.info("rsi: " + hex(regs.rsi))
		self.logger.info("rdi: " + hex(regs.rdi))
		self.logger.info("rip: " + hex(regs.rip))
		self.logger.info("rsp: " + hex(regs.rsp))












	







