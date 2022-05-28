import debugger
import mutator
import struct
import time
import threading
import os, sys
import signal
import logging
import re
import mmap
import numpy as np
import random
import shutil
import cov_tools
import json
import hashlib
from collections import OrderedDict
sys.path.insert(0, './coverage_counter/')
from opcode_counter import OPCODE_COUNTER_X64
from opcode_counter import FUNC_START
from d8_debug_configs import *

#DeoptimizeFunction: push rbp 0x2d3ec0
#DeoptimizeFunction:ret 0x2d40c2


disable_switch = False

REX_ADDR = '0x[0-9a-f]{8,16}'
REX_DEOPT_BLOCK_FS = '(' + REX_ADDR + ')' + ':.*\n' + REX_ADDR + ':.*' + 'call.*' + '0x%x'
REX_BRANCH_TO_DEOPT_BLOCK_FS = '('+REX_ADDR+'):\t(j.+)\t' + '(0x%x).*\n' + '('+REX_ADDR+'):'
REX_RET = '('+REX_ADDR+'):\t' + 'ret'
REX_OEP = '(' + REX_ADDR + '):\t' + 'push\trbp'
UNUSED_STACK_JUNK_OFFSET = 0x7000
SEGFUALT_FLAG = '!SEGFAULT!'


p64=lambda x: struct.pack('<Q', x)
p32=lambda x: struct.pack('<L', x)
u64=lambda x: struct.unpack('<Q', x)[0]
u32=lambda x: struct.unpack('<L', x)[0]

def inst_index_for_func_table(inst):
	if inst in ['je', 'jz']:
		return 0
	elif inst in ['jne', 'jnz']:
		return 1
	elif inst in ['js']:
		return 2
	elif inst in ['jns']:
		return 3
	elif inst in ['jg', 'jnle']:
		return 4
	elif inst in ['jge', 'jnl']:
		return 5
	elif inst in ['jle', 'jng']:
		return 6
	elif inst in ['ja', 'jnbe']:
		return 7
	elif inst in ['jae', 'jnb']:
		return 8
	elif inst in ['jb', 'jnae']:
		return 9
	elif inst in ['jbe', 'jna']:
		return 10
	elif inst in ['jo']:
		return 11
	elif inst in ['jp']:
		return 12
	else:
		return None

def opcode_call_rbp_offset(off):
	return '\xff\x95' + struct.pack('<L', (off & 0xffffffff))

def _pass_timeout(a, b):
	pass	

class JitFuzzer:
	def __init__(self,time_start, m, iteration=0, guide_mode=True, disable_deopt=True):
		self.dbg=None
		self.mutator = m
		self.logger = self.set_logger()
		self.cov_table = 0
		self.main_ret = 0
		self.deopt_entry_list = []
		self.coverage = cov_tools.Coverage()
		self.deopt_coverage_ptr = []
		self.func_table_block = ''
		self.func_table_addr = ''
		self.func_table_addr_bu = ''
		self.crash_log = ''
		self.main_start = 0
		self.main_ope = 0
		self.main_size = 0
		self.deopt_count = 0
		self.optimized=False
		self.preparing = False
		self.recvtimeout = False
		self.object_detail = ''
		self.is_muatating = False
		#adding
		self.iter = iteration
		self.guide_mode = guide_mode
		self.new_cov = -1
		self.break_done = False
		self.disable_deopt = disable_deopt
		self.error = False
		self.time_start = time_start

	def set_logger(self):
		logger = logging.getLogger('JitFuzzer')
		
		if len(logger.handlers) > 0:
			return logger 

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

	def action_log_opted_func_called(self):
		#global UNUSED_STACK_JUNK_OFFSET
		regs = self.dbg.get_regs()
		rip_ret = regs.rip
		self.logger.debug('main function called %lx'%regs.rip)
		#self.dbg.print_regs()
		self.func_table_addr = regs.rbp - UNUSED_STACK_JUNK_OFFSET
		self.func_table_addr_bu = self.dbg.get_mem(regs.rbp - UNUSED_STACK_JUNK_OFFSET, len(self.func_table_block))
		self.dbg.set_mem(regs.rbp - UNUSED_STACK_JUNK_OFFSET, self.func_table_block)
		if self.is_muatating:
			self.iter += 1
		self.cleanup_deopt_coverage()
		return rip_ret, None

	def action_printcode_debugname(self):
		self.logger.info('[getting function name]')
		regs = self.dbg.get_regs()
		rip_ret = regs.rip
		mem = struct.unpack('<Q', self.dbg.get_mem(regs.rbp - 0x178, 8))[0]
		name = self.dbg.get_str(mem)
		self.logger.error(name + '\n')
		return rip_ret, name

	def action_printcode(self):
		self.logger.debug("running print code callback")
		regs = self.dbg.get_regs()
		rip_ret = regs.rip
		self.logger.info('[getting function size]')
		self.logger.info('calling ExecutableInstructionSize')
		st = self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_EXECUTABLE_INSTRUCTION_SIZE_START
		ed = self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_EXECUTABLE_INSTRUCTION_SIZE_END
		arguments = list()
		arguments.append(('rdi', self.dbg.get_regs().rsi))
		res = self.dbg.call_func(st, ed, arguments)
		opted_func_size = res.rax
		self.logger.info('result: %x'%res.rax)
		self.logger.info('optimized function size: %x'%opted_func_size)

		self.logger.info('[getting optimized function start position]')
		self.logger.info('calling InstructionStart')
		st = self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_INSTRUCTION_START_START
		ed = self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_INSTRUCTION_START_END
		arguments = list()
		arguments.append(('rdi', self.dbg.get_regs().rsi))
		res = self.dbg.call_func(st, ed, arguments)
		opted_func_start = res.rax
		self.logger.info('result(start addr): %x'%opted_func_start)
		
		return rip_ret, (opted_func_start, opted_func_size)

	def action_assemble_deoptimizer(self):
		regs = self.dbg.get_regs()
		rip_ret = regs.rip
		self.logger.debug('[got deopt entry: 0x%x]'%regs.rax)
		if regs.rax not in self.deopt_entry_list:
			self.deopt_entry_list.append(regs.rax)
		return rip_ret, regs.rax

	def action_deopt_disable(self):
		if not self.optimized:
			return self.dbg.get_regs().rip, None

		self.logger.debug('[FAILED]:deopt hooked!! skipping deopt')

		self.deopt_count += 1
		regs = self.dbg.get_regs()
		rip_ret = regs.rip
		disable_switch=True
		if self.disable_deopt:
			#rip = regs.rip + 5
			rip = self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_DEOPT_RET
			self.dbg.set_reg('rip', rip)
		else:
			self.error=True
		if self.is_muatating:
			log, cov = self.analyze_deopt_coverage()
			self.logger.info(log)

			index = self.coverage.get_index(cov)
			if index != None:
				self.coverage.count_cov(index)
			else:
				self.new_cov = self.coverage.add_cov(cov)

			suc, fail = self.coverage.counter
			self.coverage.counter = (suc, fail+1)
			#self.logger.debug(json.dumps(self.coverage.all, indent=2))
			self.logger.info("explored total: %.4f%%"%(self.coverage.explored_total()*100))
			self.logger.info("path variation: %d"%(len(self.coverage.all)))
			self.logger.info("success: %d, fail: %d"%self.coverage.counter)
			self.logger.info("iteration: %d"%self.iter)

		#self.cleanup_deopt_coverage()
		return rip_ret, None


	def action_opted_func_ret(self):
		self.logger.error('[SUCCESS]:target function returned')
		self.deopt_count += 1
		regs = self.dbg.get_regs()
		rip_ret = regs.rip
		if self.is_muatating:
			log, cov = self.analyze_deopt_coverage()
			self.logger.info(log)

			index = self.coverage.get_index(cov)
			if index != None:
				self.coverage.count_cov(index)
			else:
				self.new_cov = self.coverage.add_cov(cov)

			suc, fail = self.coverage.counter
			self.coverage.counter = (suc+1, fail)
			#self.logger.debug(json.dumps(self.coverage.all, indent=2))
			self.logger.info("explored total: %.4f%%"%(self.coverage.explored_total()*100))
			self.logger.info("path variation: %d"%(len(self.coverage.all)))
			self.logger.info("success: %d, fail: %d"%self.coverage.counter)
			self.logger.info("iteration: %d"%self.iter)
		#self.cleanup_deopt_coverage()
		#data = self.dbg.get_mem(self.cov_table, 0x100)
		#for i in range(0, len(data), 8):
		#	print hex(u64(data[i:i+8]))

		return rip_ret, None

	def cleanup_deopt_coverage(self):
		for _, ptr in self.deopt_coverage_ptr:
			self.dbg.set_mem(ptr, p32(0))

	def interact_single(self, cmd, timeout=None):
		self.dbg.io.sendline(cmd)
		data = self.dbg.io.recvuntil('\nd8>', timeout=timeout)
		if data == '':
			exit()
		return data

	def interact_single_maybe_crash(self, cmd, timeout=None):
		self.dbg.io.sendline(cmd)
		data = self.dbg.io.recvuntil(['\nd8>', '[end of stack trace]'], timeout=timeout)
		#if data == '':
		#	exit()
		if '[end of stack trace]' in data:
				self.crash_log = data
		return data

	def interact_1(self):
		data = self.dbg.io.recvuntil('\nd8>')
		print self.interact_single('load("%sinitial_args.js");'%self.mutator.test_dir)
		self.preparing=False
		with open('%sparam_string.txt'%self.mutator.test_dir, 'r') as f:
			param_string = f.read()
		return param_string

	def interact_2(self, param_string):
		print "interact_2"
		print param_string
		while not self.optimized:
			data = self.interact_single('for(var ii=0;ii<100;ii++){main(%s);}'%\
				param_string, timeout=10)
			print data
			if 'Error' in data:
				self.error = True

		return 'SUCCESS'

		#%OptimizeFunctionOnNextCall(main)

	def interact_3(self, param_string):
		#self.dbg.io.recvuntil('\nd8>')
		print "interact_3"
		data = self.interact_single('print("SyncString");')
		if 'SyncString' not in data:
			self.dbg.io.recvuntil('SyncString')
			self.dbg.io.recvuntil('\nd8>')

		self.is_muatating = True
		print self.interact_single("main(%s);"%param_string)
		iter_tmp = self.iter
		while True:
			if self.guide_mode and (len(self.coverage.all) > 0):
				pool_idx = self.coverage.weighted_pick()
				print "1", "arg_orig = deepClone(args_pool[%d]);"%pool_idx
				self.interact_single_maybe_crash("arg_orig = deepClone(args_pool[%d]);"%pool_idx)
			index = random.choice(range(self.mutator.param_num))
			print self.interact_single_maybe_crash("tmp = deepClone(arg_orig[%d]);"%index)
			print self.interact_single_maybe_crash("tmp=mutate_custom(tmp);")
			print self.interact_single_maybe_crash("arg_array = deepClone(arg_orig);")
			print self.interact_single_maybe_crash("arg_array[%d] = tmp;"%index)
			print self.interact_single_maybe_crash("tmp_array = deepClone(arg_array);")
			self.object_detail = self.interact_single_maybe_crash("JSON.stringify(arg_array);")
			for i in range(self.mutator.param_num):
				print self.interact_single_maybe_crash("arg%d = deepClone(arg_array[%d]);"%(i, i))
			with open(self.mutator.test_dir + 'param_info.txt', 'w') as f:
				f.write(self.object_detail)
			print "2",self.object_detail
			#self.interact_single('%OptimizeFunctionOnNextCall(main);')
			
			result = self.interact_single_maybe_crash('var res = main(%s);'%param_string)

			
			#self.dbg.io.recvuntil('\nd8>')
			if (self.new_cov > -1) and self.guide_mode:
				print self.interact_single_maybe_crash("args_pool[%d] = deepClone(tmp_array);"%self.new_cov)
				self.new_cov = -1
			#self.iter += 1
			if iter_tmp +1 != self.iter:
				self.logger.error('Somehow the function deopted')
				print "result:", result
				print "recv",self.dbg.io.recvuntil('I')
				self.error = True
				return None
			iter_tmp += 1


			time.sleep(0.05)		


	def interact_4(self):
		self.dbg.io.recvuntil('\nd8>')
		if (self.new_cov > -1) and self.guide_mode:
			print "3", "args_pool[%d] = deepClone(tmp_array);"%self.new_cov
			self.interact_single("args_pool[%d] = deepClone(tmp_array);"%self.new_cov)
			self.new_cov = -1
		self.iter += 1
		print "iteration:", self.iter
		time.sleep(0.05)		

	

	def segfault_handler(self):
		self.logger.info('crash at:' + hex(self.dbg.get_regs().rip))
		with open(self.mutator.test_dir + 'rip.txt', 'w') as f:
			f.write( hex(self.dbg.get_regs().rip) + '\n')
		start = time.time()
		while time.time() - start <  10 or self.crash_log != '':
			pass
		with open(self.mutator.test_dir + "crash_log.txt", 'w') as f:
			f.write(self.crash_log)
		self.dbg.detach(self.dbg.pid)
		shutil.copytree(self.mutator.test_dir, RESULT_DIR + hashlib.md5(str(time.time())).hexdigest())


	def wait_and_handle_break(self, timeout=None):
		while True:
			self.dbg.cont()
			if timeout != None:
				signal.signal(signal.SIGALRM, _pass_timeout)
				signal.alarm(timeout)
			try:
				res = self.dbg.wait_until_break()
			except:
				return 0, 'timeout'

			if res == 123:
				print "!!!!!!!!!!!!!!!!!!clone"
				continue

			elif res == 11:
				self.logger.error('SEGFAULT at: %lx'%self.dbg.get_regs().rip)
				#self.segfault_handler()
				return SEGFUALT_FLAG, SEGFUALT_FLAG

			elif res == 1:
				done = self.dbg.break_handler()
				return done

	def tmp_log(self):
		regs = self.dbg.get_regs()
		self.dbg.print_regs()
		return regs.rip, None

	def analyze_deopt_coverage(self):
		log = '[!]runtime-guard coverage info:\n'
		log += 'branch:\t\tHIT (counter_ptr)\n'
		cov = OrderedDict()
		cov_sum = 0
		cov_total = 2*len(self.deopt_coverage_ptr)
		if cov_total == 0:
			self.logger.error('deopt location parse faile:')
			self.logger.error(self.mutator.target)
			return '[!]devide zero return:\n'

		for i, (branch_addr, ptr) in enumerate(self.deopt_coverage_ptr):
			counter = u32(self.dbg.get_mem(ptr, 4))
			log += '0x%x:\t'%branch_addr
			log += '%d (0x%x)\n'%(counter, ptr)
			cov_sum += counter
			cov['branch%03d'%i + ':P'] = int(counter/2)
			cov['branch%03d'%i + ':F'] = counter%2
			

		#log += 'passed/total_check (%%): %.4f%%\n'%\
		#((float(cov_sum)/cov_total)*100)

		return log, cov

	def settings(self):
		argv = list()
		argv.append(D8_BIN)
		argv.append('--single-threaded')
		#argv.append('--trace-opt')
		#argv.append('--trace-deopt')
		argv.append('--print-code')
		argv.append('--allow-natives-syntax')
		#argv.append('2>&1')
		self.preparing=True
		self.dbg = debugger.Debugger(D8_BIN, argv)
		#self.mutator = mutator.Mutator()


	def fuzz_one(self):
		#time_start = time.time()
		self.settings()
		#self.mutator.gen_test_sample()

		self.dbg.run()
		#self.dbg.trace_child()	

		libv8_break = []
		libv8_break.append((V8_TEXT_OFFSET + OFFSET_PRINTCODE, self.action_printcode))
		libv8_break.append((V8_TEXT_OFFSET + OFFSET_PRINTCODE_DEBUGNAME, self.action_printcode_debugname))
		libv8_break.append((V8_TEXT_OFFSET + OFFSET_DEOPT, self.action_deopt_disable))
		libv8_break.append((V8_TEXT_OFFSET + OFFSET_ASSEMBLE_DEOPT, self.action_assemble_deoptimizer))
		if self.dbg.break_on_lib({'libv8.so':libv8_break}) != 0:
			self.logger.error("unable to set bp in lib")	

		self.dbg.disable_break_all()
		self.dbg.cont()

		"""
		self.preparing=True
		t = threading.Thread(target=self.interact, args=())
		t.start()
		"""
		param_string = self.interact_1()
		if param_string == "Error":
			return "ERROR"
		"""
		while self.preparing:
			if self.recvtimeout:
				print "1"
				self.wait_and_handle_break(timeout=1)
				self.recvtimeout = False
				
		"""
		self.dbg.stop()
		res = self.dbg.wait_until_break()
		print res

		self.dbg.enable_break_all()
		self.dbg.disable_break(self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_DEOPT)
		
		print "break_done"
		self.break_done = True
		self.dbg.cont()

		t1 = threading.Thread(target=self.interact_2, args=(param_string, ))
		t1.start()
		#self.interact_2(param_string)

		js_main_addr = 0
		js_main_size = 0
		while True:
			rip, ret = self.wait_and_handle_break(timeout=60)
			if ret == 'timeout':
				return 'TIMEOUT'
			elif self.error:
				return 'ERROR'
			if rip == self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_PRINTCODE:
				mcode_start , mcode_size = ret
		
			elif rip == self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_PRINTCODE_DEBUGNAME:
				mcode_name = ret
				if mcode_name == 'main':
					js_main_addr = mcode_start
					js_main_size = mcode_size
					self.optimized = True
					break

			elif rip == self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_DEOPT:
				pass

			elif rip == self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_ASSEMBLE_DEOPT:
				pass

			elif rip == SEGFUALT_FLAG and ret == SEGFUALT_FLAG:
				self.logger.error('unintended segfault, not handling')
				return "ERROR"



		self.optimized = True
		res = t1.join()
	
		self.dbg.disable_break_all()

		########################parse disassembled js function###############
		asm = self.dbg.get_disassembly(js_main_addr, js_main_size)
		#print asm
		self.logger.info('deopt: %s'%str(self.deopt_entry_list))
		deopt_blocks = list()
		for deopt_entry in self.deopt_entry_list:
			rex = REX_DEOPT_BLOCK_FS%deopt_entry
			deopt_blocks += re.findall(rex, asm)
		deopt_blocks = map((lambda x: int(x, 16)), deopt_blocks)

		print deopt_blocks

		branches_tmp = list()
		branches = dict()
		for deopt_block_addr in deopt_blocks:
			rex = REX_BRANCH_TO_DEOPT_BLOCK_FS%deopt_block_addr
			branches_tmp += re.findall(rex, asm)

		print branches_tmp

		if len(branches_tmp) < 3:
			self.logger.error('branch analysis failed')
			return "ERROR"

		for addr, inst, taken, not_taken in branches_tmp:
			if inst == 'jmp':
				continue
			branches[int(addr, 16)] = inst, int(taken, 16), int(not_taken, 16)
			#sel.dbg.set_break_sw(int(addr, 16), action=self.action_observe_branch)
		branches = OrderedDict(branches)
		
		if len(re.findall(REX_RET, asm)) == 0:
			self.logger.error('exit point not found')
			return "ERROR"
		ret_point = int(re.search(REX_RET, asm).group(1), 16)
		
		#print re.findall(REX_RET, asm)

		###########insert deopt-coverage checking routine into child############

		#map_anon_memories for branch counting
		fake_stack = self.dbg.do_child_mmap(-1, 0x1000, prot=(mmap.PROT_WRITE | mmap.PROT_READ))
		branch_counter_func = self.dbg.do_child_mmap(-1, 0x1000) 
		counters = self.dbg.do_child_mmap(-1, 0x1000, prot=(mmap.PROT_READ | mmap.PROT_WRITE))
		counter_table = self.dbg.do_child_mmap(-1, 0x1000, prot=(mmap.PROT_READ | mmap.PROT_WRITE))

		self.logger.error('fake_stack: ' + hex(fake_stack))
		self.logger.error('fucntions: ' + hex(branch_counter_func))
		self.logger.error('counters: ' + hex(counters))
		self.logger.error('counter_table: ' + hex(counter_table))

		#realloc ptr values
		opcode = OPCODE_COUNTER_X64
		opcode = opcode.replace(p64(0xdeadbeefdeadbeef), p64(fake_stack + 0x800))
		opcode = opcode.replace(p64(0x1234567812345678), p64(counter_table))

		#initialize mapped memory
		self.dbg.set_mem(branch_counter_func, opcode)
		self.dbg.set_mem(counters, '\x00'*0x1000)
		counters_ptr = counters
		table_ptr = counter_table
		for addr in branches.keys():
			inst, taken, not_taken = branches[addr]
			
			self.dbg.set_mem(table_ptr, p64(addr))
			self.dbg.set_mem(table_ptr+0x8, p64(counters_ptr))
			self.dbg.set_mem(table_ptr+0x10, p64(taken))
			self.dbg.set_mem(table_ptr+0x18, p64(not_taken))
			self.deopt_coverage_ptr.append((addr, counters_ptr))
			table_ptr += 0x20
			counters_ptr += 0x4
			
			##################
			if len(self.deopt_coverage_ptr) == 0:
				self.logger.error('cannot find deopt coverage')
				self.logger.error(self.mutator.target)
				self.logger.error(asm)
			###########

			inst_idx = inst_index_for_func_table(inst)
			opcode = opcode_call_rbp_offset(-UNUSED_STACK_JUNK_OFFSET + (inst_idx * 8))
			#hook deopt branch
			self.dbg.set_mem(addr, opcode)
			#self.dbg.set_break_sw(addr, action=tmp_log)

		js_main_oep = int(re.search(REX_OEP, asm).group(1), 16)

		self.func_table_block = ''
		for off in FUNC_START:
			self.func_table_block += p64(branch_counter_func + off)

		self.main_start = js_main_addr
		self.main_ope = js_main_oep
		self.main_size = js_main_size
		self.main_ret = ret_point
		self.cov_table = counters

		
		self.dbg.disable_break_all()

		self.dbg.enable_break(self.dbg.lib['libv8.so'] + V8_TEXT_OFFSET + OFFSET_DEOPT)
		""" Never Do This
		while not self.is_muatating:
			rip, ret = self.wait_and_handle_break()
		"""
		self.dbg.set_break_sw(js_main_oep + 4, action=self.action_log_opted_func_called)
		self.dbg.set_break_sw(ret_point, action=self.action_opted_func_ret)
		

		#self.dbg.set_break_sw(branch_counter_func + 0x594 , action=tmp_log)
		#self.dbg.set_break_sw(branch_counter_func + 0x646, action=tmp_log)


		t = threading.Thread(target=self.interact_3, args=(param_string, ))
		t.start()
		

		self.optimized = True
		while True:
			rip, ret = self.wait_and_handle_break(timeout=60)
			if self.error:
				return "DEOPTIMIZED"

			if rip == SEGFUALT_FLAG and ret == SEGFUALT_FLAG:
				self.logger.info('[!]SEGFAULT!!!!')
				self.segfault_handler()
				return "SEGFAULT"

			if (time.time() - self.time_start) > (2*60):
				return "SUCCESS"

			if ret == 'timeout':
				return 'TIMEOUT_CONTINUABLE'


