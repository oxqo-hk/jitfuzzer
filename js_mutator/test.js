load('index.js')

fuzzer.seed(Date.now());
var y = new ArrayBuffer();
var z = [1, 2, 3]
console.log(typeof y);
console.log(typeof 2);

var mut = [[[7, 6,5, 4, "hello"], {v : 2}, y,4, 5]];
console.log(JSON.stringify(mut));

/*
for (let i=0; i<100; i++){
	fuzzer.mutate.object(mut)();
	print(JSON.stringify(mut));
}
*/

printObject(mut, 'mut');

for(i=0;i<3;i++)
	mutateProperty(mut, undefined, 0);

printObject(mut, 'mut');
