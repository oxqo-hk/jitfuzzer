var random = new Random(Random.engines.mt19937().seed(0));

/**
 * @param _ {number}
 * @returns {null}
 */

var fuzzer = {};

fuzzer.seed = function(_) {
    random = new Random(Random.engines.mt19937().seed(_));
};

fuzzer.mutate = {
    object: mutateObject,
    string: mutateString
};

function mutateObject(obj) {
    return function generate() {
        // copy the object so that modifications
        // are not additive
        var copy = xtend({}, obj);
        traverse(copy).forEach(transformObjectValue);
        return copy;
    };
}

function transformObjectValue(val) {
    if (random.bool(0.1)) {
        mutateVal.call(this, val);
    } else if (random.bool(0.008)) {
        if (this.level) {
            this.remove();
        }
    }
}

function mutateVal(val) {
    switch(typeof val) {
        case 'boolean':
            this.update(!val);
            break;
        case 'number':
            this.update(val + random.real(-1000, 1000));
            break;
        case 'string':
            this.update(mutateString(val));
            break;
        default:
            if (Array.isArray(val)) this.update(mutateArray(val));
            break;
    }
    if (random.bool(0.01)){
        this.update(mutateWithProperty(val, null, 0))
    }
}

function mutateVal2(val) {
    switch(typeof val) {
        case 'boolean':
            return (!val);
        case 'number':
            return (val + random.real(-1000, 1000));
        case 'string':
            return (mutateString(val));
        case 'bigint':
            return (BigInt(random.integer(Number.MIN_SAFE_INTEGER, Number.MAX_SAFE_INTEGER)))
        default:
            if (Array.isArray(val)) return (mutateArray(val));
        }
}

/**
 * @param val {string} a string value
 * @returns {string}
 */
function mutateString(val) {
    var arr = val.split('');
    if (random.bool(0.05)) {
        arr = arr.reverse();
    }
    if (random.bool(0.25)) {
        arr.splice(
            random.integer(1, arr.length),
            random.integer(1, arr.length));
    }
    if (random.bool(0.25)) {
        var args = [random.integer(1, arr.length), 0]
            .concat(random.string(random.integer(1, arr.length)).split(''));
        arr.splice.apply(arr, args);
    }
    val = arr.join('');
    return val;
}

/**
 * @param val {array} an array
 * @returns {array}
 */
function mutateArray(val) {
    if (random.bool(0.1)) {
        val = val.reverse();
    }
    if (random.bool(0.1)) {
        val = val.slice(random.integer(0, val.length));
    }

    if (random.bool(0.1)) {
        val = val.slice(0, random.integer(0, val.length));
    }

    if (random.bool(0.1)){
        val.push(generator());
    }
    if (random.bool(0.1)){
        val = 0xfffff;
    }
    return val;
}
/*
function mutateArray2(val) {
    if (random.bool(0.2)){
        val = val.reverse();
    }else if (random.bool(0.9)){
        if (random.bool(0.5)){
            //increase length
            if (random.bool(0.5)){
                val.push(generator());
            }else{
                for (let i=0;i<0x20000001;i++){
                    val[i] = 1.1;
                }
            }
        }else{
            //reduce length
            if random.bool(0.5){
                val = val.slice(random.integer(0, val.length));
            }else{
                val = val.slice(0, random.integer(0, val.length));
            }       
        }
    }else{
        val.length = random.integer(0, 9007199254740991);
    }
    
    return val;
}
*/

function printObject(obj, obj_name, parent){
    if (parent === obj || obj === undefined || obj === null){
        print("name: " + obj_name);
        print("value: " + JSON.stringify(obj));
        return 0;
    }
    
    print("name: " + obj_name);
    print("value: " + JSON.stringify(obj));

    let type = Object.prototype.toString.call(obj);
    print("type: " + type)
    let iter = Object.getOwnPropertyNames(obj);
    print("properties:")
    print(iter)
    print("\n\n")
    iter.map(function (name){
        print(JSON.stringify(Object.getOwnPropertyDescriptor(obj, name)));
        printObject(obj[name], obj_name + '[\'' + name + '\']', obj)
    });

}

function addProperty(obj){
    obj[random.string(random.integer(1, 100))] = generator();
    return obj;
}

function mutateWithProperty(obj, parent, level){
    if (parent === obj || obj === undefined || obj === null || level > 30)
        if(random.bool(0.5))
            return generator();
        else
            return obj;

    //if (random.bool(0.05) && level != 0){
    if (random.bool(0.3)){
        obj = generator();
        return mutateVal2(obj);
    }

    else if(random.bool(0.1)){
        obj = addProperty(obj);
        return obj;
    }
    let iter = Object.getOwnPropertyNames(obj);
    iter.map(function (name){
        if (Object.getOwnPropertyDescriptor(obj, name)['configurable'] == true){
            obj[name] = mutateWithProperty(obj[name], obj, level+1);
            return obj;
        } else if(Object.getOwnPropertyDescriptor(obj, name)['writable'] == true){
            if(random.bool(0.1))
                obj[name] = mutateVal2(obj[name]);
        }
    });
    return obj;

}

function mutateWithProperty2(obj, deep){
    if (obj === undefined || obj === null || deep > 5 )
        if(random.bool(0.5))
            return generator();
        else
            return obj;
        
    let iter = Object.getOwnPropertyNames(obj);
    iter.map(function(name){
        if (Object.getOwnPropertyDescriptor(obj, name)['writable'] == true && random.bool(0.5) ){
            print(name);
            obj.name = mutateWithProperty2(obj, deep+1);
            //return obj;
        }else if (Object.getOwnPropertyDescriptor(obj, name)['configurable'] == true && random.bool(0.5) ){
            Object.defineProperty(obj, name, {'writable': true});
            obj[name] = generator();
            //return obj;
        }
        else{
            obj = generator();
        }
    });
    return obj;
}


function mutate_custom(obj){
    if(random.bool(0.3)){
        if(random.bool(0.7)){
            return mutateVal2(obj);
        }
        else{
            return generator();
        }
    }
    else{
        return mutateWithProperty2(obj, 0);
    }

}

//mutate_custom([{1:2}, [1, 2, 3, 4], {x: "hello"}, "hello", [1, [1, 2], [3]]])
//var x = [{1:2}, [1, 2, 3, 4], {x: "hello"}, "hello", [1, [1, 2], [3]]]