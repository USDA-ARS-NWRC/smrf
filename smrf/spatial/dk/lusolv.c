/*
 *    lusolv.c
 *
 *    David Garen  5/2000
 *
 *    Solve a system of linear equations using the LU decomposition
 *    method.  Matrix inverse is not calculated, as in Gauss-Jordan
 *    method.  Returns zero for singular matrix (no solution).
 *
 *    Algorithms taken from:
 *    W. H. Press, B. P. Flannery, S. A. Teukolsky, and W. T. Vetterling
 *    (1988).  Numerical Recipes in C.  Cambridge University Press, pp. 43-44.
 *
 */

#include <stdlib.h>
//#include <malloc/malloc.h>
#include <math.h>
#include <stdio.h>

#include "dk_header.h"


/* #define TINY 1.0e-20; */

int lusolv(
	int n, 											/* number of rows and columns in matrix a */
	double **a, 								/* input matrix */
	double *x										/* vector of equation solutions */
)
{
	double d;                     /* +/- 1 for even or odd number of
                                   row interchanges */
	int i;                       /* looping index */
	int *indx;                   /* row permutation from pivoting */
//	void free();
	int ret;                     /* function return value */

	indx = ivector(n);

	if ((ret = ludcmp(a, n, indx, &d)) != 0)
		return(1);
	lubksb(a, n, indx);
	for (i = 0; i < n; i++)
		x[i] = a[i][n];
	free(indx);
	return(0);
}

/*
 *    ludcmp.c
 *
 *    Given an n X n matrix a, this routine replaces it by the LU decomposition
 *    of a rowwise permutation of itself.
 */

int ludcmp(
	double **a, 								/* input matrix */
	int n, 											/* number of rows and columns in matrix a */
	int *indx, 									/* row permutation from pivoting */
	double *d										/* +/- 1 for even or odd number of
																row interchanges */
)
{
	double big;                  /* largest array element */
	double dum;                  /* dummy variable */
//	double *dvector();           /* double vector space allocation function */
	int i, j, k;                 /* looping indexes */
	int imax;                    /* index of largest array element */
	double sum;                  /* summing variable */
	double temp;                 /* temporary variable */
	double *vv;                  /* implicit scaling information for a row */

	vv = dvector(n);
	*d = 1.0;

	/* Loop over rows to get the implicit scaling information */

	for (i = 0; i < n; i++) {
		big = 0.0;
		for (j = 0; j < n; j++)
			if ((temp = fabs(a[i][j])) > big)
				big = temp;

		/* No nonzero largest element -- singular matrix, no solution */

		if (big == 0.0)
			return(1);

		/* Otherwise, save the scaling */

		vv[i] = 1.0 / big;
	}

	/* Loop over columns (Crout's method) */

	for (j = 0; j < n; j++) {
		for (i = 0; i < j; i++) {
			sum = a[i][j];
			for (k = 0; k < i; k++)
				sum -= a[i][k] * a[k][j];
			a[i][j] = sum;
		}

		/* Search for largest pivot element */

		big = 0.0;
		for (i = j; i < n; i++) {
			sum = a[i][j];
			for (k = 0; k < j; k++)
				sum -= a[i][k] * a[k][j];
			a[i][j] = sum;
			if ((dum = vv[i] * fabs(sum)) >= big) {
				big = dum;
				imax = i;
			}
		}

		/* Interchange rows if necessary */

		if (j != imax) {
			for (k = 0; k < n; k++) {
				dum = a[imax][k];
				a[imax][k] = a[j][k];
				a[j][k] = dum;
			}
			*d = -(*d);
			vv[imax] = vv[j];
		}
		indx[j] = imax;

		/* If the pivot element is zero, the matrix is singular (at least
         to the precision of the algorithm) */

		if (a[j][j] == 0.0)
		{
			printf("Error: Singular matrix\n");
			
			return(1);

		}
		/* For some applications on singular matrices, it is desirable
            to substitute TINY for zero; this line is given in the book
            but is not used here:
         a[j][j] = TINY; */

		/* Divide by pivot element */

		if (j != n-1) {
			dum = 1.0 / a[j][j];
			for (i = j+1; i < n; i++)
				a[i][j] *= dum;
		}
	}
	free(vv);
	return(0);
}

/*
 *    lubksb.c
 *
 *    Solves a set of linear equations by forward- and backsubstitution.
 *    The input matrix a is an LU decomposition of the original matrix.
 *    The right-hand side vector is stored as an additional column in
 *    matrix a.
 */

void lubksb(
	double **a, 								/* input matrix */
	int n, 											/* number of rows and columns in matrix a */
	int *indx										/* row permutation from pivoting */
)
{
	int i, j;                    /* looping indexes */
	int ii = -1;                 /* index of first nonzero r.h.s. value */
	int ip;                      /* index value */
	double sum;                  /* summing variable */

	/* Forward substitution */

	for (i = 0; i < n; i++) {
		ip = indx[i];
		sum = a[ip][n];
		a[ip][n] = a[i][n];
		if (ii >= 0) {
			for (j = ii; j < i; j++)
				sum -= a[i][j] * a[j][n];
		}
		else if (sum > 0.0)
			ii = i;
		a[i][n] = sum;
	}

	/* Backsubstitution */

	for (i = n-1; i >= 0; i--) {
		sum = a[i][n];
		for (j = i+1; j < n; j++)
			sum -= a[i][j] * a[j][n];
		a[i][n] = sum / a[i][i];
	}
}
