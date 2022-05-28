function main(arg) {
const v4 = [13.37,13.37,13.37];
const v6 = [1337,1337,1337];
const v7 = [13.37,"symbol",13.37,RegExp];
const v8 = {toString:13.37,c:RegExp};
const v9 = {toString:v8};
let v10 = 1337;
const v15 = [13.37,13.37,13.37];
const v17 = [1337];
const v18 = [Set,Set,"toString",65537];
const v19 = {length:v15,toString:v17,d:v18};
let v20 = Set;
let v26 = 1337;
const v31 = [];
const v32 = {constructor:v31,length:13.37,e:WeakMap};
const v33 = {length:WeakMap,constructor:13.37};
let v34 = 1337;
const v40 = [13.37];
"toString".__proto__ = v19;
const v42 = [1337];
const v43 = [];
const v44 = {constructor:v43,length:13.37,e:WeakMap};
const v45 = {length:WeakMap,constructor:v40};
let v46 = 1337;
const v50 = [];
const v53 = [1337];
const v59 = [13.37];
const v60 = [];
const v62 = Object();
const v66 = new Int32Array(62651);
const v67 = "CE2Si6Ijpu"[v66];
let v71 = v59;
let v72 = 1337;
const v79 = [13.37];
const v81 = [13.37];
const v82 = [];
const v87 = [13.37];
const v89 = [1337];
const v90 = [];
const v91 = {constructor:v90,length:13.37,e:WeakMap};
const v92 = {length:WeakMap,constructor:v87};
function v96(v97,v98,v99) {
    for (const v100 in v98) {
    }
}
let v103 = 0;
for (const v104 of v90) {
    if (v104) {
    } else {
    }
}
const v105 = v103 + 1;
v103 = v105;
v6.__proto__ = v45;
const v108 = [13.37];
const v111 = "CE2Si6Ijpu" < v71;
let v112 = v42;
v112 = v62;
let v123 = 0;
const v125 = v123 + 1;
v123 = v125;
for (let v129 = 0; v129 < 100; v129++) {
}
v42[4] = v17;
const v163 = v43.__proto__;
const v164 = -253146551 / v44;
const v165 = "CE2Si6Ijpu".indexOf();
const v192 = Object(1337,WeakMap);
v53[-2046000388] = WeakMap;
return a.map(v => v);
}
//main();

let a = [1, 2, ,,, 3];

//%NeverOptimizeFunction(main);
for (let i=0; i<10; i++){
    main(a);
}
%OptimizeFunctionOnNextCall(main);
main(a);
console.log('11111111');

a.length = 33554431;
console.log('22222');
a.fill(1,0);
console.log('3333');
a.push(2);
console.log('4444');
a.length += 500;

main(a);
