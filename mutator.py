#!/usr/bin/python
import re
import os
import random
import logging
import time
import numpy as np
import hashlib

REX_ASSIGN_LET = "let "
REX_ASSIGN_CONST = "const "
REX_ASSIGN_VAR = "var "
REX_ASSIGN = "v[0-9]+ = .*;"
REX_ASSIGN_GROUPS = "(v[0-9]+) = (.*);"
REX_ASSIGN_RECURS = "v[0-9]+ = .*v[0-9]+.*"
REX_VAR = "v[0-9]+"
REX_VAR_GROUP = "(v[0-9]+)"
DIR_ALL_SAMPLE_JS = '/home/oxqo/experiment/js_samples/big_main/'
DIR_TEST_SAMPLE = '/mnt/hgfs/share/jitfuzzer/tests/'
JS_MUTATOR_PATH = "/mnt/hgfs/share/jitfuzzer/js_mutator/"


#getter, setter

class Mutator:
	def __init__(self):
		self.param_num = 0
		self.js_org = ''
		self.js_mut = ''
		self.src_org = list()
		self.line_org = list()
		self.line_mut = list()
		self.target = None
		self.logger = self.set_logger()
		self.arguments_assignment = []
		self.param_string = ''
		self.test_dir = ''

	def set_logger(self):
		logger = logging.getLogger('Mutator')
		
		if len(logger.handlers) > 0:
			return logger # Logger already exists
		logger.setLevel(logging.DEBUG)
		logging.basicConfig(filename='example.log',level=logging.DEBUG)

		handler = logging.StreamHandler()
		#formatter = logging.Formatter("%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s", 
		#	datefmt='%Y.%m.%d %H:%M:%S')
		formatter = logging.Formatter("%(relativeCreated)d - %(name)s (%(lineno)s) - %(levelname)s: %(message)s")
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		return logger

	def set_target(self, js_file):
		#self.param_num = 0
		with open("data/v8_natives", 'r') as f:
			natives = f.read().splitlines()

		with open(js_file, 'r') as f:
			js_org = f.read()

		lines = js_org.splitlines()
		js_mut = js_org

		for line in lines:
			for syntax in natives:
				if syntax in line:
					js_mut = js_mut.replace(line, '')

		self.js_org = js_org
		self.js_mut = js_mut
		self.target = js_file
		#self.src_org = list()
		#self.line_org = list()
		#self.line_mut = list()


	def search_assignments(sel, js_org):
		res = list()
		
		for el in re.findall(REX_ASSIGN_LET + REX_ASSIGN, js_org):
			res.append(el)

		for el in re.findall(REX_ASSIGN_CONST + REX_ASSIGN, js_org):
			res.append(el)

		for el in re.findall(REX_ASSIGN_VAR + REX_ASSIGN, js_org):
			res.append(el)

		while len(re.findall(REX_ASSIGN_RECURS, ''.join(el + '\n' for el in res))) > 0:
			for el in res:
				if len(re.findall(REX_ASSIGN_RECURS, el)) > 0:
					res.remove(el)

		return res


	def mutate_function(self, js_file=None):
		if js_file==None and self.target == None:
			self.logger.error("there's no target")
			return -1
		elif self.target == None:
			self.set_target(js_file)
		self.arguments_assignment = []
		#remove natives syntax
		assignments = self.search_assignments(self.js_org)
		self.param_num = min(random.randint(3, 6), len(assignments))
		mut = list()
		for _ in range(self.param_num):
			choice = random.choice(assignments)
			mut.append(choice)
			assignments.remove(choice)

		arg_idx = 0;
		for i, line in enumerate(mut):
			rex_var = "v[0-9]+"
			dt = re.search(REX_ASSIGN_GROUPS, line).group(1)
			sc = re.search(REX_ASSIGN_GROUPS, line).group(2)
			new_line = REX_ASSIGN_LET + '%s = a%d;'%(dt, i)
			#arg_idx += 1
			mut[i] = new_line

			self.line_org.append(line)
			self.line_mut.append(new_line)
			self.src_org.append(sc)
			self.arguments_assignment.append('var arg%d = %s;'%(i, sc))

		##problem when it's like v38=v39
		##changing all asssign method?? only const?
		##what to do if there's same line?
		decl_main = re.search('function main\(.*\)', self.js_mut).group(0)
		argument_string = 'a0'
		for i in range(self.param_num-1):
			argument_string += ', a%d'%(i+1)
		decl_main_new = "function main(%s)"%argument_string
		self.line_org.append(decl_main)
		self.line_mut.append(decl_main_new)


		for i in range(len(self.line_org)):
			self.js_mut = self.js_mut.replace(self.line_org[i], self.line_mut[i])

		##add main's argument

		##remove call main
		try:
			call_main = re.search('(\nmain\(.*\);)', self.js_mut).group(1)
			self.js_mut = self.js_mut.replace(call_main, '')
		except:
			pass

		return self.js_org, self.js_mut, self.arguments_assignment

	def pick_random_sample(self, count):
		for directory, _, files in os.walk(DIR_ALL_SAMPLE_JS):
			if directory == DIR_ALL_SAMPLE_JS:
				break
		res = np.random.choice(files, count)
		return res

	def gen_random_objects(self, count):
		res = list()
		choiced = self.pick_random_sample(count)
		
		for file in choiced:
			with open(DIR_ALL_SAMPLE_JS + file, 'r') as f:
				data = f.read()
			assign = self.search_assignments(data)

			res += list(np.random.choice(assign, min(int(random.random()*20), len(assign))))


		return np.random.choice(res, count)

	def clear_testdir(self):
		for p, d, f_list in os.walk(self.test_dir):
			for f in f_list:
				os.remove(p + f)

	def gen_test_sample(self):
		target = self.pick_random_sample(1)[0]
		target = DIR_ALL_SAMPLE_JS + target
		self.set_target(target)
		self.mutate_function()
		self.test_dir = DIR_TEST_SAMPLE 
		self.clear_testdir()

		with open(DIR_TEST_SAMPLE + 'org.js', 'w') as f:
			f.write(self.js_org)

		with open(DIR_TEST_SAMPLE + 'mut.js', 'w') as f:
			f.write(self.js_mut)

		with open(DIR_TEST_SAMPLE + 'initial_args.js', 'w') as f:
			data = ''
			data += 'load("%s");'%(JS_MUTATOR_PATH + 'index.js') + '\n'
			data += 'var args_pool = new Array();\n'
			data += 'var arg_array = new Array();\n'
			data += 'var arg_orig = new Array();\n'
			data += 'var tmp_array = new Array();\n'
			data += 'var tmp = undefined;\n'
			self.param_string = ''
			for i in range(self.param_num):
				data += 'arg_array[%d] = deepClone(arg%d);\n'%(i, i)
				self.param_string += 'arg%d,'%i
			self.param_string = self.param_string[:-1]
			data += 'arg_orig = deepClone(arg_array);\n'
			data += 'args_pool[0] = deepClone(arg_array);\n'
			data += 'load("%smut.js");'%self.test_dir

			for line in self.arguments_assignment:
				f.write(line + '\n')

			f.write(data)

		with open(DIR_TEST_SAMPLE + 'org_filename.txt', 'w') as f:
			f.write(self.target)

		with open(DIR_TEST_SAMPLE + 'param_string.txt', 'w') as f:
			f.write(self.param_string)

		return DIR_TEST_SAMPLE


	def gen_test_sample_target(self, target, targetdir,argnum):
		#target = self.pick_random_sample(1)[0]
		#target = DIR_ALL_SAMPLE_JS + target
		self.set_target(target)
		#self.mutate_function(js_file = target)
		with open(target, 'r') as f:
			target_data = f.read()
		self.js_org = target_data
		self.js_mut = target_data
		self.param_num = argnum
		self.test_dir = DIR_TEST_SAMPLE 
		self.clear_testdir()

		with open(DIR_TEST_SAMPLE + 'org.js', 'w') as f:
			f.write(self.js_org)

		with open(DIR_TEST_SAMPLE + 'mut.js', 'w') as f:
			f.write(self.js_mut)

		with open(targetdir + 'repro_arguments', 'r') as f:
			arguments_assignment = f.read()

		self.arguments_assignment=[]
		for line in arguments_assignment.split('\n'):
			self.arguments_assignment.append(line)

		with open(DIR_TEST_SAMPLE + 'initial_args.js', 'w') as f:
			data = ''
			data += 'load("%s");'%(JS_MUTATOR_PATH + 'index.js') + '\n'
			data += 'var args_pool = new Array();\n'
			data += 'var arg_array = new Array();\n'
			data += 'var arg_orig = new Array();\n'
			data += 'var tmp_array = new Array();\n'
			data += 'var tmp = undefined;\n'
			
			self.param_string = ''
			for i in range(self.param_num):
				data += 'arg_array[%d] = deepClone(arg%d);\n'%(i, i)
				self.param_string += 'arg%d,'%i
			self.param_string = self.param_string[:-1]
			
			self.param_string = "arg0,arg1,arg2,arg3,[],arg5"
			data += 'arg_orig = deepClone(arg_array);\n'
			data += 'args_pool[0] = deepClone(arg_array);\n'
			data += 'load("%smut.js");'%self.test_dir

			for line in self.arguments_assignment:
				f.write(line + '\n')

			f.write(data)

		with open(DIR_TEST_SAMPLE + 'org_filename.txt', 'w') as f:
			f.write(self.target)

		with open(DIR_TEST_SAMPLE + 'param_string.txt', 'w') as f:
			f.write(self.param_string)

		return DIR_TEST_SAMPLE






