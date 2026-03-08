import sys
path=sys.argv[1]
with open(path,'r',encoding='utf-8',errors='ignore') as f:
    data=f.read(1000)
print('first chunk:', repr(data[:500]))
