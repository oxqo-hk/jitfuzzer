String.prototype.repeat = function(num) {
    if (num < 0) {
        return '';
    } else {
        return new Array(num + 1).join(this);
    }
};

function is_defined(x) {
    return typeof x !== 'undefined';
}

function is_object(x) {
    return Object.prototype.toString.call(x) === "[object Object]";
}

function is_array(x) {
    return Object.prototype.toString.call(x) === "[object Array]";
}

/**
 * Main.
 */
function xlog(v, label) {
    var tab = 0;

    var rt = function() {
        return '    '.repeat(tab);
    };

    // Log Fn
    var lg = function(x) {
        // Limit
        if (tab > 10) return '[...]';
        var r = '';
        if (!is_defined(x)) {
            r = '[VAR: UNDEFINED]';
        } else if (x === '') {
            r = '[VAR: EMPTY STRING]';
        } else if (is_array(x)) {
            r = '[\n';
            tab++;
            for (var k in x) {
                r += rt() + k + ' : ' + lg(x[k]) + ',\n';
            }
            tab--;
            r += rt() + ']';
        } else if (is_object(x)) {
            r = '{\n';
            tab++;
            for (var k in x) {
                r += rt() + k + ' : ' + lg(x[k]) + ',\n';
            }
            tab--;
            r += rt() + '}';
        } else {
            r = x;
        }
        return r;
    };

    // Space
    print('\n\n');

    // Log
    print('< ' + (is_defined(label) ? (label + ' ') : '') + Object.prototype.toString.call(v) + ' >\n' + lg(v));
};



// Demo //

var o = {
    'aaa' : 123,
    'bbb' : 'zzzz',
    'o' : {
        'obj1' : 'val1',
        'obj2' : 'val2',
        'obj3' : [1, 3, 5, 6],
        'obj4' : {
            'a' : 'aaaa',
            'b' : null
        }
    },
    'a' : [ 'asd', 123, false, true ],
    'func' : function() {
        alert('test');
    },
    'fff' : false,
    't' : true,
    'nnn' : null
};

xlog(o, 'Object'); // With label
xlog(o); // Without label

xlog(['asd', 'bbb', 123, true], 'ARRAY Title!');

var no_definido;
xlog(no_definido, 'Undefined!');

xlog(true);

xlog('', 'Empty String');