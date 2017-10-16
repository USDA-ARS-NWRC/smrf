/*
 *    krige.c
 *
 *    David Garen   8/91, 3/94
 *
 *    Calculate kriging weights
 *
 *    26 May 2000:
 *    Change solution method to LU decomposition
 *
 *    Feb 2016:
 *    - Create new function krige_grid to calculate the kriging weights
 *    	on a grid. This is meant to be called from a Python function
 *    - Everything else is the same except the 2D arrays must now be indexed
 *    	with linear indexing
 *
 */

#include <stdio.h>
#include <stdlib.h>
//#include <malloc/malloc.h>
#include <omp.h>

#include "dk_header.h"



void krige_grid(nsta, ngrid, ad, dgrid, elevations, nthreads, weights)
int nsta;					/* number of stations used */
int ngrid;					/* number of grid cells*/
double *ad;                      /* matrix of distances between prec/temp
                                    stations for computing kriging weights */
double *dgrid;                   /* array of distances between grid cells
                                    and prec/temp stations */
double *elevations;				 /* vector of station elevations */
int nthreads;				/* number of threads for parrallel processing */
double *weights;			/* output weights */
//int nthreads;					/* number of threads to use */
{

	double w[nsta+1];			/* kriging weights */
	int i, j;

	/* Calculate kriging weights using all stations */
	omp_set_dynamic(0);     // Explicitly disable dynamic teams
	omp_set_num_threads(nthreads); // Use N threads for all consecutive parallel regions

#pragma omp parallel shared(nsta, ad, dgrid, elevations, weights) private(i, j, w)
	{
#pragma omp for
		for (i = 0; i < ngrid; i++) {

			krige(nsta, ad, &dgrid[i*nsta], elevations, w);

			for (j = 0; j < nsta; j++){
				weights[i*nsta + j] = w[j];
			}
		}
	}

	//	return wall;
}



void krige(nsta, ad, dgrid, elevations, w)
int nsta;                          /* number of stations used */
double *ad;                      /* matrix of distances between prec/temp
                                    stations for computing kriging weights */
double *dgrid;                   /* array of distances between grid cells
                                    and prec/temp stations */
double *elevations;				 /* vector of station elevations */
double *w;						/* kriging weights */
{
	double elevsave;               /* stored value of station elevation */
	int m, mm, n, nn, i, j;             /* loop indexes */
	int msave;                    /* stored value of m index */
	int nsp1;                     /* ns plus 1 */
	double *wcalc;                /* calculation vector for weights */
	int ns;					 	 /* number of stations */
	int luret;                    /* return value from lusolv() */
	int *staflg;				 	 /* station use flags*/
	double temp;						 /* temporary variable */
	int itemp;						 /* temporary variable */
	double *dist;					 /* sorted distance */
	int *idx;					 /* index sorted distance */
	double **a;                   /* data matrix for solving for kriging
                                       weights (input to m_inv()) */
//	double *w;                    /* kriging weights */
//	double w[nsta+1];

	//   nsta = ns;

	// find the N closest stations
	dist = vector(nsta);
	idx = ivector(nsta);
	for (i = 0; i < nsta; ++i){
		dist[i] = dgrid[i];
		idx[i] = i;
	}
	for (i = 0; i < nsta; ++i){
		for (j = i + 1; j < nsta; ++j){
			if (dist[i] > dist[j]) {
				// sort the distance
				temp = dist[i];
				dist[i] = dist[j];
				dist[j] = temp;

				// re-sort the index
				itemp = idx[i];
				idx[i] = idx[j];
				idx[j] = itemp;
			}
		}
	}

	// set station use flags
	ns = 0;
	staflg = ivector(nsta);
	for (m = 0; m < nsta; m++) {
		staflg[idx[m]] = 1;
		ns++;
	}
	//   for (i = 0; i < nsta; ++i){
	//	   printf("%f - %i - %i\n",dist[i],idx[i],staflg[i]);
	//   }
	//   exit(0);

	a = dmatrix(nsta+1, nsta+2);
//	w = dvector(nsta+1);


	wcalc = dvector(nsta+1);
	while (1) {
		nsp1 = ns + 1;

		/* Load matrix for calculating kriging weights using only
         the desired stations (staflg = 1) */

		mm = -1;
		for (m = 0; m < nsta; m++) {
			if (staflg[m] == 1) {
				mm++;
				nn = -1;
				for (n = 0; n < nsta; n++) {
					if (staflg[n] == 1) {
						nn++;
						a[mm][nn] = ad[m*nsta + n];
					}
				}
				a[mm][ns] = a[ns][mm] = 1;
				a[mm][nsp1] = dgrid[m];
			}
		}
		a[ns][ns] = 0;
		a[ns][nsp1] = 1;
		n = nsp1;

		/* Solve linear system for kriging weights */

		if ((luret = lusolv(n, a, wcalc)) != 0) {
			printf("Error in lusolv()\n");
			exit(0);
		}

		/* Check for negative weights, throw out the most distant station by elevation with
         a negative weight, and recalculate weights until all are positive */

		elevsave = 0.0;
		mm = msave = -1;
		for (m = 0; m < nsta; m++) {
			if (staflg[m] == 1) {
				mm++;
				if (wcalc[mm] < 0.0) {
					if (elevations[m] > elevsave) {
						msave = m;
						elevsave = elevations[m];
					}
				}
			}
		}
		if (msave >= 0) {
			staflg[msave] = 0; // set station use flag to zero for furthest station
			ns--;
		}
		else {
			mm = -1;
			for (m = 0; m < nsta; m++) {
				if (staflg[m] == 1) {
					mm++;
					w[m] = wcalc[mm];
				}
				else
					w[m] = 0.0;
			}
			break;
		}
	}

//	free(wcalc);

	/* clean up 1D arrays*/
	free(dist);
	free(idx);
	free(staflg);
	free(wcalc);

	/* clean up 2D arrays*/
	for (m = 0; m < nsta+1; m++) {
		free(a[m]);
	}
	free(a);


//	return w;
}
