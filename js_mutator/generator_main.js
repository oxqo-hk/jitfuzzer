/*global define:true*/

'use strict';

// Generates random values of the types defined in:
//
// Standard ECMA-262 ECMAScript® Language Specification Edition 5.1 (June 2011)
// http://www.ecma-international.org/publications/standards/Ecma-262.htm

// if (typeof define !== 'function') { var define = require('amdefine')(module) }


 var object;
 function randomElement(array) {
   return array[_.random(array.length - 1)];
 }
 function generator(options) {
   var value;
   options = options || {};
   if (options.values) {
     // 25% of the time, return a previous value in order to create circular
     // references.
     if (Math.random() < 0.25)
       return randomElement(options.values);
   }
   else
     options.values = [];
   value = randomElement(_.values(generator))(options);
   options.values.push(value);
   return value;
 }
 // 8.1 Undefined
 generator.undefined = function () {
   return undefined;
 };
 // 8.2 Null
 generator.null = function () {
   return null;
 };
 // 8.3 Boolean
 generator.boolean = function () {
   return Math.random() < 0.5;
 };
 // 8.4 String
 generator.string = function (options) {
   var charCodes, charCodeLimit;
   options = options || {};
   charCodes = [];
   charCodeLimit = Math.pow(2, 16);
   _.times(_.random(options.maximumLength || 10), function () {
     charCodes.push(_.random(charCodeLimit));
   });
   return String.fromCharCode.apply(null, charCodes);
 };
 // 8.5 Number
 generator.number = function () {
   return randomElement([
     function () {
       var sign;
       sign = generator.boolean() ? -1 : 1;
       return sign * Math.random() * Number.MAX_VALUE;
     },
     // This must be generated separately because the above function will
     // never generate it.
     function () { return Number.MAX_VALUE; },
     function () { return NaN; },
     function () { return -Infinity; },
     function () { return Infinity; }
   ])();
 };
 // 8.6 Object
 generator.object = object = function (options) {
   var types;
   options = options || {};
   types = Object.keys(object);
   return object[randomElement(options.functions === false
     ? _.without(types, 'function')
     : types
   )](options);
 };
 object.simple = function (options) {
   var length, name, object;
   function getter() {
   }
   function setter() {
   }
   options = _.clone(options) || {};
   length = _.random(options.maximumLength || 10);
   delete options.maximumLength;
   object = options.base || {};
   // Choose random but unique property names.
   while (Object.getOwnPropertyNames(object).length < length) {
     name = generator.string();
     if (!(name in object))
       Object.defineProperty(object, name,
         (options.functions === false) || generator.boolean()
         ? {
             value: generator(options),
             writable: generator.boolean(),
             enumerable: generator.boolean(),
             configurable: generator.boolean()
           }
         : {
             get: getter,
             set: setter,
             enumerable: generator.boolean(),
             configurable: generator.boolean()
         });
   }
   return object;
 };
 // 15.3 Function
 object.function = function (options) {
   options = _.clone(options) || {};
   options.base = function () {};
   return object.simple(options);
 };
 // 15.4 Array
 object.array = function (options) {
   var array, length;
   options = _.clone(options) || {};
   length = _.random(options.maximumLength || 10);
   delete options.maximumLength;
   array = [];
   _.times(length, function () {
     array.push(generator(options));
   });
   return array;
 };
 // 15.9 Date
 object.date = function () {
   // The actual range of times supported by ECMAScript Date objects is ...
   // exactly –100,000,000 days to 100,000,000 days measured relative to
   // midnight at the beginning of 01 January, 1970 UTC. This gives a range
   // of 8,640,000,000,000,000 milliseconds to either side of 01 January,
   // 1970 UTC.
   return new Date(_.random(-8640000000000000, 8640000000000000));
 };
 // 15.10 RegExp
 object.regexp = function () {
   // example taken from http://es5.github.io/#x15.10.2.3
   return new RegExp('((a)|(ab))((c)|(bc))',
       (generator.boolean() ? 'g' : '')
     + (generator.boolean() ? 'i' : '')
     + (generator.boolean() ? 'm' : ''));
 };
 // 15.11 Error
 object.error = function (options) {
   var error;
   options = options || {};
   error = new (randomElement([Error, RangeError, ReferenceError,
     SyntaxError, TypeError, URIError]))(random.string());
   // The non-standard property 'stack' sometimes has a getter function.
   if (options.functions === false)
     delete error.stack;
   return error;
 };
