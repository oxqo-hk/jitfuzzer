#!/usr/bin/python
#tester.py
import logging
logger = logging.getLogger('debugger')
logger.setLevel(logging.INFO)
logging.basicConfig(filename='example.log',level=logging.DEBUG)

handler = logging.StreamHandler()
#formatter = logging.Formatter("%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s", 
#	datefmt='%Y.%m.%d %H:%M:%S')

formatter = logging.Formatter("%(msecs)d - %(name)s (%(lineno)s) - %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info('start')

def mutate_function_test_1():
	import mutator
	m = mutator.Mutator()
	m.mutate_function('samples/test_opt.js')


def debugger_run():
	import debugger
	d = debugger.Debugger('hello', ['hello',])
	d.run()
	print hex(d.get_reg('rip'))
	with open('/proc/%d/maps'%d.pid, 'r') as f:
		print f.read()

def debugger_getmem():
	import debugger
	import re
	d = debugger.Debugger('hello', ['hello',])
	d.run()
	with open('/proc/%d/maps'%d.pid, 'r') as f:
		data = f.read()

	base = int(re.search('([0-9a-f]{4,16})-[0-9a-f]{4,16}.*r-xp.*/hello',
	 data).group(1), 16)

	out = d.get_mem(base+0x63a, 20)
	print out.encode('hex')

def debugger_setmem():
	import debugger
	import re
	d = debugger.Debugger('hello', ['hello',])
	d.run()
	with open('/proc/%d/maps'%d.pid, 'r') as f:
		data = f.read()

	base = int(re.search('([0-9a-f]{4,16})-[0-9a-f]{4,16}.*r-xp.*/hello',
	 data).group(1), 16)

	out = d.get_mem(base+0x63a, 40)
	print out.encode('hex')
	d.set_mem(base+0x645, '\x12\x34\x56\x78\x90\x90\x90\x90\x12\x34')
	out = d.get_mem(base+0x63a, 40)
	print out.encode('hex')

def debugger_break():
	import debugger
	import re
	import time
	import os
	d = debugger.Debugger('hello', ['hello',])
	d.run()
	with open('/proc/%d/maps'%d.pid, 'r') as f:
		data = f.read()

	base = int(re.search('([0-9a-f]{4,16})-[0-9a-f]{4,16}.*r-xp.*/hello',
	 data).group(1), 16)

	out = d.get_mem(base+0x63a, 40)
	print out.encode('hex')
	d.set_break_sw(base+0x63a)
	d.cont()
	_, status = os.waitpid(d.pid, 0)
	if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
		d.break_handler()
	
def debugger_action():
	import debugger
	import re
	import os
	import struct

	def action(dbg):
		dbg.logger.info('this is custom bp handler')
		dbg.logger.info('register:')
		regs = dbg.get_regs()
		for reg, val in regs._fields_:
			print reg, hex(dbg.get_reg(str(reg)))

		dbg.logger.info('stack:')
		stack = dbg.get_mem(int(regs.rsp), 40)
		print stack.encode('hex')
		print len(stack)
		
		for i in range(0, len(stack), 8):
			print '%016x'%(struct.unpack('<Q', stack[i:i+8])[0])


	d = debugger.Debugger('hello', ['hello',])
	d.run()
	with open('/proc/%d/maps'%d.pid, 'r') as f:
		data = f.read()

	base = int(re.search('([0-9a-f]{4,16})-[0-9a-f]{4,16}.*r-xp.*/hello',
	 data).group(1), 16)

	d.set_break_sw(base+0x63a, action = action)
	d.cont()
	_, status = os.waitpid(d.pid, 0)
	if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
		d.break_handler()

def debugger_syscall():
	import debugger
	import os
	d = debugger.Debugger('./mmap', ['mmap', ])
	d.run()
	
	while True:
		d.syscall()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			rax = d.get_reg('orig_rax')
			if rax != 9:
				d.syscall()
				continue
			d.syscall()
			os.waitpid(d.pid, 0)
			rax = d.get_reg('rax')
			rip = d.get_reg('rip')
			logger.info('rax:' + hex(rax) + "  rip:" + hex(rip))
		elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
			break

def debugger_open_hook():
	import debugger
	import os
	d = debugger.Debugger('./mmap', ['mmap', ])
	d.run()
	
	while True:
		d.syscall()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			regs = d.get_regs()
			if regs.orig_rax not in  [2, 257]:
				d.syscall()
				continue
			file_name = d.get_str(regs.rsi)
			d.logger.info('SYS_OPEN, file: ' +  file_name)
			d.logger.info('syscall: ' + hex(regs.orig_rax) + ' rdi: ' + hex(regs.rsi))
			d.syscall()
			_, status = os.waitpid(d.pid, 0)
			fd = d.get_reg('rax')
			d.logger.info('result: %d'%d.get_reg('rax'))
			d.fd[fd] = file_name

			
		elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
			break

	print d.fd

def debugger_syscall_num():
	import debugger
	import os
	d = debugger.Debugger('./hello', ['hello',])
	d.run()

	while True:
		scn=d.syscall_num(1) #syscall write
		if scn==-1:
			break
		d.logger.info('syscall: %d'%scn)
		regs = d.get_regs()
		d.logger.info("write: %s"%d.get_mem(regs.rsi, regs.rdx))
		d.syscall()

		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			d.logger.info("result: %d"%d.get_regs().rax)
			d.cont()

		elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
			break

def debugger_get_optimized_function_name():
	import debugger
	import os
	import time
	import struct
	import copy


	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	d = debugger.Debugger(d8_bin, [d8_bin, d8_path + 'samples/test_opt.js', 
		"--single-threaded"])

	d.run()
	d.trace_child()
	while True:
		d.syscall()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			regs = d.get_regs()
			if regs.orig_rax != 257:
				d.syscall()
				continue

			file_name = d.get_str(regs.rsi)
			d.logger.info('openat: %s'%file_name)
			if 'libv8.so' in file_name.split('/')[-1]:
				d.syscall()
				_, status = os.waitpid(d.pid, 0)
				break

			d.syscall()
			os.waitpid(d.pid, 0)
			regs = d.get_regs()
			d.logger.info('orax:' + hex(regs.orig_rax) + "  rax:" + hex(regs.rax))
		elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
			return

	rax = d.get_regs().rax
	while rax > 1000:
		d.syscall()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			rax = d.get_regs().rax
	
	d.logger.info('rax: %d'%rax)

	while True:
		d.syscall()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			rax = d.get_reg('orig_rax')
			if rax != 9 or d.get_regs().r8 != 4:
				d.syscall()
				continue
			d.syscall()
			os.waitpid(d.pid, 0)
			rax = d.get_reg('rax')
			rip = d.get_reg('rip')
			d.logger.info('mmap libv8.so')
			d.logger.info('rax:' + hex(rax) + "  rip:" + hex(rip))
			break
		elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
			break

	def bp_action_printcode(dbg):
		regs = dbg.get_regs()
		regs_bu = copy.copy(regs)
		info = regs.rdx
		shared_info = struct.unpack('<Q', dbg.get_mem(info + 24, 8))
		getDebugName_ret = libv8_base + 0x241e4e
		getDebugName_start = libv8_base + 0x241cd0
		dbg.set_break_sw(getDebugName_ret)
		regs.rbp = regs_bu.rsp - 1024
		regs.rsp = regs_bu.rsp - 1024
		regs.rsi = info
		regs.rip = getDebugName_start
		dbg.set_regs(regs)
		dbg.cont()

		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			regs = dbg.get_regs()
			mid = struct.unpack('<Q', dbg.get_mem(regs.rax, 8))[0]
			#mid = struct.unpack('<Q', dbg.get_mem(mid, 8))[0]
			dbg.logger.info("optimized func name:" + dbg.get_str(mid))
			dbg.unset_break_sw(getDebugName_ret)
			dbg.set_regs(regs_bu)
			
		dbg.unset_break_sw(regs_bu.rip)
		dbg.step()
		dbg.step()
		dbg.step()
		time.sleep(1)
		dbg.set_break_sw(regs_bu.rip, action=bp_action_printcode) 
		#dbg.cont()


		#d.logger.info("bp!!!! %x"%dbg.get_regs().rip)


	libv8_base = rax + 0x14f6000
	bp_addr = 0x135f904 + libv8_base
	d.logger.info('putting bp in %x'%bp_addr)
	res = d.set_break_sw(bp_addr, action=bp_action_printcode)
	d.logger.info('bp set done')
	d.logger.info('bp is ok?? %x'%(ord(d.get_mem(bp_addr, 1))))
	
	while True:
		d.cont()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			res = d.set_break_sw(bp_addr, action=bp_action_printcode)
			break


	while True:	
		d.cont()
		_, status = os.waitpid(d.pid, 0)
		if os.WIFSTOPPED(status) or os.WSTOPSIG(status):
			d.break_handler()

		elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
			d.logger.info('process end.')
			break

		else:
			d.cont()
	

def debugger_get_optimized_function_name_simpler():
	import debugger
	import struct

	v8_text_offset = 0x14f6000
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	d = debugger.Debugger(d8_bin, [d8_bin, d8_path + 'samples/test_opt.js',
		'--single-threaded'])

	d.run()
	d.trace_child()
	def action_printcode(dbg):
		regs = dbg.get_regs()
		dbg.logger.info('BP!!! %x'%regs.rip)
		st = dbg.lib['libv8.so'] + 0x241cd0 + v8_text_offset
		ed = dbg.lib['libv8.so'] + 0x241e4e + v8_text_offset
		arguments = list()
		arguments.append(('rsi', regs.rdx))
		res = dbg.call_func(st, ed, arguments)

		dbg.logger.info('calling GetDeubgName function')
		dbg.logger.info('result: %x'%res.rax)
		tmp = struct.unpack('<Q', dbg.get_mem(res.rax, 8))[0]
		opted_func_name = dbg.get_str(tmp)
		dbg.logger.info('optimized function name: %s'%opted_func_name)

	if d.break_on_lib({'libv8.so':[(0x2855904, action_printcode)]}) != 0:
		d.logger.error("unable to set bp in lib")

	

	d.logger.info('why does it stop here?? %x'%d.get_regs().rip)
	#d.set_break_sw(d.breakpoints.keys()[0], action=action_printcode)
	while True:
		d.cont()
		if not d.wait_until_break():
			break
		if d.get_regs().rip != d.lib['libv8.so'] + 0x2855905:
			d.logger.error('wrong rip: %x'%d.get_regs().rip)
		else:
			d.break_handler()
	
		
def debugger_get_optimized_function_name_and_size_and_start_position():
	import debugger
	import struct

	v8_text_offset = 0x14f6000
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	d = debugger.Debugger(d8_bin, [d8_bin, d8_path + 'samples/test_opt.js',
		'--single-threaded'])

	d.run()
	d.trace_child()
	def action_printcode(dbg):
		regs = dbg.get_regs()

		dbg.logger.info('\n')
		dbg.logger.info('getting function name')
		dbg.logger.info('calling GetDeubgName function')
		st = dbg.lib['libv8.so'] + 0x241cd0 + v8_text_offset
		ed = dbg.lib['libv8.so'] + 0x241e4e + v8_text_offset
		arguments = list()
		arguments.append(('rsi', regs.rdx))
		res = dbg.call_func(st, ed, arguments)

		dbg.logger.info('result: %x'%res.rax)
		tmp = struct.unpack('<Q', dbg.get_mem(res.rax, 8))[0]
		opted_func_name = dbg.get_str(tmp)
		dbg.logger.info('optimized function name: %s'%opted_func_name)

		dbg.logger.info('\n')
		dbg.logger.info('getting function size')
		dbg.logger.info('calling ExecutableInstructionSize')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6d0
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6ea
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_size = res.rax
		dbg.logger.info('result: %x'%res.rax)
		dbg.logger.info('optimized function size: %x'%opted_func_size)

		dbg.logger.info('\n')
		dbg.logger.info('getting optimized function start position')
		dbg.logger.info('calling InstructionStart')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x72e20
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x72e7b
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_start = res.rax
		dbg.logger.info('result(start addr): %x'%opted_func_start)


	if d.break_on_lib({'libv8.so':[(0x2855904, action_printcode)]}) != 0:
		d.logger.error("unable to set bp in lib")

	

	d.logger.info('why does it stop here?? %x'%d.get_regs().rip)
	#d.set_break_sw(d.breakpoints.keys()[0], action=action_printcode)
	while True:
		d.cont()
		if not d.wait_until_break():
			break
		if d.get_regs().rip != d.lib['libv8.so'] + 0x2855905:
			d.logger.error('wrong rip: %x'%d.get_regs().rip)
		else:
			d.break_handler()
	

def debugger_get_optimized_function_everything():
	import debugger
	import struct
	import time

	v8_text_offset = 0x14f6000
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	d = debugger.Debugger(d8_bin, [d8_bin, d8_path + 'samples/test_opt.js',
		'--single-threaded'])

	deopt_entry_list = []

	d.run()
	d.trace_child()
	def action_printcode(dbg):
		regs = dbg.get_regs()

		dbg.logger.info('\n')
		dbg.logger.info('[getting function name]')
		dbg.logger.info('calling GetDeubgName function')
		st = dbg.lib['libv8.so'] + 0x241cd0 + v8_text_offset
		ed = dbg.lib['libv8.so'] + 0x241e4e + v8_text_offset
		arguments = list()
		arguments.append(('rsi', regs.rdx))
		res = dbg.call_func(st, ed, arguments)

		dbg.logger.info('result: %x'%res.rax)
		tmp = struct.unpack('<Q', dbg.get_mem(res.rax, 8))[0]
		opted_func_name = dbg.get_str(tmp)
		dbg.logger.info('optimized function name: %s'%opted_func_name)

		dbg.logger.info('\n')
		dbg.logger.info('[getting function size]')
		dbg.logger.info('calling ExecutableInstructionSize')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6d0
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6ea
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_size = res.rax
		dbg.logger.info('result: %x'%res.rax)
		dbg.logger.info('optimized function size: %x'%opted_func_size)

		dbg.logger.info('\n')
		dbg.logger.info('[getting optimized function start position]')
		dbg.logger.info('calling InstructionStart')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x72e20
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x72e7b
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_start = res.rax
		dbg.logger.info('result(start addr): %x'%opted_func_start)

		"""
		dbg.logger.info('\n')
		dbg.logger.info('getting disassembly of optimized code')
		print dbg.get_disassembly(opted_func_start, opted_func_size)
		"""

	def action_assemble_deoptimizer(dbg):
		regs = dbg.get_regs()
		logger.info('[got deopt entry: 0x%x]'%regs.rax)
		if regs.rax not in deopt_entry_list:
			deopt_entry_list.append(regs.rax)

		for entry in deopt_entry_list:
			print hex(entry)


	if d.break_on_lib({'libv8.so':[(0x2855904, action_printcode)]}) != 0:
		d.logger.error("unable to set bp in lib")	

	deopt_entry_call_address = d.lib['libv8.so'] + v8_text_offset + 0x101b152
	d.set_break_sw(deopt_entry_call_address, action=action_assemble_deoptimizer)

	
	#d.set_break_sw(d.breakpoints.keys()[0], action=action_printcode)
	while True:
		d.cont()
		res = d.wait_until_break()
		if res == 123:
			continue
		elif res == 11:
			time.sleep(3)
			break

		if d.get_regs().rip -1  not in d.breakpoints.keys():
			d.logger.error('wrong rip: %x'%d.get_regs().rip)
		else:
			d.break_handler()
			



def contoller_io_test():
	#import controller
	import debugger
	import os
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	d = debugger.Debugger(d8_bin, [d8_bin, '--print-code'])
	d.run()
	d.cont()
	d.trace_child()
	d.io.sendline("import('%s/samples/test_opt.js')"%d8_path)
	for i in range(100):
		#d.controller.sendline('console.log("hello")')
		print d.io.recv()


def core_dump():
	import debugger
	import os
	d = debugger.Debugger('./hello', ['hello',])
	d.run()

	regs = d.get_regs()
	regs.rip=0x41414141
	d.set_regs(regs)
	d.cont()

	d.wait_until_break()


def everything():
	import debugger
	import struct
	import time
	import threading
	import os

	v8_text_offset = 0x14f6000
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	d = debugger.Debugger(d8_bin, [d8_bin, d8_path + 'samples/test_opt.js',
		'--single-threaded', '--print-code'])

	deopt_entry_list = []

	d.run()
	d.trace_child()
	def action_printcode(dbg):
		dbg.logger.debug("running print code callback")
		regs = dbg.get_regs()

		dbg.logger.debug("rcx: %x"%regs.rcx)

		dbg.logger.info('\n')
		dbg.logger.info('[getting function name]')
		dbg.logger.info('calling GetDeubgName function')
		st = dbg.lib['libv8.so'] + 0x241cd0 + v8_text_offset
		ed = dbg.lib['libv8.so'] + 0x241e4e + v8_text_offset
		arguments = list()
		arguments.append(('rsi', regs.rdx))
		res = dbg.call_func(st, ed, arguments)

		dbg.logger.info('result: %x'%res.rax)
		tmp = struct.unpack('<Q', dbg.get_mem(res.rax, 8))[0]
		opted_func_name = dbg.get_str(tmp)
		dbg.logger.info('optimized function name: %s\n'%opted_func_name)

		dbg.logger.info('[getting function size]')
		dbg.logger.info('calling ExecutableInstructionSize')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6d0
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6ea
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_size = res.rax
		dbg.logger.info('result: %x'%res.rax)
		dbg.logger.info('optimized function size: %x\n'%opted_func_size)

		dbg.logger.info('[getting optimized function start position]')
		dbg.logger.info('calling InstructionStart')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x72e20
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x72e7b
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_start = res.rax
		dbg.logger.info('result(start addr): %x'%opted_func_start)

		"""
		dbg.logger.info('\n')
		dbg.logger.info('getting disassembly of optimized code')
		print dbg.get_disassembly(opted_func_start, opted_func_size)
		"""

	def action_assemble_deoptimizer(dbg):
		dbg.logger.debug("running deopt_entry callback.")
		return None
		#regs = dbg.get_regs()
		#logger.info('[got deopt entry: 0x%x]'%regs.rax)
		#if regs.rax not in deopt_entry_list:
		#	deopt_entry_list.append(regs.rax)

	def recvout(dbg):
		print dbg
		while True:
			data = dbg.io.recv()
			if 'd8>' in data:
				print "end!!!!!!!!!!!!!!!!!!!!!"


	libv8_break = []
	libv8_break.append((0x2855904, action_printcode))
	libv8_break.append((v8_text_offset + 0x2d5858, action_assemble_deoptimizer))
	if d.break_on_lib({'libv8.so':libv8_break}) != 0:
		d.logger.error("unable to set bp in lib")	

	#deopt_entry_call_address = d.lib['libv8.so'] + v8_text_offset + 0x101b152
	#d.set_break_sw(deopt_entry_call_address, action=action_assemble_deoptimizer)

	t = threading.Thread(target=recvout, args=(d, ))
	t.start()

	#d.set_break_sw(d.breakpoints.keys()[0], action=action_printcode)
	while True:
		d.cont()
		res = d.wait_until_break()
		print "wait result:", res
		if res == 123:
			continue
		elif res == 11:
			d.logger.error('SEGFAULT at: %lx'%d.get_regs().rip)
			d.logger.debug('rcx at sivsegv %lx'%d.get_regs().rcx)
			#os.system('cat /proc/%d/maps'%d.pid)
			break

		elif res == 1:
			d.break_handler()

	d.detach(d.pid)
	t.join()



def disable_deopt():
	import debugger
	import struct
	import time
	import threading
	import os


	def action_log_opted_func_call(dbg):
		if disable_switch:
				dbg.logger.debug('function called %lx'%dbg.get_regs().rip)

	def action_printcode(dbg):
		dbg.logger.debug("running print code callback")
		regs = dbg.get_regs()

		dbg.logger.debug("rcx: %x"%regs.rcx)

		dbg.logger.info('\n')
		dbg.logger.info('[getting function name]')
		dbg.logger.info('calling GetDeubgName function')
		st = dbg.lib['libv8.so'] + 0x241cd0 + v8_text_offset
		ed = dbg.lib['libv8.so'] + 0x241e4e + v8_text_offset
		arguments = list()
		arguments.append(('rsi', regs.rdx))
		res = dbg.call_func(st, ed, arguments)

		dbg.logger.info('result: %x'%res.rax)
		tmp = struct.unpack('<Q', dbg.get_mem(res.rax, 8))[0]
		opted_func_name = dbg.get_str(tmp)
		dbg.logger.info('optimized function name: %s\n'%opted_func_name)

		dbg.logger.info('[getting function size]')
		dbg.logger.info('calling ExecutableInstructionSize')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6d0
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6ea
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_size = res.rax
		dbg.logger.info('result: %x'%res.rax)
		dbg.logger.info('optimized function size: %x\n'%opted_func_size)

		dbg.logger.info('[getting optimized function start position]')
		dbg.logger.info('calling InstructionStart')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x72e20
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x72e7b
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_start = res.rax
		dbg.logger.info('result(start addr): %x'%opted_func_start)

		if opted_func_start not in dbg.breakpoints.keys() and opted_func_name == 'main':
			dbg.set_break_sw(opted_func_start, action=action_log_opted_func_call)


	def action_deopt_disable(dbg):
		dbg.logger.debug('deopt hooked!! skipping deopt')
		disable_switch=True
		rip = dbg.get_regs().rip + 5
		dbg.set_reg('rip', rip)


	def recvout(dbg):
		dbg.logger.debug(dbg.io.recvuntil('d8>'))
		cmd = """import("%ssamples/test_opt.js");"""%d8_path
		dbg.io.sendline(cmd)

		while True:
			data = dbg.io.recv()
			dbg.logger.info(data)
			if 'd8>' in data:
				print "end!!!!!!!!!!!!!!!!!!!!!"
				dbg.io.sendline('')


	disable_switch=False
	v8_text_offset = 0x14f6000
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	argv = list()
	argv.append(d8_bin)
	#argv.append(d8_path + 'samples/add_opt_deopt.js')
	argv.append('--single-threaded')
	argv.append('--print-code')
	argv.append('--allow-natives-syntax')
	d = debugger.Debugger(d8_bin, argv)

	deopt_entry_list = []
	d.run()
	d.trace_child()	

	libv8_break = []
	libv8_break.append((0x2855904, action_printcode))
	libv8_break.append((v8_text_offset + 0x29e85b, action_deopt_disable))
	if d.break_on_lib({'libv8.so':libv8_break}) != 0:
		d.logger.error("unable to set bp in lib")	

	t = threading.Thread(target=recvout, args=(d, ))
	t.start()

	while True:
		d.cont()
		res = d.wait_until_break()
		#print "wait result:", res
		if res == 123:
			continue
		elif res == 11:
			d.logger.error('SEGFAULT at: %lx'%d.get_regs().rip)
			d.logger.debug('rcx at sivsegv %lx'%d.get_regs().rcx)
			#os.system('cat /proc/%d/maps'%d.pid)
			break

		elif res == 1:
			d.break_handler()

	d.detach(d.pid)
	t.join()


disable_switch=False

def segfault_test():
	import debugger
	import struct
	import time
	import threading
	import os


	def action_log_opted_func_call(dbg):
		if disable_switch:
				dbg.logger.debug('function called %lx'%dbg.get_regs().rip)

	def action_printcode_debugname(dbg):
		dbg.logger.info('[getting function name]')
		dbg.logger.info('calling GetDeubgName function')
		mem = struct.unpack('<Q', dbg.get_mem(dbg.get_regs().rbp - 0x178, 8))[0]
		name = dbg.get_str(mem)
		dbg.logger.error(name)
		return name


		"""
		st = dbg.lib['libv8.so'] + 0x241cd0 + v8_text_offset
		ed = dbg.lib['libv8.so'] + 0x241e4e + v8_text_offset
		arguments = list()
		arguments.append(('rsi', regs.rdx))
		res = dbg.call_func(st, ed, arguments)
		dbg.logger.info('result: %x'%res.rax)
		tmp = struct.unpack('<Q', dbg.get_mem(res.rax, 8))[0]
		opted_func_name = dbg.get_str(tmp)
		dbg.logger.info('optimized function name: %s\n'%opted_func_name)
		"""

	def action_printcode(dbg):
		dbg.logger.debug("running print code callback")
		regs = dbg.get_regs()

		dbg.logger.info('[getting function size]')
		dbg.logger.info('calling ExecutableInstructionSize')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6d0
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x6bc6ea
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_size = res.rax
		dbg.logger.info('result: %x'%res.rax)
		dbg.logger.info('optimized function size: %x\n'%opted_func_size)

		dbg.logger.info('[getting optimized function start position]')
		dbg.logger.info('calling InstructionStart')
		st = dbg.lib['libv8.so'] + v8_text_offset + 0x72e20
		ed = dbg.lib['libv8.so'] + v8_text_offset + 0x72e7b
		arguments = list()
		arguments.append(('rdi', dbg.get_regs().rsi))
		res = dbg.call_func(st, ed, arguments)

		opted_func_start = res.rax
		dbg.logger.info('result(start addr): %x'%opted_func_start)

		"""
		get_name_point = dbg.lib['libv8.so'] + 0x135fa1a + v8_text_offset
		dbg.set_break_sw(get_name_point, action=action_printcode_debugname)
		while True:
			dbg.cont()
			res = dbg.wait_until_break()
			if res == 1 and dbg.get_regs().rip -1 == get_name_point:
				opted_func_name = dbg.break_handler()
				break
			elif res == 11:
				d.logger.error('SEGFAULT while handling printcode')
				exit()

			elif res == 123:
				continue
		dbg.unset_break_sw(get_name_point)

		dbg.logger.info('optimized function name: %s\n'%opted_func_name)

		if opted_func_start not in dbg.breakpoints.keys() and opted_func_name == 'main':
			#dbg.set_break_sw(opted_func_start, action=action_log_opted_func_call)
			dbg.logger.error(opted_func_name)
			return True
		"""
		
		return 0


	def action_deopt_disable(dbg):
		dbg.logger.debug('deopt hooked!! skipping deopt')
		disable_switch=True
		rip = dbg.get_regs().rip + 5
		dbg.set_reg('rip', rip)


	def recvout(dbg):
		dbg.logger.debug(dbg.io.recvuntil('d8>'))
		cmd = """import("%ssamples/test_opt.js");"""%d8_path
		dbg.io.sendline(cmd)

		while True:
			data = dbg.io.recv()
			#dbg.logger.info(data)
			if 'd8>' in data:
				print "end!!!!!!!!!!!!!!!!!!!!!"
				dbg.io.sendline('')


	
	v8_text_offset = 0x14f6000
	d8_path = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/"
	d8_bin = "/home/oxqo/research/jsfuzzer/v8/out/x64.debug/d8"
	argv = list()
	argv.append(d8_bin)
	#argv.append(d8_path + 'samples/add_opt_deopt.js')
	argv.append('--single-threaded')
	argv.append('--trace-opt')
	argv.append('--print-code')
	argv.append('--allow-natives-syntax')
	d = debugger.Debugger(d8_bin, argv)

	deopt_entry_list = []
	d.run()
	d.trace_child()	

	libv8_break = []
	libv8_break.append((0x2855904, action_printcode))
	libv8_break.append((0x135fa1a + v8_text_offset, action_printcode_debugname))
	#libv8_break.append((v8_text_offset + 0x29e85b, action_deopt_disable))
	if d.break_on_lib({'libv8.so':libv8_break}) != 0:
		d.logger.error("unable to set bp in lib")	

	t = threading.Thread(target=recvout, args=(d, ))
	t.start()

	while True:
		d.cont()
		res = d.wait_until_break()
		#print "wait result:", res
		if res == 123:
			continue
		elif res == 11:
			d.logger.error('SEGFAULT at: %lx'%d.get_regs().rip)
			#os.system('cat /proc/%d/maps'%d.pid)
			break

		elif res == 1:
			done = d.break_handler()

				

	d.detach(d.pid)
	t.join()

def random_objects():
	import mutator
	m = mutator.Mutator()
	#m.set_target('/home/oxqo/experiment/js_samples/fuzzilli/00057121.js')
	x = m.gen_random_objects(100)
	for line in x:
		print line


def weighted_pick_print():
	import cov_tools

	c = cov_tools.Coverage()
	c.add_cov({1: 2})
	c.add_cov({1: 2})
	c.add_cov({2: 2})
	c.add_cov({3: 2})
	print c.all
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(1)
	c.count_cov(2)
	c.count_cov(2)
	c.count_cov(2)
	c.count_cov(2)
	c.count_cov(2)
	c.count_cov(2)
	c.count_cov(2)
	print c.all
	for i in range(100):
		print c.weighted_pick()





#def mutator_test()




#debugger_get_optimized_function_name()
#mutate_function_test_1()
#debugger_run()
#debugger_setmem()
#debugger_break()
#debugger_action()
#debugger_syscall()
#debugger_open_hook()
#debugger_syscall_num()
#debugger_get_optimized_function_name_simpler()
#debugger_get_optimized_function_name_and_size_and_start_position()
#debugger_get_optimized_function_everything()
#contoller_io_test()
#core_dump()
#controller_io_debugger()
#everything()
#disable_deopt()
#segfault_test()
#mutate_function_test_1()
#random_objects()
wp()