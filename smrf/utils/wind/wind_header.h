
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

//extern float SLOPE (int l, int m, int xcoords[], int ycoords[], int elevs[], int height);

extern int find_line(int start_x, int start_y, int end_x, int end_y,
		int nx, int ny, int xcoords[], int ycoords[]);
