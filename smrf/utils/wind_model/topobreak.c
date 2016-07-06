#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <ctype.h>
/*#include <malloc/malloc.h>*/
#include "grid_io.h"
#include "breshen.h"

#define TRUE 1
#define FALSE 0
#define PI 3.141592654
#define DISTANCE (float) (sqrt((endj-startj)*(endj-startj) +\
		(endi-starti)*(endi-starti))) * Dem->CellSize

int endi, endj;
Grid Dem, Adjdem;
int xcoords[500], ycoords[500], elevs[500], H[500];

void ENDPOINTS(starti, startj, deg_direction, max_dist)
int starti, startj, max_dist;
float deg_direction;
{
	float rad_direction, tempj, tempi, *FloatCell, gg;
	int elev, *IntCell, poti, potj;

	FloatCell = &gg;
	IntCell = &elev;

	rad_direction = ( (float) deg_direction/180) * PI;
	endj = startj;
	tempj = startj;
	endi = starti;
	tempi = starti;

	Get_Cell_Value ((short) starti + 1, (short) startj + 1, Adjdem, IntCell, FloatCell);

	if (deg_direction > 0 && deg_direction <= 45)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempi = endi - 1;
			tempj = tempj + tan(rad_direction);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction > 45 && deg_direction < 90)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempj = endj + 1;
			tempi = tempi - tan (PI / 2 - rad_direction);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 90 && deg_direction <= 135)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempj = endj + 1;
			tempi = tempi + tan (rad_direction - PI / 2);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 135 && deg_direction < 180)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempi = endi + 1;
			tempj = tempj + tan (PI - rad_direction);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction > 180 && deg_direction <= 225)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempi = endi + 1;
			tempj = tempj - tan (rad_direction - PI);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj +1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction > 225 && deg_direction < 270)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempj = endj - 1;
			tempi = tempi + tan (1.5 * PI - rad_direction);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 270 && deg_direction <= 315)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempj = endj - 1;
			tempi = tempi - tan (rad_direction - 1.5 * PI);
			poti = floor(tempi + 0.5);
			Get_Cell_Value(poti + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endj = tempj;
				endi = poti;
			}
		}
	}
	else if (deg_direction > 315 && deg_direction < 360)
	{
		while (elev >= 0 && DISTANCE < max_dist)
		{
			tempi = endi - 1;
			tempj = tempj - tan (2 * PI - rad_direction);
			potj = floor(tempj + 0.5);
			Get_Cell_Value(tempi + 1, potj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
			{
				endi = tempi;
				endj = potj;
			}
		}
	}
	else if (deg_direction == 90)
	{
		while (elev >= 0 && DISTANCE <= max_dist)
		{
			tempj += 1;
			Get_Cell_Value(tempi + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
				endj = tempj;
		}
	}
	else if (deg_direction == 180)
	{
		while (elev >= 0 && DISTANCE <= max_dist)
		{
			tempi += 1;
			Get_Cell_Value(tempi + 1,tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
				endi = tempi;
		}
	}
	else if (deg_direction == 270)
	{
		while (elev >= 0 && DISTANCE <= max_dist)
		{
			tempj -= 1;
			Get_Cell_Value(tempi + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
				endj = tempj;
		}
	}
	else if (deg_direction == 0 || deg_direction == 360)
	{
		while (elev >= 0 && DISTANCE <= max_dist)
		{
			tempi -= 1;
			Get_Cell_Value(tempi + 1, tempj + 1, Adjdem, IntCell, FloatCell);
			if (*IntCell >= 0)
				endi = tempi;
		}
	}
}


float SLOPE (l,m)
int l,m;

{
	int rise;
	float run, slop;
	if (l == m)
	{
		slop = 0;
		goto slopend;
	}
	rise = elevs[m] - elevs[l];
	run = sqrt((xcoords[l] - xcoords[m]) * (xcoords[l] - xcoords[m]) + \
			(ycoords[l] - ycoords[m]) * (ycoords[l] - ycoords[m])) * Dem->CellSize;
	if (run == 0){
		slop = 0;
		goto slopend;
	}
	slop = rise/run;
	slopend:    return (slop);
}


float HORD(starti, startj, endi, endj)
int startj, starti, endj, endi;
{
	int p, *IntCell, current_elevation, elev, i, j, N = 0, found;
	float *FloatCell, zz, run = 0, slope = -11.5, temp_slope = 0;
	float hordeg;
	short *X, *Y, nextX, nextY;
	struct BreshenhamData *LineData, Initialize;

	FloatCell = &zz;
	IntCell = &elev;
	nextY = (short) starti;
	nextX = (short) startj;
	X = &nextX;
	Y = &nextY;
	Get_Cell_Value(starti, startj, Dem, IntCell, FloatCell);

	LineData = &Initialize;
	Initialize.SlopeType = 0;
	xcoords[0] = startj;
	ycoords[0] = starti;
	elevs[0] = *IntCell;
	if (starti == endi && startj == endj)
	{
		hordeg = 0.;
		goto end;
	}
	while ((int)*X != endj || (int)*Y != endi)
	{
		GetNextCellCoordinate((short)startj, (short)starti, (short)endj,\
				(short)endi, X, Y, LineData);
		Get_Cell_Value(nextY, nextX, Dem, IntCell, FloatCell);
		++N; 
		xcoords[N] = nextX;
		ycoords[N] = nextY;
		elevs[N] = *IntCell;
	}
	H[N - 1] = N - 1;
	i = N - 2;
	while ( i >= 0 )
	{
		j = i + 1;
		found = 0;
		while (found == 0)
		{
			if (SLOPE (i,j) < SLOPE (j,H[j]))
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
				if (SLOPE(i,j) > SLOPE (j,H[j]))
					H[i] = j;
				else
					H[i] = H[j];
			}
		}
		--i;
	}
	hordeg = atan(SLOPE(0,H[0])) / PI * 180;
	end:    return (hordeg);
}

main (int argc, char *argv[])
{
	int xl, xu, yl, yu, azim1, azim2, north_flag = 0;
	int i, j, count, z, *IntData, kk, IntValue, dist_max, input_max;
	int yULpix, xULpix, xlpix, xupix, ylpix, yupix;
	int l = 0, m = 0, row, col, arg_count = 0;
	int c;
	float accum_hor, index, hord, w, increment, *FloatData, zz, separation;
	float longhor, FloatValue;
	Grid Hor, Hordeg;

	char horizon_file[50];
	char output_file[50];
	char dem_file[50];

	IntData = &kk;
	FloatData = &zz;

	if (argc != 7)  {
		printf("\n\nUSAGE: topobreak -s separation distance between near and far maxus calculations (integer)\n\t\t-a azimuth (integer) -d dem file (elevations as integers)\n\nNOTE: Cells located at the edges of the DEM usually do not have a sufficient view\n\t of upwind conditions to calculate a reliable topobreak.  Make sure your region of\n\t interest has a sufficient buffer of upwind elevation data.\n\nIMPORTANT: The algorithm will be looking for the extended maxus files(i.e. maxus1000),\n\t\t so this function must be executed in a directory that contains these files\n\n PLEASE REPORT ANY BUGS/PROBLEMS TO ADAM WINSTRAL (adam.winstral@ars.usda.gov)\n\n");
		exit(0);
	}

	while (--argc > 1) {
		if ((*++argv)[0] == '-') {
			c = *++argv[0];
			switch (c) {
			case 's':
			++arg_count;
			++argv;
			--argc;
			dist_max = atoi(*argv);
			break;
			case 'a':
			++arg_count;
			++argv;
			--argc;
			azim1 = atoi(*argv);
			break;
			case 'd':
			++arg_count;
			++argv;
			--argc;
			strcpy(dem_file, *argv);
			break;
			default:
				break;
			}
		}			

	}
	if (arg_count != 3)  {
		printf("\n\nUSAGE: topobreak -s separation distance between near and far maxus calculation s (integer)\n\t\t-a azimuth (integer) -d dem file (elevations as integers)\n\nNOTE: Cells located at the edges of the DEM usually do not have a sufficient view\n\t of upwind conditios to calculate a reliable topobreak.  Make sure your region of\n\t interest has a sufficient buffer of upwind elevation data.\n\nIMPORTANT: The algorithm will be looking for the extended maxus files(i.e. maxus1000),\n\t\tso this function must be executed in a directory that contains these files\n\nPLEASEREPORT ANY BUGS/PROBLEMS TO ADAM WINSTRAL (adam.winstral@ars.usda.gov)\n\n");

		exit(0);
	}
	sprintf(output_file, "tbreak%d_%d.asc",dist_max,azim1 % 360);
	sprintf(horizon_file, "maxus_%d.asc",azim1 % 360);
	Hordeg = Read_Grid(horizon_file);
	Dem = Read_Grid(dem_file);
	Adjdem = New_Grid_Header();
	Adjdem->NumRows = Dem->NumRows + 2;
	Adjdem->NumCols = Dem->NumCols + 2;
	Adjdem->XLLCorner = Dem->XLLCorner - Dem->CellSize;
	Adjdem->YLLCorner = Dem->YLLCorner - Dem->CellSize;
	Adjdem->CellSize = Dem->CellSize;
	Adjdem->DataType = INT;
	Adjdem->NoData = -9999;
	New_Data_Matrix(Adjdem);
	for (row = 0; row < Adjdem->NumRows; row++)  {
		for (col = 0; col < Adjdem->NumCols; col++)  {
			if (row == 0 || row == Adjdem->NumRows - 1 || \
					col == 0 || col == Adjdem->NumCols - 1)
				Put_Cell_Value(row,col,Adjdem,-9999,FloatValue);
			else  {
				Get_Cell_Value(row - 1,col - 1,Dem,IntData,FloatData);
				Put_Cell_Value(row, col, Adjdem, *IntData, FloatValue);
			}
		}

	}

	xl = Dem->XLLCorner + Dem->CellSize / 2;
	xu = Dem->XLLCorner + Dem->NumCols * Dem->CellSize - Dem->CellSize / 2;
	yl = Dem->YLLCorner + Dem->NumRows / 2;
	yu = Dem->YLLCorner + Dem->NumRows * Dem->CellSize - Dem->CellSize / 2;

	/*  azim1 = 130;    */
	azim2 = azim1;
	increment = 4.5;
	/*  dist_max = 100;  */

	input_max = dist_max - Dem->CellSize;

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
					ENDPOINTS (row, col, w, input_max);
					Get_Cell_Value (endi,endj,Hordeg,IntData,FloatData);
					longhor = *FloatData;
					hord = HORD(row, col, endi, endj);
					separation = hord - longhor;
					accum_hor += separation;
					count = ++count;
				}
			}
			else
			{
				for (w = azim1; w < 360; w = w + increment)
				{
					ENDPOINTS (row, col, w, input_max);
					Get_Cell_Value(endi,endj,Hordeg,IntData,FloatData);
					longhor = *FloatData;
					hord = HORD(row, col, endj, endi);
					separation = hord - longhor;
					accum_hor += separation;
					count = ++count;
				}
				for (z = azim2; z >= 0; z = z - increment)
				{
					ENDPOINTS (row, col, w, input_max);
					Get_Cell_Value(endi,endj,Hordeg,IntData,FloatData);
					longhor = *FloatData;
					hord = HORD(row, col, endj, endi);
					separation = hord - longhor;
					accum_hor += separation;
					count = ++count;
				}
			}
			index = accum_hor/count;
			Put_Cell_Value(l, m, Hor, IntValue, index);
			++m;
		}
		++l;
		m = 0;
		if (l % 50 == 0) printf("starting row %d\n", l);
	}
	Print_Grid(Hor,output_file);
}



