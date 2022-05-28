function main() {
    const v59 = [13.37];
    const v49 = [13.37];
    let v1 = 0x1234;
    let v2 = [].fill.call({length: 120}, 0);
    let v3 = true;
    let v4 = 0x4321;
    let v8 = [];
    let v11 = [];
    
    let v104 = 0;
    while (v104 < 3) {
        for (const v105 of v49) {
            v105.c = v59;
        }
        const v106 = v104 + 1;
        v104 = v106;
    }
    let v117 = 0;
    while (v117 < 10) {
        const v118 = {
            has: Object,
            defineProperty: Object,
            ownKeys: Object,
            getOwnPropertyDescriptor: Object,
            isExtensible: Object,
            set: Object,
            construct: Object,
            deleteProperty: Object,
            setPrototypeOf: Object,
            getPrototypeOf: Object,
            preventExtensions: Object,
            apply: Object,
            get: Object
        };
        const v119 = v117 + 1;
        v117 = v119;
    }
    if (v1 < v4) {
        if (v2.length > 100 && v2[2] != null) {
            if (v3) {
                function v14(v15, v16) {}
                // Transition to dictionary mode in the final invocation.
                const v17 = v11.__defineSetter__(v8, v14);
                // Will then read OOB.
                const v18 = v11.includes(1234);
                return v18;
            } else {
                let v98 = 1337;
            }
        } else {
            const v100 = Object();
        }
    } else {
        const v109 = -253146551;
    }
}
%NeverOptimizeFunction(main);
main()
