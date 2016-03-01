

// from array.c
extern double *vector(int n);
extern double *dvector(int n);
extern int *ivector(int n);
extern double **matrix(int nr, int nc);
extern double **dmatrix(int nr, int nc);
extern int **imatrix(int nr, int nc);
extern double ***cube(int nr, int nc, int nd);



// from lusolv.c
extern int lusolv(int n, double **a, double *x);
extern int ludcmp(double **a, int n, int *indx, double *d);
extern void lubksb(double **a, int n, int *indx);



// from krige.c
extern void krige(int nsta, double *ad, double *dgrid, double *elevations, double *w);
extern void krige_grid(int nsta, int ngrid, double *ad, double *dgrid, double *elevations, int nthreads, double *weights);
