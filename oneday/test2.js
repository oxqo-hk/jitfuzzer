function v7(v8,v11) {
    function v14(v15,v16) { }
    // Transition to dictionary mode in the final invocation.
    const v17 = v11.__defineSetter__(v8, v14);
    // Will then read OOB.
    const v18 = v11.includes(1234);
    return v18;
}
v7([], []);
v7([], []);
%OptimizeFunctionOnNextCall(v7);
v7([], []);
