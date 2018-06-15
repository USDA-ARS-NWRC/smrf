
#define ABS(x)			( (x) < 0 ? -(x) : (x) )

#define DBL_EPSILON 2.2204460492503131e-16

/* From topotherm.c */

void topotherm(int ngrid, double *ta, double *tw, double *z, double *skvfac, int nthreads, double *thermal);
double satw(double tk);
double sati(double tk);
double brutsaert(double ta, double lmba, double ea, double z, double pa);

/* from dewpt.c */
void dewpt(int ngrid, double *ea, int nthreads, double tol, double *dpt);
double dew_pointp(double e, double tol);
double	zerobr(double a, double b, double t);

/* from iwbt.c */
void iwbt(int ngrid, double *ta, double *td,	double *z, int nthreads, double tol,	double *tw);
double wetbulb(double	ta,	double dpt, double press, double tol);
