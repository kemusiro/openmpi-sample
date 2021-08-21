from mpi4py import MPI
import gmpy2 as mp
from gmpy2 import mpz, mpfr
import mmap
import sys

A = mpz(13591409)
B = mpz(545140134)
C = mpz(640320)
C3over24 = mpz(C**3 / 24)

def calc_PQT_root(n):
    """円周率を並列に計算する。
    """
    # まず自分の割り当て分を計算する。
    alloc = int(n / size)
    P2, Q2, T2 = calc_PQT_local(rank * alloc, (rank + 1) * alloc)

    # 各ノードの計算結果をマージする。
    level = int(mp.ceil(mp.log2(size)))
    k = 1
    for i in range(level):
        if (rank & k) == k:
            P1, Q1, T1 = comm.recv(source=rank-k, tag=0)
            T2 = T1 * Q2 + P1 * T2
            P2 = P1 * P2
            Q2 = Q1 * Q2
            k *= 2
        else:
            comm.send((P2, Q2, T2), dest=rank+k, tag=0)
            break
    return P2, Q2, T2
        
def calc_PQT_local(n1, n2):
    """ノード内でP(n1, n2), Q(n1, n2), T(n1, n2)を計算する。
    """
    if n1 + 1 == n2:
        P = (-1) * (2 * n2 - 1) * (6 * n2 - 5) * (6 * n2 - 1)
        Q = C3over24 * n2 ** 3
        T = (A + B * n2) * P
        return P, Q, T
    else:
        m = int((n1 + n2) / 2)
        P1, Q1, T1 = calc_PQT_local(n1, m)
        P2, Q2, T2 = calc_PQT_local(m, n2)
        P = P1 * P2
        Q = Q1 * Q2
        T = T1 * Q2 + P1 * T2
        return P, Q, T

def check_pi():
    """円周率が何桁まで一致するかを判定する。
    """
    with open('/share/common/pi-10oku.txt', 'rb') as f0, open('pi.txt', 'rb') as f1:
        mm0 = mmap.mmap(f0.fileno(), 0, flags=mmap.MAP_PRIVATE)
        mm1 = mmap.mmap(f1.fileno(), 0, flags=mmap.MAP_PRIVATE)
        index = mpz(0) 
        length = 1024 * 1024
        mm0.seek(0)
        mm1.seek(0)
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
        mm0.close()
        mm1.close()
    return n
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('pi_chudnovsky.py <power>')
        sys.exit(1)
    power = int(sys.argv[1])
    digits = (2 ** power) * 14
    prec = int(digits * mp.log2(10))
    n = int(digits / 14)
    mp.get_context().precision=prec

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    name = MPI.Get_processor_name()

    if rank == size - 1:
        print('calculating...')
    start0 = MPI.Wtime()
    P, Q, T = calc_PQT_root(n)
    if rank == size - 1:
        temp1 = C * mp.sqrt(C) * Q
        temp2 = 12 * (T + A * Q)
        pi = temp1 / temp2
        end1 = MPI.Wtime()
        with open('pi.txt', 'w') as f:
            f.write(str(pi))
        print('checking...')
        n = check_pi()
        print('time = {:.2f} sec.'.format(end1 - start0))
        print(f'match = {n}')
