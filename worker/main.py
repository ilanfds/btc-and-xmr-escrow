import time, os
print("worker online(stub). REDIS_HOST=", os.getenv("REDIS_HOST"))

while True:
    time.sleep(5)