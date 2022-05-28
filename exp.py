import sys
import mutator
from jitfuzzer import *
import time
import os


if len(sys.argv) < 2:
	test_num = 0
else:
	test_num = sys.argv[1]
m = mutator.Mutator()
m.gen_test_sample()
start = time.time()


fuzz = JitFuzzer(start, m, guide_mode=True, disable_deopt=True)
segfault_count = 0
while True:
	result = fuzz.fuzz_one()
	os.system('kill -9 `pidof d8`')
	os.system('rm example.log')
	if time.time() - start > (2*60):
		result = 'SUCCESS'
		break
	if result in ['ERROR', 'TIMEOUT']:
		os.system('kill -9 `pidof python` `pidof d8`')
	elif result in ['DEOPTIMIZED', 'TIMEOUT_CONTINUABLE']:
		continue
	elif result == 'SEGFAULT':
		segfault_count += 1
	elif result == 'SUCCESS':
		break

log = open('data/experiment.log', 'a')	
log.write('--------------------------------------------------------\n')
log.write("test " + test_num + ' start!\n')
log.write("file: " + m.target + "\n")
log.write("##################################\n")
log.write("Guided, deopt disabled:")
log.write(result + '\n')
log.write(json.dumps(fuzz.coverage.all, indent=2))
log.write("explored total: %.4f%%\n"%(fuzz.coverage.explored_total()*100))
log.write("path variation: %d\n"%(len(fuzz.coverage.all)))
log.write("success: %d, fail: %d\n"%fuzz.coverage.counter)
log.write("iteration: %d\n"%fuzz.coverage.get_iteration())
log.write("segfault_count: %d\n"%segfault_count)
log.write("##################################\n")
log.flush()
fuzz.dbg.io.cleanup()

start = time.time()
fuzz = JitFuzzer(start, m, guide_mode=False, disable_deopt=True)
segfault_count = 0
while True:
	result = fuzz.fuzz_one()
	os.system('kill -9 `pidof d8`')
	os.system('rm example.log')
	if time.time() - start > (2*60):
		result = 'SUCCESS'
		break
	if result in ['ERROR', 'TIMEOUT']:
		continue
	elif result in ['DEOPTIMIZED', 'TIMEOUT_CONTINUABLE']:
		continue
	elif result == 'SEGFAULT':
		segfault_count += 1
	elif result == 'SUCCESS':
		break

log.write("##################################\n")
log.write("Not guided, deopt disabled:")
log.write(result + '\n')
data = json.dumps(fuzz.coverage.all, indent=2)
log.write(data + '\n')
log.write("explored total: %.4f%%\n"%(fuzz.coverage.explored_total()*100))
log.write("path variation: %d\n"%(len(fuzz.coverage.all)))
log.write("success: %d, fail: %d\n"%fuzz.coverage.counter)
log.write("iteration: %d\n"%fuzz.coverage.get_iteration())
log.write("segfault_count: %d\n"%segfault_count)
log.write("##################################\n")
log.flush()
fuzz.dbg.io.cleanup()

start = time.time()
fuzz = JitFuzzer(start, m, guide_mode=False, disable_deopt=False)
segfault_count = 0
while True:
	result = fuzz.fuzz_one()
	os.system('kill -9 `pidof d8`')
	os.system('rm example.log')
	if time.time() - start > (2*60):
		result = 'SUCCESS'
		break
	if result in ['ERROR', 'TIMEOUT']:
		continue
	elif result in ['DEOPTIMIZED', 'TIMEOUT_CONTINUABLE']:
		continue
	elif result == 'SEGFAULT':
		segfault_count += 1
	elif result == 'SUCCESS':
		break

log.write("##################################\n")
log.write("Not guided, deopt enabled:")
log.write(result + '\n')
log.write(json.dumps(fuzz.coverage.all, indent=2))
log.write("explored total: %.4f%%\n"%(fuzz.coverage.explored_total()*100))
log.write("path variation: %d\n"%(len(fuzz.coverage.all)))
log.write("success: %d, fail: %d\n"%fuzz.coverage.counter)
log.write("iteration: %d\n"%fuzz.coverage.get_iteration())
log.write("segfault_count: %d\n"%segfault_count)
log.write("##################################\n\n\n")
log.flush()
log.close()
fuzz.dbg.io.cleanup()

os.system('kill -9 `pidof python` `pidof d8`')