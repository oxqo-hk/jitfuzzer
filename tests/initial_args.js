var arg0 = 1;
var arg1 = [];arg1.length=120;arg1.fill(10);
var arg2 = true;
var arg3 = [];
var arg4 = [];
var arg5 = 2;

load("/mnt/hgfs/share/jitfuzzer/js_mutator/index.js");
var args_pool = new Array();
var arg_array = new Array();
var arg_orig = new Array();
var tmp_array = new Array();
var tmp = undefined;
arg_array[0] = deepClone(arg0);
arg_array[1] = deepClone(arg1);
arg_array[2] = deepClone(arg2);
arg_array[3] = deepClone(arg3);
arg_array[4] = deepClone(arg4);
arg_array[5] = deepClone(arg5);
arg_orig = deepClone(arg_array);
args_pool[0] = deepClone(arg_array);
load("/mnt/hgfs/share/jitfuzzer/tests/mut.js");