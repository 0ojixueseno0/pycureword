import hashlib

needhash = "12345upload123test"
print(hashlib.md5(needhash.encode('utf-8')).hexdigest())