import hashlib
import time
import sys

def calculate_script_hash():
    with open(sys.argv[0], 'rb') as f:
        exe_content = f.read()
    hasher = hashlib.sha256()
    hasher.update(exe_content)

    timestamp = str(time.time()).encode('utf-8')
    hasher.update(timestamp)

    return hasher.hexdigest()
