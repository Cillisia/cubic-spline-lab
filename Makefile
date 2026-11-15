CC = gcc
CFLAGS = -O3 -std=c11 -Wall -Wextra
all: bin/spline_pthreads bin/spline_openmp bin/spline_mpi
bin:
	mkdir -p bin
bin/spline_pthreads: src/spline.c | bin
	$(CC) $(CFLAGS) $< -pthread -lm -o $@
bin/spline_openmp: src/spline.c | bin
	$(CC) $(CFLAGS) -DUSE_OMP $< -fopenmp -pthread -lm -o $@
bin/spline_mpi: src/spline.c | bin
	mpicc $(CFLAGS) -DUSE_MPI $< -pthread -lm -o $@
