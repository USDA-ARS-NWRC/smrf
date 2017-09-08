#include <stdio.h>
#include <stdlib.h>
//#include <malloc/malloc.h>

/*
 *    vector.c
 *
 *    David Garen  8/89
 *
 *    Allocate a double vector with n elements.
 *
 *    This program is a modified version of one from:
 *    William H. Press, Brian P. Flannery, Saul A. Teukolsky, and William T.
 *    Vetterling, Numerical Recipes in C:  The Art of Scientific Computing,
 *    Cambridge University Press, 1988, p. 705.
 *
 */

double *vector(int n)
//int n;
{
   double *v = (double *) NULL;

   if (n > 0)
      v = (double *) malloc(n * sizeof(double));
   if (!v) {
      printf("\n\nAllocation failure in vector().\n");
      exit(0);
   }
   return(v);
}

/*
 *    dvector.c
 *
 *    David Garen  8/89
 *
 *    Allocate a double vector with n elements.
 *
 *    This program is a modified version of one from:
 *    William H. Press, Brian P. Flannery, Saul A. Teukolsky, and William T.
 *    Vetterling, Numerical Recipes in C:  The Art of Scientific Computing,
 *    Cambridge University Press, 1988, p. 706.
 */

double *dvector(int n)
{
   double *v = (double *) NULL;

   if (n > 0)
      v = (double *) malloc(n * sizeof(double));
   if (!v) {
      printf("\n\nAllocation failure in dvector().\n");
      exit(0);
   }
   return(v);
}

/*
 *    ivector.c
 *
 *    David Garen  8/89
 *
 *    Allocate an integer vector with n elements.
 *
 *    This program is a modified version of one from:
 *    William H. Press, Brian P. Flannery, Saul A. Teukolsky, and William T.
 *    Vetterling, Numerical Recipes in C:  The Art of Scientific Computing,
 *    Cambridge University Press, 1988, p. 706.
 */

int *ivector(int n)
{
   int *v = (int *) NULL;

   if (n > 0)
      v = (int *) malloc(n * sizeof(int));
   if (!v) {
      printf("\n\nAllocation failure in ivector().\n");
      exit(0);
   }
   return(v);
}

/*
 *    matrix.c
 *
 *    David Garen  8/89
 *
 *    Allocate a double matrix with nr rows and nc columns.
 *
 *    This program is a modified version of one from:
 *    William H. Press, Brian P. Flannery, Saul A. Teukolsky, and William T.
 *    Vetterling, Numerical Recipes in C:  The Art of Scientific Computing,
 *    Cambridge University Press, 1988, p. 706.
 */

double **matrix(int nr, int nc)
{
   int i;
   double **m = (double **) NULL;

   /* Allocate pointers to rows */

   if (nr > 0)
      m = (double **) malloc(nr * sizeof(double *));
   if (!m) {
      printf("\n\nAllocation failure 1 in matrix()\n");
      exit(0);
   }

   /* Allocate rows and set pointers to them */

   for (i = 0; i < nr; i++) {
      m[i] = (double *) NULL;
      if (nc > 0)
         m[i] = (double *) malloc(nc * sizeof(double));
      if (!m[i]) {
         printf("\n\nAllocation failure 2 in matrix()\n");
         exit(0);
      }
   }

   /* Return pointer to array of pointers to rows */

   return(m);
}

/*
 *    dmatrix.c
 *
 *    David Garen  8/89
 *
 *    Allocate a double matrix with nr rows and nc columns.
 *
 *    This program is a modified version of one from:
 *    William H. Press, Brian P. Flannery, Saul A. Teukolsky, and William T.
 *    Vetterling, Numerical Recipes in C:  The Art of Scientific Computing,
 *    Cambridge University Press, 1988, p. 706.
 */

double **dmatrix(int nr, int nc)
{
   int i;
   double **m = (double **) NULL;

   /* Allocate pointers to rows */

   if (nr > 0)
      m = (double **) malloc(nr * sizeof(double *));
   if (!m) {
      printf("\n\nAllocation failure 1 in dmatrix()\n");
      exit(0);
   }

   /* Allocate rows and set pointers to them */

   for (i = 0; i < nr; i++) {
      m[i] = (double *) NULL;
      if (nc > 0)
         m[i] = (double *) malloc(nc * sizeof(double));
      if (!m[i]) {
         printf("\n\nAllocation failure 2 in dmatrix()\n");
         exit(0);
      }
   }

   /* Return pointer to array of pointers to rows */

   return(m);
}

/*
 *    imatrix.c
 *
 *    David Garen  8/89
 *
 *    Allocate an integer matrix with nr rows and nc columns.
 *
 *    This program is a modified version of one from:
 *    William H. Press, Brian P. Flannery, Saul A. Teukolsky, and William T.
 *    Vetterling, Numerical Recipes in C:  The Art of Scientific Computing,
 *    Cambridge University Press, 1988, p. 707.
 */

int **imatrix(int nr, int nc)
{
   int i, **m = (int **) NULL;

   /* Allocate pointers to rows */

   if (nr > 0)
      m = (int **) malloc(nr * sizeof(int *));
   if (!m) {
      printf("\n\nAllocation failure 1 in imatrix()\n");
      exit(0);
   }

   /* Allocate rows and set pointers to them */

   for (i = 0; i < nr; i++) {
      m[i] = (int *) NULL;
      if (nc > 0)
         m[i] = (int *) malloc(nc * sizeof(int));
      if (!m[i]) {
         printf("\n\nAllocation failure 2 in imatrix()\n");
         exit(0);
      }
   }

   /* Return pointer to array of pointers to rows */

   return(m);
}

/*
 *    cube.c
 *
 *    David Garen  12/93
 *
 *    Allocate a double 3-D matrix with nr rows, nc columns,
 *    and nd elements deep.
 */

double ***cube(int nr, int nc, int nd)
{
   int i, j;
   double ***m = (double ***) NULL;

   if (nr > 0)
      m = (double ***) malloc(nr * sizeof(double **));
   if (!m) {
      printf("\n\nAllocation failure 1 in cube()\n");
      exit(0);
   }

   for (i = 0; i < nr; i++) {
      m[i] = (double **) NULL;
      if (nc > 0)
         m[i] = (double **) malloc(nc * sizeof(double *));
      if (!m[i]) {
         printf("\n\nAllocation failure 2 in cube()\n");
         exit(0);
      }
   }

   for (i = 0; i < nr; i++) {
      for (j = 0; j < nc; j++) {
         m[i][j] = (double *) NULL;
         if (nd > 0)
            m[i][j] = (double *) malloc(nd * sizeof(double));
         if (!m[i][j]) {
            printf("\n\nAllocation failure 3 in cube()\n");
            exit(0);
         }
      }
   }

   return(m);
}
