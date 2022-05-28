import sys
import mutator
from jitfuzzer import *
import time
import os

target = "/home/oxqo/experiment/js_samples/repro/repro.js"
targetdir = "/home/oxqo/experiment/js_samples/repro/"

test_num = sys.argv[1]
m = mutator.Mutator()
m.gen_test_sample_target(target, targetdir, 6)
#m.param_string = "arg0,arg1,arg2,arg3,[],arg5"
start = time.time()

segfault_count = 0
while True:
	start = time.time()
	fuzz = JitFuzzer(start, m, guide_mode=True, disable_deopt=True)
	result = fuzz.fuzz_one()
	os.system('kill -9 `pidof d8`')
	os.system('rm example.log')
	if time.time() - start > (2*60):
		result = 'SUCCESS'
		continue
	if result in ['ERROR', 'TIMEOUT']:
		os.system('kill -9 `pidof python` `pidof d8`')
	elif result in ['DEOPTIMIZED', 'TIMEOUT_CONTINUABLE']:
		continue
	elif result == 'SEGFAULT':
		segfault_count += 1
		break
	elif result == 'SUCCESS':
		m = mutator.Mutator()
		m.gen_test_sample_target(target)
		continue


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
