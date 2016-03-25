/* From topotherm.c */

void topotherm(int ngrid, double *ta, double *tw, double *z, double *skvfac, int nthreads, double *thermal);
double satw(double tk);
double sati(double tk);
double brutsaert(double ta, double lmba, double ea, double z, double pa);
