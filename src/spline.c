#define _XOPEN_SOURCE 700
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <pthread.h>
#ifdef USE_OMP
#include <omp.h>
#endif
#ifdef USE_MPI
#include <mpi.h>
#endif
static int n, workers=1, rank_id=0;
static double *x,*y,*buf[2],*m,*coef;
static pthread_barrier_t barrier;
static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec+1e-9*t.tv_nsec;
}
static void *alloc(size_t z) {
    void *p=calloc(z,1);
    if(!p) {
        fprintf(stderr,"Out of memory\n");
        exit(2);
    }
    return p;
}
static void stage(int i,int stride,double *old,double *out) {
    double *r=old+4*i,*v=out+4*i;
    v[0]=v[2]=0;
    v[1]=r[1];
    v[3]=r[3];
    if(i>=stride) {
        double *q=old+4*(i-stride),f=-r[0]/q[1];
        v[0]=f*q[0];
        v[1]+=f*q[2];
        v[3]+=f*q[3];
    }
    if(i+stride<n) {
        double *q=old+4*(i+stride),f=-r[2]/q[1];
        v[2]=f*q[2];
        v[1]+=f*q[0];
        v[3]+=f*q[3];
    }
}
static void coefficients(int i) {
    double h=x[i+1]-x[i];
    coef[4*i]=y[i];
    coef[4*i+1]=(y[i+1]-y[i])/h-h*(2*m[i]+m[i+1])/6;
    coef[4*i+2]=m[i]/2;
    coef[4*i+3]=(m[i+1]-m[i])/(6*h);
}
static void *thread_run(void *arg) {
    int id=*(int*)arg,cur=0;
    for(int s=1; s<n; s*=2) {
        for(int i=id; i<n; i+=workers)stage(i,s,buf[cur],buf[1-cur]);
        pthread_barrier_wait(&barrier);
        cur=1-cur;
    }
    for(int i=id; i<n; i+=workers)m[i]=buf[cur][4*i+3]/buf[cur][4*i+1];
    pthread_barrier_wait(&barrier);
    for(int i=id; i<n-1; i+=workers)coefficients(i);
    return NULL;
}
static void solve(void) {
#ifdef USE_MPI
    int *cnt=alloc(workers*sizeof(int)),*off=alloc(workers*sizeof(int));
    for(int p=0; p<workers; p++) {
        off[p]=4*(int)((long long)n*p/workers);
        cnt[p]=4*(int)((long long)n*(p+1)/workers)-off[p];
    }
    int lo=off[rank_id]/4,hi=lo+cnt[rank_id]/4,cur=0;
    for(int s=1; s<n; s*=2) {
        for(int i=lo; i<hi; i++)stage(i,s,buf[cur],buf[1-cur]);
        MPI_Allgatherv(MPI_IN_PLACE,0,MPI_DOUBLE,buf[1-cur],cnt,off,MPI_DOUBLE,MPI_COMM_WORLD);
        cur=1-cur;
    }
    for(int i=lo; i<hi; i++)m[i]=buf[cur][4*i+3]/buf[cur][4*i+1];
    for(int p=0; p<workers; p++) {
        cnt[p]/=4;
        off[p]/=4;
    }
    MPI_Allgatherv(MPI_IN_PLACE,0,MPI_DOUBLE,m,cnt,off,MPI_DOUBLE,MPI_COMM_WORLD);
    for(int i=lo; i<hi && i<n-1; i++)coefficients(i);
    for(int p=0; p<workers; p++) {
        int a=(int)((long long)n*p/workers),b=(int)((long long)n*(p+1)/workers);
        if(a>n-1)a=n-1;
        if(b>n-1)b=n-1;
        off[p]=4*a;
        cnt[p]=4*(b-a);
    }
    MPI_Allgatherv(MPI_IN_PLACE,0,MPI_DOUBLE,coef,cnt,off,MPI_DOUBLE,MPI_COMM_WORLD);
    free(cnt);
    free(off);
#elif defined(USE_OMP)
    int cur=0;
#pragma omp parallel num_threads(workers) shared(cur)
    {
        for(int s=1; s<n; s*=2) {
#pragma omp for schedule(static)
            for(int i=0; i<n; i++)stage(i,s,buf[cur],buf[1-cur]);
#pragma omp single
            cur=1-cur;
        }
#pragma omp for schedule(static)
        for(int i=0; i<n; i++)m[i]=buf[cur][4*i+3]/buf[cur][4*i+1];
#pragma omp for schedule(static)
        for(int i=0; i<n-1; i++)coefficients(i);
    }
#else
    pthread_t *t=alloc(workers*sizeof(*t));
    int *ids=alloc(workers*sizeof(int));
    pthread_barrier_init(&barrier,NULL,workers);
    for(int p=0; p<workers; p++) {
        ids[p]=p;
        if(pthread_create(t+p,NULL,thread_run,ids+p)) {
            fprintf(stderr,"pthread_create failed\n");
            exit(2);
        }
    }
    for(int p=0; p<workers; p++)pthread_join(t[p],NULL);
    pthread_barrier_destroy(&barrier);
    free(t);
    free(ids);
#endif
}
int main(int argc,char **argv) {
#ifdef USE_MPI
    MPI_Init(&argc,&argv);
    MPI_Comm_rank(MPI_COMM_WORLD,&rank_id);
    MPI_Comm_size(MPI_COMM_WORLD,&workers);
#endif
    if(argc<4) {
        fprintf(stderr,"Usage: executable input.txt workers output.txt [repeats]\n");
        return 2;
    }
#ifndef USE_MPI
    workers=atoi(argv[2]);
#endif
    int repeats=argc>4?atoi(argv[4]):1;
    if(workers<1||repeats<1)return 2;
    FILE *f=fopen(argv[1],"r");
    if(!f) {
        perror(argv[1]);
        return 2;
    }
    if(fscanf(f,"%d",&n)!=1||n<2||n>100000000)return 2;
    x=alloc(n*sizeof(double));
    y=alloc(n*sizeof(double));
    m=alloc(n*sizeof(double));
    coef=alloc(4*(size_t)(n-1)*sizeof(double));
    buf[0]=alloc(4*(size_t)n*sizeof(double));
    buf[1]=alloc(4*(size_t)n*sizeof(double));
    for(int i=0; i<n; i++)if(fscanf(f,"%lf %lf",x+i,y+i)!=2||!isfinite(x[i])||!isfinite(y[i])||(i&&x[i]<=x[i-1])) {
        fprintf(stderr,"Invalid nodes\n");
        return 2;
    }
    fclose(f);
    double best=1e300;
    for(int rep=0; rep<repeats; rep++) {
        for(int i=0; i<n; i++) {
            double *r=buf[0]+4*i;
            r[0]=r[2]=r[3]=0;
            r[1]=1;
            if(i>0&&i<n-1) {
                double h=x[i]-x[i-1],k=x[i+1]-x[i];
                r[0]=h;
                r[1]=2*(h+k);
                r[2]=k;
                r[3]=6*((y[i+1]-y[i])/k-(y[i]-y[i-1])/h);
            }
        }
#ifdef USE_MPI
        MPI_Barrier(MPI_COMM_WORLD);
#endif
        double start=now();
        solve();
        double elapsed=now()-start;
#ifdef USE_MPI
        double mx;
        MPI_Allreduce(&elapsed,&mx,1,MPI_DOUBLE,MPI_MAX,MPI_COMM_WORLD);
        elapsed=mx;
#endif
        if(elapsed<best)best=elapsed;
    }
    if(!rank_id) {
        f=fopen(argv[3],"w");
        if(!f) {
            perror(argv[3]);
            return 2;
        }
        for(int i=0; i<n-1; i++)fprintf(f,"%.17g %.17g %.17g %.17g\n",coef[4*i],coef[4*i+1],coef[4*i+2],coef[4*i+3]);
        fclose(f);
#ifdef USE_MPI
        const char *name="c_mpi";
#elif defined(USE_OMP)
        const char *name="openmp";
#else
        const char *name="pthreads";
#endif
        printf("%s,%d,%d,%.9g\n",name,n,workers,best);
    }
    free(x);
    free(y);
    free(m);
    free(coef);
    free(buf[0]);
    free(buf[1]);
#ifdef USE_MPI
    MPI_Finalize();
#endif
    return 0;
}
