/*
 * Saturation function over ice and water
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <errno.h>
#include <omp.h>
#include "envphys_c.h"
#include "envphys.h"

// stephman boltzman constant
#define STEF_BOLTZ 5.6697e-8

extern int errno;


void topotherm(
		int ngrid,		/* number of grid points */
		double *ta,		/* air temperature */
		double *tw,		/* dew point temperature */
		double *z,		/* elevation */
		double *skvfac,	/* sky view factor */
		int nthreads,	/* number of threads for parrallel processing */
		double *thermal	/* thermal radiation (return) */
)
{
	int samp;
	double ta_p, tw_p, z_p, skvfac_p; // pixel values
	double ea;			/*	vapor pressure		*/
	double emiss;		/*	atmos. emiss.		*/
	double T0;			/*	Sea Level ta		*/
	double lw_in;		/*	lw irradiance		*/
	double press;		/*	air pressure		*/


	omp_set_dynamic(0);     // Explicitly disable dynamic teams
	omp_set_num_threads(nthreads); // Use N threads for all consecutive parallel regions

#pragma omp parallel shared(ngrid, ta, tw, z, skvfac) private(samp, ta_p, tw_p, z_p, skvfac_p, ea, emiss, T0, press, lw_in)
	{
#pragma omp for

		for (samp=0; samp < ngrid; samp++) {

			ta_p = ta[samp];
			tw_p = tw[samp];
			z_p = z[samp];
			skvfac_p = skvfac[samp];

			/* convert ta and tw from C to K */
			ta_p += FREEZE;
			tw_p += FREEZE;

			if(ta_p < 0 || tw_p < 0){
				printf("ta or tw < 0 at pixel %i", samp);
				exit(-1);
			}

			/*	calculate theoretical sea level	*/
			/*	atmospheric emissivity  */
			/*	from reference level ta, tw, and z */

			if(tw_p > ta_p) {
				tw_p = ta_p;
			}

			ea = sati(tw_p);
			emiss = brutsaert(ta_p,
					STD_LAPSE_M, ea,
					z_p, SEA_LEVEL);

			/*	calculate sea level air temp	*/

			T0 = ta_p - (z_p * STD_LAPSE_M);

			/*	adjust emiss for elev, terrain	*/
			/*	     veg, and cloud shading	*/

			press = HYSTAT(SEA_LEVEL, T0,
					STD_LAPSE, (z_p/1000.),
					GRAVITY, MOL_AIR);

			/* elevation correction */
			emiss *= press/SEA_LEVEL;

			/* terrain factor correction */
			emiss = (emiss * skvfac_p) + (1.0 - skvfac_p);

			/* check for emissivity > 1.0 */
			if (emiss > 1.0)
				emiss = 1.0;

			/*	calculate incoming lw rad	*/

			lw_in = emiss * STEF_BOLTZ *ta_p*ta_p*ta_p*ta_p;

			/* set output band */

			thermal[samp] = lw_in;

		}
	}

}


/*
 * Saturation vapor pressure over water
 */
double
satw(
		double tk)		/* air temperature (K)		*/
{
	double  x;
	double  l10;

	if (tk <= 0.) {
		printf("tk < 0 satw");
		exit(-1);
	}

	errno = 0;
	l10 = log(1.e1);

	x = -7.90298*(BOIL/tk-1.) + 5.02808*log(BOIL/tk)/l10 -
			1.3816e-7*(pow(1.e1,1.1344e1*(1.-tk/BOIL))-1.) +
			8.1328e-3*(pow(1.e1,-3.49149*(BOIL/tk-1.))-1.) +
			log(SEA_LEVEL)/l10;

	x = pow(1.e1,x);

	if (errno) {
		perror("satw: bad return from log or pow");
	}

	return(x);
}


/*
 * Saturation vapor pressure over ice
 */
double
sati(
		double tk)		/* air temperature (K)	*/
{
	double  l10;
	double  x;

	if (tk <= 0.) {
		printf("tk < 0 satw");
		exit(-1);
	}

	if (tk > FREEZE) {
		x = satw(tk);
		return(x);
	}

	errno = 0;
	l10 = log(1.e1);

	x = pow(1.e1,-9.09718*((FREEZE/tk)-1.) - 3.56654*log(FREEZE/tk)/l10 +
			8.76793e-1*(1.-(tk/FREEZE)) + log(6.1071)/l10);

	if (errno) {
		perror("sati: bad return from log or pow");
	}

	return(x*1.e2);
}


/*
 * calculates atmospheric emissivity using a modified form of the equations by W. Brutsaert
 */
double
brutsaert(
		double   ta,		/* air temp (K)				*/
		double   lmba,		/* temperature lapse rate (deg/m)	*/
		double   ea,		/* vapor pressure (Pa)			*/
		double   z,			/* elevation (z)			*/
		double   pa)		/* air pressure (Pa)			*/
{
	double 	t_prime;
	double 	rh;
	double 	e_prime;
	double 	air_emiss;

	t_prime = ta - (lmba * z);
	rh = ea / sati(ta);
	if (rh > 1.0) {
		rh = 1.0;
	}
	e_prime = (rh * sati(t_prime))/100.0;
	/*	e_prime = rh * sati(t_prime);	*/

	air_emiss = (1.24*pow((e_prime/t_prime), 1./7.))*pa/SEA_LEVEL;
	/* "if" statement below is new */
	if (air_emiss > 1.0) {
		air_emiss = 1.0;
	}

	return(air_emiss);
}
