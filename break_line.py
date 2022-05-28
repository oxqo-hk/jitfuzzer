def bl(data):
    x = data.encode('hex')
    y = ''
    for i in range(0, len(x), 2):
        y += '\\x' + x[i:i+2]

    for i in range(0, len(y), 4*20):
        print '"' + y[i:min(i+4*20, len(y))] + '"\\'

