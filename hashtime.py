from hashlib import sha256, md5
from time import time
from timeit import default_timer as timer
import numpy as np

N = int(1e6)

sha256_times = np.zeros(N)

numbers = np.random.rand(N)

def test(fun):
    times = np.zeros(N)
    for i,num in zip(range(len(numbers)),numbers):
        m = fun()
        start = timer()
        m.update(str(num).encode())
        m.digest()
        end = timer()
        times[i] = end - start
    return times

md5_times = test(md5)
sha256_times = test(sha256)

print( f' MD5  : mean={md5_times.mean():.3e} stdev={md5_times.std():.3e}' )
print( f'SHA256: mean={sha256_times.mean():.3e} stdev={sha256_times.std():.3e}' )
