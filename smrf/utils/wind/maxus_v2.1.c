#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include "grid_io.h"
#include "breshen.h"

#define TRUE 1
#define FALSE 0
#define PI 3.141592654
#define DISTANCE (double) (sqrt((endj-startj)*(endj-startj) +\
		(endi-starti)*(endi-starti))) * Dem->CellSize


int endi, endj;
double dmax;
Grid Dem, Adjdem;
int xcoords[500], ycoords[500], H[500];
double elevs[500];
double height;

void ENDPOINTS(starti, startj, deg_direction)
int starti, startj;
double deg_direction;
{
	double rad_direction;
	int tempj, tempi;
	float *FloatCell, elev;
	int gg, *IntCell, poti, potj, zz;

	FloatCell = &elev;
	IntCell = &gg;

	rad_direction = (deg_direction/180) * PI;
	endj = startj;
	tempj = startj;
	endi = starti;
	tempi = starti;
	Get_Cell_Value (starti + 1, startj + 1, Adjdem, IntCell, FloatCell);

	if (deg_direction > 0 && deg_direction <= 45)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempi = endi - 1;
			tempj = tempj + tan(rad_direction);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}

	}
	else if (deg_direction > 45 && deg_direction < 90)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempj = endj + 1;
			tempi = tempi - tan (PI / 2 - rad_direction);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}

		}
	}
	else if (deg_direction > 90 && deg_direction <= 135)
	{
		while (elev >= 0  && DISTANCE < dmax)
		{
			tempj = endj + 1;
			tempi = tempi + tan (rad_direction - PI / 2);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 135 && deg_direction < 180)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempi = endi + 1;
			tempj = tempj + tan (PI - rad_direction);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction > 180 && deg_direction <= 225)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempi = endi + 1;
			tempj = tempj - tan (rad_direction - PI);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction > 225 && deg_direction < 270)
	{
		while(elev >= 0 && DISTANCE < dmax)
		{
			tempj = endj - 1;
			tempi = tempi + tan (1.5 * PI - rad_direction);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 270 && deg_direction <= 315)
	{
		while(elev >= 0 && DISTANCE < dmax)
		{
			tempj = endj - 1;
			tempi = tempi - tan (rad_direction - 1.5 * PI);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 315 && deg_direction < 360)
	{
		while(elev >= 0 && DISTANCE < dmax)
		{
			tempi = endi - 1;
			tempj = tempj - tan (2 * PI - rad_direction);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction == 90)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempj += 1;
			Get_Cell_Value(tempi + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
				endj = tempj;
		}
	}
	else if (deg_direction == 180)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempi += 1;
			Get_Cell_Value(tempi + 1,tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
				endi = tempi;
		}
	}
	else if (deg_direction == 270)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempj -= 1;
			Get_Cell_Value(tempi + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
				endj = tempj;
		}
	}
	else if (deg_direction == 0 || deg_direction == 360)
	{
		while (elev >= 0 && DISTANCE < dmax)
		{
			tempi -= 1;
			Get_Cell_Value(tempi + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*FloatCell >= 0)
				endi = tempi;
		}
	}
}



double SLOPE (l,m,height)
int l;
int m;
double height;
{
	double rise;
	double run, slop;
	if (l == m)
	{
		slop = 0;
		goto slopend;
	}
	rise = elevs[m] - ( height + elevs[l] );
	run = sqrt((xcoords[l] - xcoords[m]) * (xcoords[l] - xcoords[m]) + \
			(ycoords[l] - ycoords[m]) * (ycoords[l] - ycoords[m])) * Dem->CellSize;
	slop = rise/run;
	slopend:    return (slop);
}


/* Much of this algorithm described in Dozier, 1981	*/
double HORD(starti, startj, endi, endj)
int startj, starti, endj, endi;
{
	int p, *IntCell, current_elevation, zz, i, j, N, found;
	float *FloatCell, elev;
	double run = 0, slope = -11.5, temp_slope = 0;
	double hordeg;
	short *X, *Y, nextX, nextY;
	struct BreshenhamData *LineData, Initialize;

	FloatCell = &elev;
	IntCell = &zz;
	nextY = (short) starti;
	nextX = (short) startj;
	X = &nextX;
	Y = &nextY;
	Get_Cell_Value(starti, startj, Dem, IntCell, FloatCell);

	LineData = &Initialize;
	Initialize.SlopeType = 0;
	xcoords[0] = startj;
	ycoords[0] = starti;
	elevs[0] = *FloatCell;
	if (starti == 1 && startj == 0) {
		printf("%f\n", elevs[0]);
	}

	N = 1;
	if (starti == endi && startj == endj)
	{
		hordeg = 0.0;
		goto end;
	}
	while (((int)*X != endj || (int)*Y != endi) && N < 500)
	{
		GetNextCellCoordinate((short)startj, (short)starti, (short)endj,\
				(short)endi, X, Y, LineData);
		Get_Cell_Value(nextY, nextX, Dem, IntCell, FloatCell);
		xcoords[N] = nextX;
		ycoords[N] = nextY;
		elevs[N] = *FloatCell;

		if (starti == 1 && startj == 0) {
			printf("%f\n", elevs[N]);
		}

		++N;
	}

	if ( N == 500 ) N = 499;
	H[N - 1] = N - 1;
	i = N - 2;
	while ( i >= 0 )
	{
		j = i + 1;
		found = 0;
		while (found == 0)
		{
			if (SLOPE (i,j,height) < SLOPE (j,H[j],height))
			{
				if (j == N - 1)
				{
					found = 1;
					H[i] = j;
				}
				else
					j = H[j];
			}
			else
			{
				found = 1;
				if (SLOPE(i,j,height) > SLOPE (j,H[j],height))
					H[i] = j;
				else
					H[i] = H[j];
			}
		}
		--i;
	}
	hordeg = atan(SLOPE(0,H[0],height)) / PI * 180;
	end:	return (hordeg);
}

main (int argc, char *argv[])
{
	int xl, xu, yl, yu, azim2, north_flag = 0;
	double azim1;
	int i, j, count, z, IntValue, row, col;
	int yULpix, xULpix, xlpix, xupix, ylpix, yupix;
	int l = 0, m = 0, arg_count = 0;
	int c, input_max;
	int *IntCell, yy;
//	int IntValue;
	int *Integer, caca;
	float *Float, caca2;
	float FloatValue, *FloatCell, xx;
	double accum_hor, index, hord, w, increment;
	Grid Hor;
	char output_file[50];
	char dem_file[50];

	FloatCell = &xx;
	IntCell = &yy;
	Float = &caca2;
	Integer = &caca;

	if (argc != 9)  {
		printf("\n\nUSAGE: maxus -a azimuth (integer) -z dmax (integer) -d dem file (elevations as integers) -h instrument height (int)\n\nPLEASE REPORT ANY BUGS/PROBLEMS TO ADAM WINSTRAL (adam.winstral@ars.usda.gov)\n\n");
		printf("Only supplied %d arguments; should be 9\n", argc);
		exit(0);
	}
	while (--argc > 1)  {
		if ((*++argv)[0] == '-')  {
			c = *++argv[0];
			switch (c) {
			case 'a':
				++arg_count;
				++argv;
				--argc;
				azim1 = atoi(*argv);
				break;
			case 'z':
				++arg_count;
				++argv;
				--argc;
				dmax = atoi(*argv);
				break;
			case 'd':
				++arg_count;
				++argv;
				--argc;
				strcpy(dem_file, *argv);
				break;
			case 'h':
				++arg_count;
				++argv;
				--argc;
				height = atoi(*argv);
				break;
			default:
				break;
			}
		}

	}

	if (arg_count != 4)  {
		printf("\n\nUSAGE: maxus -a azimuth (integer) -z dmax (integer) -d dem file (elevations as integers) -h instrument height (int)\n\nPLEASE REPORT ANY BUGS/PROBLEMS TO ADAM WINSTRAL (adam.winstral@ars.usda.gov)\n\n");
		printf("arg_count = %d, should be 4\n", arg_count);
		exit(0);
	}
	sprintf(output_file, "maxus_%d.asc",azim1 % 360);

	/*
	 * Adjdem is the DEM with -9999 all around the edges to known when to stop
	 * looking for the end point
	 */
	Dem = Read_Grid(dem_file);
	Adjdem = New_Grid_Header();
	Adjdem->NumRows = Dem->NumRows + 2;
	Adjdem->NumCols = Dem->NumCols + 2;
	Adjdem->XLLCorner = Dem->XLLCorner - Dem->CellSize;
	Adjdem->YLLCorner = Dem->YLLCorner - Dem->CellSize;
	Adjdem->CellSize = Dem->CellSize;
//	Adjdem->DataType = FLOAT;
	Adjdem->NoData = -9999;
	New_Data_Matrix(Adjdem);
	for (row = 0; row < Adjdem->NumRows; row++)  {
		for (col = 0; col < Adjdem->NumCols; col++)  {
			if (row == 0 || row == Adjdem->NumRows - 1 || \
					col == 0 || col == Adjdem->NumCols -1)
				Put_Cell_Value(row,col,Adjdem,-9999,-9999);
			else  {
				Get_Cell_Value(row - 1 ,col - 1,Dem,IntCell,FloatCell);
				Put_Cell_Value(row, col, Adjdem, *IntCell, *FloatCell);
			}
		}
	}

	xl = Dem->XLLCorner + Dem->CellSize / 2;
	xu = Dem->XLLCorner + Dem->NumCols * Dem->CellSize - Dem->CellSize / 2;
	yl = Dem->YLLCorner + Dem->NumRows / 2;
	yu = Dem->YLLCorner + Dem->NumRows * Dem->CellSize - Dem->CellSize / 2;

	/* NOTE:  The program was originally set up to handle multiple wind directions  */
	/*      and to average maxus' through an upwind window.  That interfered with   */
	/*      topobreak calculations so the c code now fixes azim2 to azim1.  This    */
	/*      is also why there are some somewhat strange looking for loops below.    */

	/* The program processing is as follows:	*/
	/*	for each cell find the endpoints of the described search line (ENDPOINTS)	*/
	/*		HORD will then search the line segment and find the cell with the	*/
	/*			maximum positive slope and return that slope in degrees		*/

	/*   azim1 = 130;  */
	azim2 = azim1;

	increment = 5.0;

	Hor = Create_New_Grid(Dem, FLOAT);

	if (azim1 > azim2) north_flag = TRUE;

	for (row = 0; row < Dem->NumRows; row++)
	{
		for (col = 0; col < Dem->NumCols; col++)
		{
			accum_hor = 0;
			count = 0;
			if (north_flag != TRUE)
			{
				for (w = azim1; w <= azim2; w = w + increment)
				{
					ENDPOINTS (row, col, w);
					hord = HORD(row, col, endi, endj);
					accum_hor += hord;
					count = ++count;
				}
			}
			else
			{
				for (w = azim1; w < 360; w = w + increment)
				{
					ENDPOINTS (row, col, w);
					hord = HORD(row, col, endj, endi);
					accum_hor += hord;
					count = ++count;
				}
				for (z = azim2; z >= 0; z = z - increment)
				{
					ENDPOINTS (row, col, w);
					hord = HORD(row, col, endj, endi);
					accum_hor += hord;
					count = ++count;
				}
			}
			index = accum_hor/count;
			Put_Cell_Value(l, m, Hor, IntValue, index);
			++m;
		}
		++l;
		m = 0;
		if (l % 50 == 0)  {
			printf("Starting row %d\n", l);
		}
	}
	Print_Grid(Hor, output_file);
}


