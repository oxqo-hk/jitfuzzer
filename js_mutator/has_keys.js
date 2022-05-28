function hasKeys(source) {
    return source !== null &&
        (typeof source === "object" ||
        typeof source === "function")
}
