#!/bin/env python3
import unicodedata
import os, sys

target = sys.argv[1] if len(sys.argv)>=2 else 'NFC'
x = unicodedata.normalize(target, sys.stdin.read())
if target == 'NFC':
    x = x.replace('ı́', 'í')
print(x)
