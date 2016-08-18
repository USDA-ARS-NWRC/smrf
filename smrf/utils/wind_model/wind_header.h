
//typedef struct {
//	int *data;
//	size_t used;
//	size_t size;
//} Array;


extern void calc_maxus(int nx, int ny, double *x, double *y, double *z,
		double *X_start, double *Y_start, double *X_end, double *Y_end,
		double height, int nthreads, double *maxus);

extern double hord(int N, double *x, double *y, double *z, double height);

extern double slope (double x1, double y1, double z1, double x2, double y2, double z2, double height);

//extern void find_line(int start_x, int start_y, int end_x, int end_y,
//		Array *xcoords, Array *ycoords);
