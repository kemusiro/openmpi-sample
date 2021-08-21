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

