
def query(row, col):
    return table[row][col]

table = {}

def s(r, c, code):
    table.setdefault(r, {})
    assert c not in table[r]
    table[r][c] = code

def sv(r, c, vec):
    for i, code in enumerate(vec):
        s(r, c+i, code)

s(0,0,9)
for i in range(11, 13): s(0, i, 95+i-11)
for i in range(1 , 11): s(0, i, 67+i-1)

s(1, 0, 49)
for i in range(1, 14): s(1, i, 10+i-1)

for i in range(0, 14): s(2, i, 23+i)

s(3, 0, 66)
for i in range(1, 12): s(3, i, 38+i-1)
s(3, 12, 51)

for i in range(0, 12): s(4, i, 50+i if i!= 1 else 94)

sv(5, 0, [37, 133, 64, 65, 108, 105])
sv(6, 0, [107, 78, 127])
sv(7, 0, [118, 110, 112])
sv(8, 0, [119, 115, 117])
sv(9, 0, [111])
sv(10, 0, [113, 116, 114])
sv(11, 0, [77, 106, 63, 82])
sv(12, 0, [79, 80, 81, 86])
sv(13, 0, [83, 84, 85])
sv(14, 0, [87, 88, 89, 104])
sv(15, 0, [90, 91])
