#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <omp.h>
#include "breshen.h"
#include "wind_header.h"

#define MAX_SIZE 500
#define PI 3.141592654

/* ------------------------------------------------------------------------- */
/*
 * Define an array struct that will dynamically allocate memory
 * http://stackoverflow.com/questions/3536153/c-dynamically-growing-array
 */
/*
typedef struct {
	int *data;
	size_t used;
	size_t size;
} Array;

void initArray(Array *a, size_t initialSize) {
	a->data = (int *)malloc(initialSize * sizeof(int));
	a->used = 0;
	a->size = initialSize;
}

void insertArray(Array *a, int element) {
	if (a->used == a->size) {
		a->size *= 2;
		a->data = (int *)realloc(a->data, a->size * sizeof(int));
	}
	a->data[a->used++] = element;
}

void freeArray(Array *a) {
	free(a->data);
	a->data = NULL;
	a->used = a->size = 0;
}
 */



void calc_maxus(nx, ny, x, y, z, X_start, Y_start, X_end, Y_end, height, nthreads, maxus)
int nx;						/* number of grid cells x dir*/
int ny;						/* number of grid cells y dir*/
double *x;					/* X coordinates of the matrix */
double *y;					/* Y coordinates of the matrix */
double *z;					/* Z (elevation) of the matrix */
double *X_start;			/* matrix of start point indicies */
double *Y_start;			/* matrix of start point indicies */
double *X_end;				/* matrix of start point indicies */
double *Y_end;				/* matrix of start point indicies */
double height;				/* instrument height */
int nthreads;				/* number of threads for parrallel processing */
double *maxus;				/* output maxus */
{

	int i, j, ngrid, line_length;
	int start_x, start_y, end_x, end_y;
	int xcoords[MAX_SIZE], ycoords[MAX_SIZE];
	double mxs;

	ngrid = nx * ny;

	omp_set_dynamic(100);			// give 100 cells to each processor at a time
	omp_set_num_threads(nthreads); // Use N threads for all consecutive parallel regions

#pragma omp parallel shared(nx, ny, x, y, z, X_start, Y_start, X_end, Y_end, height, maxus) \
		private(i, j, start_x, start_y, end_x, end_y, xcoords, ycoords, line_length, mxs)
	{
#pragma omp for

		for (i = 0; i < ngrid; i++) {

			// Determine the start and end points
			start_x = X_start[i];
			start_y = Y_start[i];
			end_x = X_end[i];
			end_y = Y_end[i];

//			int dx, dy;
//			dy = 31;
//			dx = 4980;
//			if (start_x == dx && start_y == dy) {
//				printf("x=%i, y=%i\n", start_x, start_y);
//				printf("x=%i, y=%i\n", end_x, end_y);
//			}

			// determine the points along the line
			line_length = find_line(start_x, start_y, end_x, end_y, nx, ny, xcoords, ycoords);

			// determine the elevations along the line
			double xl[line_length], yl[line_length], elev[line_length];
			int n = 0;
			for (j = 0; j < line_length; j++) {
				// check to ensure that the points are within the modeling domain
				if (xcoords[j] >= 0 && xcoords[j] <= nx-1 && ycoords[j] >= 0 && ycoords[j] <= ny-1){
					xl[j] = x[xcoords[j]];
					yl[j] = y[ycoords[j]];
					elev[j] = z[ycoords[j]*nx + xcoords[j]];

//					if (start_x == dx && start_y == dy) {
//						printf("%f\n", elev[j]);
//					}

					n++;
				}
			}


			// calculate the maximum upwind slope along the line
			maxus[i] = hord(n, xl, yl, elev, height);


//			if (start_x == dx && start_y == dy) {
//				printf("%f\n", maxus[i]);
//			}

		}
	}

}





/* ------------------------------------------------------------------------- */
int find_line(start_x, start_y, end_x, end_y, nx, ny, xcoords, ycoords)
int start_x;		/* start x coordinate */
int start_y;		/* start y coordinate */
int end_x;			/* end x coordinate */
int end_y;			/* end y coordinate */
int nx;				/* number of points in x coordinates */
int ny;				/* number of points in y coordinates */
int xcoords[];		/* array of x coordinates */
int ycoords[];		/* array of y coordinates */
{
	int N;
	short *X, *Y, nextX, nextY;
	struct BreshenhamData *LineData, Initialize;


	// Initialize the bresham calculation
	nextY = (short) start_y;
	nextX = (short) start_x;
	X = &nextX;
	Y = &nextY;

	LineData = &Initialize;
	Initialize.SlopeType = 0;
	xcoords[0] = start_x;
	ycoords[0] = start_y;
	N = 1;



	while (((int)*X != end_x || (int)*Y != end_y) && N < MAX_SIZE)
	{
		// Check to see if the values are within the boundaries
		if (*X > nx || *X < 0 || *Y > ny || *Y < 0) {
			break;
		}
		GetNextCellCoordinate((short)start_x, (short)start_y, (short)end_x,\
				(short)end_y, X, Y, LineData);
		xcoords[N] = nextX;
		ycoords[N] = nextY;
		++N;
	}

	return N;

}



/* ------------------------------------------------------------------------- */
/*
 * Find the maximum upwind slope from the point using the methods developed
 * in hor1d described by Dozier 1981
 */

double hord(N, x, y, z, height)
int N;				/* line length */
double *x;			/* x coordinates along line */
double *y;			/* y coordinates along line */
double *z;			/* elevation along line */
double height;		/* instrument height */
{
	int i, j, found;
	int H[N]; // index to current points horizon
	double slope_ij, slope_hj;
	double hordeg;

	H[N - 1] = N - 1;
	i = N - 2;
	while ( i >= 0 )
	{
		j = i + 1;
		found = 0;
		while (found == 0)
		{
			slope_ij = slope(x[i], y[i], z[i], x[j], y[j], z[j], height);
			slope_hj = slope(x[j], y[j], z[j], x[H[j]], y[H[j]], z[H[j]], height);

			//			slope_ij = SLOPE(i, j, xcoords, ycoords, z, height);
			//			slope_hj = SLOPE(j, H[j], xcoords, ycoords, z, height);

			if (slope_ij < slope_hj)
			{
				if (j == N - 1)
				{
					found = 1;
					H[i] = j;
				}
				else
				{
					j = H[j];
				}
			}
			else
			{
				found = 1;
				if (slope_ij > slope_hj) {
					H[i] = j;
				} else {
					H[i] = H[j];
				}
			}
		}
		--i;
	}


	slope_hj = slope(x[0], y[0], z[0], x[H[0]], y[H[0]], z[H[0]], height);
	hordeg = atan(slope_hj) / PI * 180;
//	hordeg = H[0];
	return hordeg;


}

double slope (x1, y1, z1, x2, y2, z2, height)
double x1;			/* Point 1 x,y,z */
double y1;
double z1;
double x2;			/* Point 2 x,y,z */
double y2;
double z2;
double height;
{
	double rise, run;

	rise = z2 - ( height + z1 );
	run = sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));

	return (rise/run);
}


//float SLOPE (l, m, xcoords, ycoords, elevs, height)
//int l;
//int m;
//int xcoords[];
//int ycoords[];
//int elevs[];
//int height;
//{
//	int rise;
//	float run, slop, cellsize=30;
//
//	rise = elevs[m] - ( height + elevs[l] );
//	//	rise = 10;
//	//	run = 10.0;
//	run = sqrt((xcoords[l] - xcoords[m]) * (xcoords[l] - xcoords[m]) + \
//			(ycoords[l] - ycoords[m]) * (ycoords[l] - ycoords[m])) * cellsize;
//	slop = rise/run;
//	return slop;
//}



