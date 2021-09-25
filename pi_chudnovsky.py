from mpi4py import MPI
import gmpy2 as mp
from gmpy2 import mpz
import numpy as np
import mmap
import sys

# 円周率を並列に計算する。
def calc_PQT_root(n):
    # まず自分の割り当て分を計算する。
    alloc = int(n / size)
    PQT2 = calc_PQT_local(rank * alloc, (rank + 1) * alloc)

    # 各ノードの計算結果をマージする。
    level = int(mp.ceil(mp.log2(size)))
    k = 1
    for _ in range(level):
        if (rank & k) == k:
            PQT1 = comm.recv(source=rank-k, tag=0)
            PQT2 = np.array([PQT1[0] * PQT2[0],
                             PQT1[1] * PQT2[1],
                             PQT1[2] * PQT2[1] + PQT1[0] * PQT2[2]])
            k *= 2
        else:
            comm.send(PQT2, dest=rank+k, tag=0)
            break
    return PQT2

# ノード内でP(n1, n2), Q(n1, n2), T(n1, n2)を計算する。
def calc_PQT_local(n1, n2):
    if n1 + 1 == n2:
        P = mpz((-1) * (2 * n2 - 1) * (6 * n2 - 5) * (6 * n2 - 1))
        return np.array([P, C3over24 * n2 ** 3, (A + B * n2) * P])
    else:
        m = int((n1 + n2) / 2)
        PQT1 = calc_PQT_local(n1, m)
        PQT2 = calc_PQT_local(m, n2)
        return np.array([PQT1[0] * PQT2[0],
                         PQT1[1] * PQT2[1],
                         PQT1[2] * PQT2[1] + PQT1[0] * PQT2[2]])

# 円周率が何桁まで一致するかを判定する。
def check_pi(pifile):
    with open(pifile, 'rb') as f0, \
         open('pi.txt', 'rb') as f1:
        # 2つのファイルをメモリにマップして比較する。
        with mmap.mmap(f0.fileno(), 0, flags=mmap.MAP_PRIVATE) as mm0, \
             mmap.mmap(f1.fileno(), 0, flags=mmap.MAP_PRIVATE) as mm1:
            index = mpz(0) 
            length = 1024 * 1024 # 一度にチェックする桁数
            found = False
            while not found:
                ans = mm0.read(length)
                calc = mm1.read(length)
                if ans != calc:
                    maxlen = min(len(ans), len(calc))
                    for i in range(maxlen):
                        if ans[i] != calc[i]:
                            n = index + i - 2
                            found = True
                            break
                    else:
                        n = index + maxlen - 3
                        break
                else:
                    index += length
    return n
    
if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    A = mpz(13591409)
    B = mpz(545140134)
    C = mpz(640320)
    C3over24 = mpz(C**3 / 24)

    power = int(sys.argv[1])
    n = 2 ** power
    digits = n * 14
    # gmpy2の浮動小数の精度として、求められる円周率の桁数を設定する。
    mp.get_context().precision = int(digits * mp.log2(10))

    if rank == size - 1:
        print('calculating...')
    start = MPI.Wtime()
    PQT = calc_PQT_root(n)
    if rank == size - 1:
        temp1 = C * mp.sqrt(C) * PQT[1]
        temp2 = 12 * (PQT[2] + A * PQT[1])
        pi = temp1 / temp2
        end = MPI.Wtime()
        with open('pi.txt', 'w') as f:
            f.write(str(pi))
        print('checking...')
        if len(sys.argv) > 2:
            pifile = sys.argv[2]
        else:
            pifile = '/share/common/pi-10oku.txt'
        n = check_pi(pifile)
        print('time = {:.2f} sec.'.format(end - start))
        print(f'match = {n}')
