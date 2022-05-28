function add(a, b){
	return a + b;
}

function main(x){
	let a = x;
	let b = 1234;
	let c = 1.1;

	for(var d=0; d<100000; d++){
		c = add(a, b);
	}

	console.log(c);
}

for(let i=0;i<1000;i++){
	main(100);
}
