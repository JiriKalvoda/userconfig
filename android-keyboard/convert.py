import zipfile
import json
from pprint import pprint

archive = zipfile.ZipFile('orig.zip', 'r')
file = archive.open('220928 Keyboard Data.json')
data = json.loads(file.read())
pprint(data)

def decode(x):
    bytes.fromhex(x).decode('utf-16-BE')

def encode(x):
    x.encode('utf-16-BE').hex().upper()

def proc_k(k):
    for x in k:
        if x[0] == "F":
            k[x] = proc_act(k[x])
    return k

def proc_act(act):
    print(act)
    act = {x["JMID"]: x for x in act}

    if 0 in act:
        act[1] = act[0]

    for i in act:
        act[i]["JMID"] = i
    return list(act.values())

for desighn in data["Designs"]:
    if desighn["Name"] == "UCW":
            desighn["Keys"] = [
                    proc_k(i) for i in desighn["Keys"]
                    ]

with zipfile.ZipFile('out.zip', 'w') as archive:
    with archive.open('220928 Keyboard Data.json', "w") as file:
        file.write(json.dumps(data).encode())
