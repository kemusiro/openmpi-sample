# openmpi-sample

Open MPIのサンプルプログラムです。

# 前提条件

以下の環境で実行できることを確認しています。

* Raspberry Pi 4 model B (8GB)
* Ubuntu 20.04
* Open MPI 4.0.3
* mpi4pyモジュール

# 実行方法

## hello.c

最小限のOpen MPIのプログラムです。

~~~c
/* mpi.h : MPIを使うために必要な定数やライブラリの定義が含まれる。 */
#include <mpi.h>
#include <stdio.h>

int main(int argc, char *argv[])
{
    int rank, size, name_len;
    char name[MPI_MAX_PROCESSOR_NAME];

    /* MPI実行環境の初期化(必須) */
    MPI_Init(&argc, &argv);
    /* 並列数を求める。 */
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    /* 自分自身のランクを求める。 */
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    /* 自分自身のプロセッサー名(ノード名)を求める。 */
    MPI_Get_processor_name(name, &name_len);
    printf("Hello, I'm process %d of %d on %s\n", rank, size, name);
    /* MPI実行環境の削除(必須) */
    MPI_Finalize();
    return 0;
}
~~~

このプログラムを`mpicc`によりコンパイルします。

~~~shell
$ mpicc hello.c -o hello
~~~

`mpirun`にオプションを指定せずに実行すると、Raspberry PiのCPUの4つのコアを用いて並列に実行します。

~~~shell
$ mpirun ./hello
Hello, I'm process 2 of 4 on node10
Hello, I'm process 0 of 4 on node10
Hello, I'm process 3 of 4 on node10
Hello, I'm process 1 of 4 on node10
~~~

この結果は、node10で4つのプロセスが並列実行されたことを意味します。複数のノードで並列実行する場合は、`mpirun`に適切なオプションを指定してください。たとえばnode10、node11、node12、node13の4つのノードを使って実行する場合は以下のようにします。

~~~shell
$ mpirun --map-by core -H node10,node11,node12,node13  ./hello
Hello, I'm process 0 of 4 on node10
Hello, I'm process 1 of 4 on node11
Hello, I'm process 2 of 4 on node12
Hello, I'm process 3 of 4 on node13
~~~

## hello.py

`hello.c`のPython版です。実行には`mpi4py`モジュールをあらかじめインストールしてください。

~~~shell
$ pip install mpi4py
~~~

プログラムは以下の通りです。

```python
from mpi4py import MPI

size = MPI.COMM_WORLD.Get_size()
rank = MPI.COMM_WORLD.Get_rank()
name = MPI.Get_processor_name()
print(f"Hello, I'm process {rank} of {size} on {name}")
```

これを実行するには、`mpirun`でPython自体を実行ファイルとして指定します。

```shell
$ mpirun --map-by core -H node10,node11,node12,node13 python3 hello.py
Hello, I'm process 3 of 4 on node13
Hello, I'm process 0 of 4 on node10
Hello, I'm process 2 of 4 on node12
Hello, I'm process 1 of 4 on node11
```

## pi_chudnovsky.py

Chudnovskyのアルゴリズムを用いて円周率を計算します。

以下のPythonモジュールをあらかじめインストースしてください。

* mpi4py
* gmpy2
* NumPy

また円周率の計算結果の検証のため、以下のサイトから10億桁分の円周率のデータを入手します。

https://tstcl.jp/ja/randd/pi.php

ここでダウンロードしたZIPファイルを展開してできる`pi-10oku.txt`ファイルを`pi_chudnovsky.py`と同じディレクトリに置きます。

そして`mpirun`で実行します。

```shell
$ mpirun --map-by core -H node10,node11,node12,node13 python3 pi_chudnovsky.py 10 ./pi-10oku.txt
calculating...
checking...
time = 0.03 sec.
match = 14335
```

1つめの引き数として整数を指定します。この整数をnとすると14×2^n桁数の円周率を求めることを意味します。たとえばn=10の場合は14×2^10=14336となります。また2つめの引き数で、正しい円周率をテキスト形式で保存したファイルを指定します。

プログラムを実行すると実行時間と、円周率ファイルとマッチした小数点以下の桁数を表示します。上記の例の場合は、0.03秒で14335桁の円周率がマッチしたことを意味します。