#include <ctype.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "grid_io.h"

#define TRUE 1
#define FALSE 0

int inc, window;
Grid Sum_Grid;
char prefix[50];

void Output(int mid_window)

/*  Input is the azimuth of the mid-vector of the upwind window		*/
/*  Program views the global Sum_Grid which contains the sum of each	*/
/*  vector calculation within the upwind window, divides the sum by the	*/
/*  number of vectors in the upwind window, and writes the output grid.	*/

{

	char out_file[50];
	Grid Out_Grid;
	float out_val, *Float, float_buf;
	int row, col, int_val, *Int, int_buf;

	Float = &float_buf;
	Int = &int_buf;

	Out_Grid = Create_New_Grid(Sum_Grid, FLOAT);
	sprintf(out_file, "%s_%d.%d.asc", prefix, window, mid_window);
	for (row = 0; row < Out_Grid->NumRows; row++)  {
		for (col = 0; col < Out_Grid->NumCols; col++)  {
			Get_Cell_Value(row,col,Sum_Grid,Int,Float);
			out_val = *Float / (window / inc + 1);
			Put_Cell_Value(row,col,Out_Grid,int_val,out_val);
		}
	}
	Print_Grid(Out_Grid, out_file);

}

main(int argc, char *argv[])

{

	Grid Old_Grid, New_Grid;

	int row, col, c, i, m, int_val, *Int_Data, int_buf, k = 0, second = FALSE;
	int min_azimuth, max_azimuth, arg_count = 0;
	float sum_val, old_val, new_val, *Float_Data, float_buf;

	char old_file[50], new_file[50], minmax[2][3] = {0};

	Float_Data = &float_buf;
	Int_Data = &int_buf;

	if (argc != 9)  {
		printf("\n\nUSAGE: windower -i increment between each directional file (integer) \n\t\t -w width of window centered on prevailing wind direction (integer) \n\t\t -a az1,az2 range of prevailing wind directions (integer) \n\t\t -p prefix for input files (ex. maxus, tbreak#dmax)\n\nNOTE: The quotient w/i MUST be an even integer!\n\nPLEASE REPORT ANY BUGS/PROBLEMS TO ADAM WINSTRAL (awinstra@nwrc.ars.usda.gov)\n\n");
		exit(0);
	}
	while (--argc > 1) {
		if ((*++argv)[0] == '-') {
			c = *++argv[0];
			switch (c) {
			case 'i':
			++arg_count;
			++argv;
			--argc;
			inc = atoi(*argv);
			break;
			case 'w':
				++arg_count;
				++argv;
				--argc;
				window = atoi(*argv);
				break;
			case 'a':
				++arg_count;
				++argv;
				--argc;
				while(c = *argv[0])  {
					if (*argv[0] == ',')  {
						second = TRUE;
						min_azimuth = atoi(minmax[0]);
						*++argv[0];
						k = 0;
					}
					if (!second)
						minmax[0][k] = *argv[0];
					if (second)
						minmax[1][k] = *argv[0];
					k++;
					*++argv[0];
				}
				max_azimuth = atoi(minmax[1]);
				if (max_azimuth < min_azimuth)
					max_azimuth = max_azimuth + 360;
				break;
			case 'p':
				++arg_count;
				++argv;
				--argc;
				strcpy(prefix, *argv);
				break;
			default:
				break;
			}

		}

	}
	if (arg_count != 4 || second==FALSE)  {
		printf("\n\nUSAGE: windower -i increment between each directional file (integer) \n\t\t -w width of window centered on prevailing wind direction (integer) \n\t\t -a az1,az2range of prevailing wind directions (integer) \n\t\t -p prefix for input files (ex. maxus, tbreak#dmax)\n\nNOTE: The quotient w/i MUST be an even integer!\n\nPLEASE REPORT ANY BUGS/PROBLEMS TO ADAM WINSTRAL (awinstra@nwrc.usda.gov)\n\n");
		exit(0);
	}

	/*  Sum the first n vectors of the upwind window starting at due North		*/

	for (i = min_azimuth - window / 2; i <= min_azimuth + window / 2; i = i + inc)  {
		/*  EDIT HERE  */
		sprintf(new_file, "%s_%d.asc", prefix, (i + 360) % 360);
		New_Grid = Read_Grid(new_file);
		if (i == min_azimuth - window / 2 || i == min_azimuth - window / 2 + 360) {
			Sum_Grid = Create_New_Grid(New_Grid, FLOAT);
		}
		for (row = 0; row < New_Grid->NumRows; row++)  {
			for (col = 0; col < New_Grid->NumCols; col++)  {
				Get_Cell_Value(row,col,New_Grid,Int_Data,Float_Data);
				new_val = *Float_Data;
				if ( i != min_azimuth - window / 2 && \
						i != min_azimuth - window / 2 + 360) {
					Get_Cell_Value(row,col,Sum_Grid,Int_Data,Float_Data);
					sum_val = *Float_Data;
					sum_val = sum_val + new_val;
				}
				else
					sum_val = new_val;

				Put_Cell_Value(row,col,Sum_Grid,int_val,sum_val);
			}
		}
	}
	Output(min_azimuth);
	Erase_Grid(New_Grid);

	/*  Compute the remaining upwind window calculations by deleting/subtracting	*/
	/*  one vector from the Sum_Grid and adding the new one.  Then send the result	*/
	/*  off to OUTPUT.								*/

	for (m = min_azimuth + inc; m <= max_azimuth; m = m + inc)  {   
		sprintf(new_file, "%s_%d.asc", prefix, (m + window / 2) % 360);
		sprintf(old_file, "%s_%d.asc", prefix, (m - window / 2 - inc + 360) % 360);
		New_Grid = Read_Grid(new_file);
		Old_Grid = Read_Grid(old_file);
		for (row = 0; row < New_Grid->NumRows; row++)  {
			for (col = 0; col < New_Grid->NumCols; col++)  {
				Get_Cell_Value(row,col,Old_Grid,Int_Data,Float_Data);
				old_val = *Float_Data;
				Get_Cell_Value(row,col,New_Grid,Int_Data,Float_Data);
				new_val = *Float_Data;
				Get_Cell_Value(row,col,Sum_Grid,Int_Data,Float_Data);
				sum_val = *Float_Data;
				sum_val = sum_val - old_val + new_val;
				Put_Cell_Value(row,col,Sum_Grid,int_val,sum_val);
			}
		}
		Output(m % 360);
		Erase_Grid(Old_Grid);
		Erase_Grid(New_Grid);
	}		


}			


