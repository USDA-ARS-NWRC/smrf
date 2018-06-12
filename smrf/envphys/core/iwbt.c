/*
 **
 ** NAME
 ** 	iwbt -- compute wet or icebult from air and dewpoint temperatures
 **
 ** SYNOPSIS
 **
 **	void iwbt (fdi, fdm, fdo)
 **	int fdi, fdm, fdo;
 **
 ** DESCRIPTION
 ** 	iwbt reads a three-band image of air and dewpoint temperature and
 **	elevation and computes wetbulb temperature;
 **	Elevation is used to compute pressure using the hydrostatic equation
 **	air and dewpoint temperature, and air pressure are used to compute
 **	wet or ice bult temperature using the psychrometric constant, its
 **	value at specific temperatures using the Clausius-Clapeyron equation
 **	solving for Tw or Ti using the Newton-Raphson iterative approximation;
 **	Returns Tw or Ti, to the given output image;
 **	Works at all temperatures (accounting for both fusion and vaporization).
 **
 */

// #include "ipw.h"
// #include "envphys.h"
// #include "pgm.h"
// #include "fpio.h"
// #include "bih.h"
// #include "pixio.h"


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <errno.h>
#include <omp.h>
#include "envphys_c.h"
#include "envphys.h"

#define RH2O 461.5		/* Gas constant for water vapor (J/kg/K) */
#define EPS (MOL_H2O/MOL_AIR)	/* Ratio of moleculr weights of water and dry air */
#define CONVERGE 0.0001		/* Convergence value */

double wetbulb(
	double	ta,	/* air tempterature (K) */
	double	dpt,	/* dewpoint temperature (K) */
	double	press)	/* total air pressure (Pa)  */
{
	int	i;
	double	ea;	/* vapor pressure (Pa) */
	double	esat;	/* saturation ea @ Ta (Pa) */
	double	xlh;	/* latent heat of vaporization + fusion (sublimation) (J/kg) */
	double	xlhv;	/* latent heat of vaporization *(J/kg) */
	double	xlhf;	/* latent heat of fusion *(J/kg) */
	double	fu_fac;	/* fudge factor for xlh stradeling 0 */
	double	psyc;	/* Psychrometric "constant" (K/Pa) */
	double	dedt;	/* Change in ea with temperature (Pa/K) */
	double	pf;	/* Psychrometer value (K) */
	double	dpdt;	/* Change in pf with temperature */
	double	ti;	/* wet or ice bulb temperature (K) */
	double	ti0;	/* initial value for ti */
	double	dti;	/* closure value */

	/* find latent heat of vaporization, or vaporization + fusion */
	if (ta <= FREEZE) {
		xlhv = LH_VAP((ta + dpt) / 2.0);
		xlhf = LH_FUS((ta + dpt) / 2.0);
		xlh  = xlhv + xlhf;
	}
	else if (dpt <= FREEZE) {
		xlhv = LH_VAP((ta + dpt) / 2.0);
		xlhf = LH_FUS((FREEZE + dpt) / 2.0);
		fu_fac = ((FREEZE - dpt) / (ta - dpt));
		xlh  = xlhv + (fu_fac * xlhf);
	}
	else
		xlh = LH_VAP((ta+dpt)/2);

	/* vapor pressure and saturation vapor pressure at ta */
	ea = sati(dpt);
	esat = sati(ta);

	/* Psychrometric "constant" (K/Pa) */
	psyc = EPS * (xlh / (CP_AIR * press));

	/* solve for wet or ice bulb temperature */
	dti = 1.0;
	i = 0;
	ti = ta;
	while (dti > CONVERGE) {
		ti0 = ti;
		if (ti != ta)
			esat = sati(ti);
		dedt = xlh * (esat / (RH2O * (ti*ti)));
		pf = (ti - ta) + (psyc * (esat - ea));
		dpdt = 1.0 + (psyc * dedt);
		ti = ti - (pf / dpdt);
		dti = ti0 - ti;
		i++;
		if (i > 10)
			error("failure to converge in 10 iterations");
	}
	return(ti);
}

//Function to calculate the wet bult temeprature of the whole image
void iwbt (
		int ngrid,		/* number of grid points */
		double *ta,		/* air temperature */
		double *td,		/* dew point temperature */
		double *z,		/* elevation */
		int nthreads,	/* number of threads for parrallel processing */
		double *tw		/* wet bulb temperature (return) */
{
	int samp;
	double		td_p;		/* dew point temperature (C)	*/
	double		tw_p;		/* wet bulb temperature (C)	*/
	double		ta_p;		/* air temperature (C)		*/
	double		z_p;		/* elevation (m)		*/
	double		pa_p;		/* air pressure (pa)		*/

	omp_set_dynamic(0);     // Explicitly disable dynamic teams
	omp_set_num_threads(nthreads); // Use N threads for all consecutive parallel regions

#pragma omp parallel shared(ngrid, ta, tw, z, skvfac) private(samp, ta_p, tw_p, z_p, skvfac_p, ea, emiss, T0, press, lw_in)
	{
#pragma omp for

		for (samp=0; samp < ngrid; samp++) {

			// get pixel values
			ta_p = ta[samp];
			td_p = td[samp];
			z_p = z[samp];

			/*	set pa	*/
			if (z_p == 0.0) {
				pa_p = SEA_LEVEL;
			}
			else {
				pa_p = HYSTAT (SEA_LEVEL, STD_AIRTMP, STD_LAPSE,
							(z_p / 1000.0), GRAVITY, MOL_AIR);
			}

			/*	convert ta & td to Kelvin	*/
			ta_p += FREEZE;
			td_p += FREEZE;

			if(ta_p < 0 || td_p < 0){
				printf("ta or td < 0 at pixel %i", samp);
				exit(-1);
			}

			/*	call wetbulb function & fill output buffer	*/
			tw_p = wetbulb(ta, td, pa);

			if(tw_p < 0){
				printf("tw < 0 at pixel %i", samp);
				exit(-1);
			}
			
			// put back in array
			tw[samp] = tw_p - FREEZE
			}
		}

}
