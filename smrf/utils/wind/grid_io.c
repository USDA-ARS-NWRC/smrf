/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    This unit is designed to perform basic I/O and        */
/*              data accessing functions for GRIDASCII-formatted      */
/*              raster maps.                                          */
/*                                                                    */
/*  PROGRAMMER:  Denis J. Dean.                                       */
/*                                                                    */
/*  COMPILE     This unit cannot be compiled by itself; it has no     */
/*    COMMAND:  MAIN function.  When linking this unit to other       */
/*              units, simply use CC GRID_IO.C.                       */
/*                                                                    */
/*  DEPENDENCIES:   This program uses the standard C libraries        */
/*                  STDIO.H, STDLIB.H, CTYPE and MALLOC.H.  In        */
/*                  addition, this unit has its own header file,      */
/*                  GRID_IO.H.                                        */
/*                                                                    */
/*  CALLING         This program does not accept any command-line     */
/*    CONVENTIONS:  parameters.                                       */
/*                                                                    */
/*  TERMINATING     This program does not call any additional         */
/*    CONVENTIONS:  programs when it terminates.                      */
/*                                                                    */
/*  BASIC           This program uses a dynamically-allocated         */
/*    PRINCIPLES:   structure to hold the header information from     */
/*                  a raster map.  This structure also contains a     */
/*                  pointer to another dynamically-allocated          */
/*                  memory structure, this one used as an array to    */
/*                  hold the actual raster data from the map.         */
/*                                                                    */
/*                      Structure                                     */
/*                      ---------                                     */
/*                        NumRows:     The number of rows in the      */
/*                                     raster map.                    */
/*                        NumCols:     The number of columns in the   */
/*                                     raster map.                    */
/*                        XLLCorner:   The X-coordinate of the lower  */
/*                                     left corner of the raster map. */
/*                        YLLCorner:   The Y-coordinate of the lower  */
/*                                     left corner of the raster map. */
/*                        CellSize:    The size of the raster cells   */
/*                                     in the raster map.             */
/*                        NoData:      The flag value used in raster  */
/*                                     cells to indicate no data.     */
/*                        DataType:    A flag used to identify the    */
/*                                     type of data used in the       */
/*                                     raster map.                    */
/*                        IntData:     A pointer to the array used to */
/*                                     hold the raster map's integer  */
/*                                     data matrix.                   */
/*                        FloatData:   A pointer to the array used to */
/*                                     hold the raster map's floating */
/*                                     point data matrix.             */
/*                                                                    */
/**********************************************************************/

                      /***************************/
                      /*                         */
                      /*     Include Files       */
                      /*                         */
                      /***************************/

#include <ctype.h>         /*  Needed for ISDIGIT function            */
#include <stdio.h>         /*  Needed for basic input/output          */
#include <stdlib.h>        /*  Needed for basic flow of control       */
#include <math.h>
/*#include <malloc/malloc.h>*/        /*  Needed for dynamic memory allocation   */

#include "grid_io.h"       /*  This unit's header file.               */

                      /***************************/
                      /*                         */
                      /*       Source Code       */
                      /*                         */
                      /***************************/

void  Get_Cell_Value(int Row, int Col, Grid Map1, int * IntData,
        float * FloatData)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Extracts a value from a specified cell in a raster    */
/*              map.                                                  */
/*                                                                    */
/*  ARGUMENTS:  ROW and COL identify the cell from which this         */
/*              function will extract a value.                        */
/*                                                                    */
/*              MAP1 is the map from which this function will         */
/*              extract a value.                                      */
/*                                                                    */
/*              INTDATA is a pointer to a variable that is            */
/*              undefined on input and on output contains the         */
/*              value of cell (ROW, COL) from MAP1 if MAP1            */
/*              contains integer data.  If MAP1 contains real         */
/*              data, INTDATA remains undefined on output.            */
/*                                                                    */
/*              FLOATDATA is a pointer to a variable that is          */
/*              undefined on input and on output contains the         */
/*              value of cell (ROW, COL) from MAP1 if MAP1            */
/*              contains floating point data.  If MAP1 contains       */
/*              integer data, FLOATDATA remains undefined on output.  */
/*                                                                    */
/*  RETURNS:    Void.                                                 */
/*                                                                    */
/*  SIDE        If MAP1 contains integer data, INTDATA is assigned    */
/*    EFFECTS:  the value of cell (ROW, COL) and FLOATDATA is left    */
/*              undefined.  If MAP1 contains floating point data,     */
/*              FLOATDATA is assigned the value of cell (ROW, COL)    */
/*              and INTDATA is left undefined.                        */
/*                                                                    */
/*  ALGORITHM:  The offset within the data array of cell (ROW, COL)   */
/*              is computed and the value from this array location    */
/*              is extracted and placed in the appropriate variable.  */
/*                                                                    */
/**********************************************************************/
  {  long  Offset;

     Offset = (long) Row;
     Offset *= (long) Map1->NumCols;
     Offset += (long) Col;

     if (Map1->DataType == INT)
       *IntData = Map1->IntData[Offset];
     else
       *FloatData = Map1->FloatData[Offset];
  }


void  Put_Cell_Value(int Row, int Col, Grid Map1, int IntValue,
        float FloatValue)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Places a specified value into a specified cell of     */
/*              a raster map.                                         */
/*                                                                    */
/*  ARGUMENTS:  ROW and COL identify the cell into which this         */
/*              function will place a value.                          */
/*                                                                    */
/*              MAP1 is the map into which this function will place   */
/*              a value.                                              */
/*                                                                    */
/*              INTVALUE is the value that will be placed in cell     */
/*              (ROW, COL) of MAP1, if MAP1 contains integer data.    */
/*                                                                    */
/*              FLOATVALUE is the value that will be placed in cell   */
/*              (ROW, COL) of MAP1, if MAP1 contains floating point   */
/*              data.                                                 */
/*                                                                    */
/*  RETURNS:    Void.                                                 */
/*                                                                    */
/*  SIDE        Either INTDATA of FLOATDATA is placed in cell         */
/*    EFFECTS:  (ROW, COL) of MAP1.                                   */
/*                                                                    */
/*  ALGORITHM:  The offset within the data array of cell (ROW, COL)   */
/*              is computed and a simple assignment statement is used */
/*              to place either INTDATA or FLOATDATA in this array    */
/*              location.                                             */
/*                                                                    */
/**********************************************************************/
  {  long  Offset;

     Offset = (long) Row;
     Offset *= (long) Map1->NumCols;
     Offset += (long) Col;

     if (Map1->DataType == INT)
       Map1->IntData[Offset] = IntValue;
     else
       Map1->FloatData[Offset] = FloatValue;
  }


int  Read_Number(FILE * Input, int * IntNumber, float * FloatNumber)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Reads a single number from an input file.             */
/*                                                                    */
/*  ARGUMENTS:  INPUT is a system file pointer to the file from       */
/*              which this program will read an integer.              */
/*                                                                    */
/*              INTNUMBER is a pointer to a variable that is          */
/*              undefined on input and on output contains the         */
/*              number read from INPUT; assuming that the number      */
/*              read was an integer.                                  */
/*                                                                    */
/*              FLOATNUMBER is a pointer to a variable that is        */
/*              undefined on input and on output contains the         */
/*              number read from INPUT; assuming that the number      */
/*              read was a floating point.                            */
/*                                                                    */
/*  RETURNS:    Either the global constant INT (if the number read    */
/*              from INPUT was an integer) or the global constant     */
/*              REAL (if the number read from INPUT was a floating    */
/*              point).                                               */
/*                                                                    */
/*  SIDE        (1) The file offset pointer within INFILE is moved    */
/*    EFFECTS:      due to read operations.                           */
/*              (2) Either INTNUMBER or FLOATNUMBER are set to        */
/*                  the value read from INPUT.                        */
/*                                                                    */
/*  ALGORITHM:  A WHILE is used to read characters from INPUT until   */
/*              a digit, minus sign or decimal point is reached.  A   */
/*              second WHILE loop reads all consecutive digits and    */
/*              decimal points following until a non-digit and non-   */
/*              decimal point is encountered.  As the digits and      */
/*              decimal points are read, they are placed in a string. */
/*              Notice that a flag, DATATYPE, which is initially      */
/*              set to the gloabal constant INT, is set to REAL       */
/*              if a decimal point is encountered.                    */
/*                                                                    */
/*              After a non-digit and non-decimal point value is      */
/*              encounted and the WHILE loop terminates, a null       */
/*              terminator is placed on the end of the string and     */
/*              either INTNUMBER is set to the result of applying     */
/*              the ATOI function to string or FLOATNUMBER is set     */
/*              to the result of applying the ATOF function to the    */
/*              string (depending on the value of the DATATYPE        */
/*              flag).  Once this is accomplished, the function       */
/*              terminates and returns the DATATYPE flag value.       */
/*                                                                    */
/**********************************************************************/
  {  char  Number[80];      /*  Character version of value read in    */
     char  Char;            /*  Latest character read from file       */
     int   Offset = 0;      /*  Offset within NUMBER                  */
     int   DataType = INT;  /*  Flag used to record data type         */

     Char = fgetc(Input);
     while ((!isdigit(Char)) && (Char != '-') && (Char != '.'))
       Char = fgetc(Input);

     if (Char == '.') DataType = FLOAT;
     Number[Offset] = Char;
     Offset++;

     Char = fgetc(Input);
     while ((isdigit(Char)) || (Char == '.'))
       {  Number[Offset] = Char;
          Offset++;
          if (Char == '.') DataType = FLOAT;
          Char = fgetc(Input);
       }

     Number[Offset] = '\0';

     if (DataType == INT)
       *IntNumber = atoi(Number);
     else
       *FloatNumber = atof(Number);

     return(DataType);
  }


Grid  New_Grid_Header()
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Creates a new raster map header node and initializes  */
/*              this node's fields to null's and NODATA's.            */
/*                                                                    */
/*  ARGUMENTS:  None.                                                 */
/*                                                                    */
/*  RETURNS:    A pointer to the new node created by this function.   */
/*                                                                    */
/*  SIDE        (1) Memory is allocated for the new header node       */
/*    EFFECTS:      created by this function.                         */
/*                                                                    */
/*  ALGORITHM:  A standard error-trapped MALLOC statement and a       */
/*              series of assignment statements.                      */
/*                                                                    */
/**********************************************************************/
  {  Grid  NewGrid;        /*  New map returned by this function      */

     if ((NewGrid = (Grid) malloc(sizeof(struct GridStructure))) == NULL)
       {  printf("\n\nERROR:  Not enough memory to hold map\n\n");
          exit(0);
       }

     NewGrid->NumRows = NODATA;
     NewGrid->NumCols = NODATA;
     NewGrid->XLLCorner = NODATA;
     NewGrid->YLLCorner = NODATA;
     NewGrid->CellSize = NODATA;
     NewGrid->NoData = NODATA;
     NewGrid->DataType = NODATA;
     NewGrid->IntData = NULL;
     NewGrid->FloatData = NULL;

     return(NewGrid);
  }


int  File_Data_Type(char FileName[])
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Determines the type of data (intereg or real) stored  */
/*              in a GRIDASCII file.                                  */
/*                                                                    */
/*  ARGUMENTS:  FILENAME is the name of the GRIDASCII file being      */
/*              evaluated.                                            */
/*                                                                    */
/*  RETURNS:    Either the global constant INT (meaning that FILENAME */
/*              contains integer data) or FLOAT (meaning that         */
/*              FILENAME contains floating point data).               */
/*                                                                    */
/*  SIDE        (1) FILENAME is openned, read, and closed.            */
/*    EFFECTS:                                                        */
/*                                                                    */
/*  ALGORITHM:  A standard error-trapped FOPEN statement is used to   */
/*              open FILENAME for reading.  A FOR loop is then used   */
/*              to read past the six header lines that start the      */
/*              GRIDASCII file.  Each iteration of this loop uses     */
/*              a WHILE loop to repeatedly read characters from       */
/*              FILENAME until an end-of line marker is reached.      */
/*                                                                    */
/*              Once the header lines are bipassed, another WHILE     */
/*              loop is used to read characters from the first data   */
/*              line of FILENAME until either a decimal point or a    */
/*              end-of-line marker is reached.  Once this loop        */
/*              terminates, the input file is closed and an IF        */
/*              statement is used to evaluate the character that      */
/*              caused the loop to terminate.  If this character is   */
/*              an end-of-line marker, no decimal points were         */
/*              encountered in the entire data line so the function   */
/*              conludes that the file contains integer data.  In     */
/*              this case, the function returns INT.  If the          */
/*              character that caused the loop to terminate is a      */
/*              decimal point, the file obviously contains real       */
/*              data, so the function returns FLOAT.                  */
/*                                                                    */
/**********************************************************************/
  {  FILE *  InFile;    /*  System file pointer file being evaluated  */
     char    Char;      /*  Character read from input file            */
     int     Line;      /*  FOR loop counter                          */

     if ((InFile = fopen(FileName, "rt")) == NULL)
       {  printf("\n\nERROR:  Could not open input file %s\n\n",
            FileName);
          exit(0);
       }

     for (Line = 0; Line < 6; Line++)
       {  Char = fgetc(InFile);
          while (Char != '\n') Char = fgetc(InFile);
       }

     Char = fgetc(InFile);
     while ((Char != '.') && (Char != '\n')) Char = fgetc(InFile);

     fclose(InFile);

     if (Char == '.')
       return(FLOAT);
     else
       return(INT);
  }


void  New_Data_Matrix(Grid Map1)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Allocates the memory needed to hold the raster        */
/*              matrix for a grid.                                    */
/*                                                                    */
/*  ARGUMENTS:  MAP1 is a pointer to the header node of the map       */
/*              for which this function will allocate memory for      */
/*              a raster data matrix.  Note that at least the         */
/*              NUMROWS, NUMCOLS and DATATYPE fields of this map      */
/*              header must be valid.                                 */
/*                                                                    */
/*  RETURNS:    Void.                                                 */
/*                                                                    */
/*  SIDE        An IF statement is used to determine what type of     */
/*    EFFECTS:  data (integer or floating point) is stored in         */
/*              MAP1.  An error-trapped MALLOC statement is then      */
/*              used to assign memory for the appropriate type of     */
/*              data matrix.                                          */
/*                                                                    */
/**********************************************************************/
  {  if (Map1->DataType == INT)
       {  if ((Map1->IntData = (int *) malloc(Map1->NumRows * Map1->
           NumCols * sizeof(int))) == NULL)
            {  printf("\n\nERROR:  Not enough memory to hold map\n\n");
               exit(1);
            }
       }
     else
       {  if ((Map1->FloatData = (float *) malloc(Map1->NumRows * Map1->
           NumCols * sizeof(float))) == NULL)
            {  printf("\n\nERROR:  Not enough memory to hold map\n\n");
               exit(1);
            }
       }
  }


Grid  Read_Grid(char FileName[])
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Reads a raster map from an ARC/INFO GRIDASCII-format  */
/*              file into a memory-resident structure.                */
/*                                                                    */
/*  ARGUMENTS:  FILENAME is a string containing the name of the       */
/*              file to be read.                                      */
/*                                                                    */
/*  RETURNS:    A pointer to the structure containing the header      */
/*              information of the map read from FILENAME.            */
/*                                                                    */
/*  SIDE        (1) FILENAME is opened, read in its entirety, and     */
/*    EFFECTS:      closed.                                           */
/*              (2) Memory is allocated to hold the map read from     */
/*                  FILENAME.                                         */
/*              (3) If I/O errors or memory allocation errors occur,  */
/*                  an error message is printed out and program       */
/*                  execution is halted.                              */
/*                                                                    */
/*  ALGORITHM:  Memory is allocated for the grid header node using    */
/*              the NEW_GRID_HEADER function.  The DATATYPE field     */
/*              of this new header is filled using the FILE_DATA_TYPE */
/*              function.                                             */
/*                                                                    */
/*              FILENAME is opened using a standard error-trapped     */
/*              FOPEN statement.  The error handler in this case      */
/*              simply prints an error message and terminates the     */
/*              program.                                              */
/*                                                                    */
/*              A series of six calls to READ_NUMBER are made to read */
/*              the first six header lines from FILENAME.  Each of    */
/*              the values read from these file header lines are then */
/*              placed in the dynamically allocated header structure. */
/*                                                                    */
/*              A call to NEW_DATA_MATRIX is then used to allocate    */
/*              memory for the new raster data matrix.                */
/*                                                                    */
/*              A pair of nested FOR loops are used to read the data  */
/*              from FILENAME into the dynamically-allocated memory   */
/*              array.  Each pass through these loops uses the        */
/*              READ_NUMBER function to read a single value from the  */
/*              input file.                                           */
/*                                                                    */
/*              When these nested FOR loops conclude, FILENAME is     */
/*              closed and the function terminates, returning a       */
/*              pointer to the new map.                               */
/*                                                                    */
/**********************************************************************/
  {  Grid    InputGrid;           /*  Grid to be read into system     */
     FILE *  InFile;              /*  System file pointer to input    */
     int     Row, Col;            /*  FOR loop counters for input     */
     int     Int;                 /*  Argument for READ_NUMBER        */
     float   Float;               /*  Argument for READ_NUMBER        */

     InputGrid = New_Grid_Header();
     InputGrid->DataType = File_Data_Type(FileName);

     if ((InFile = fopen(FileName, "rt")) == NULL)
       {  printf("\n\nERROR:  Could not open input file %s\n\n",
            FileName);
          exit(0);
       }

     if (Read_Number(InFile, &Int, &Float) == INT)
       InputGrid->NumCols = Int;
     else
       InputGrid->NumCols = Float;

     if (Read_Number(InFile, &Int, &Float) == INT)
       InputGrid->NumRows = Int;
     else
       InputGrid->NumRows = Float;

     if (Read_Number(InFile, &Int, &Float) == INT)
       InputGrid->XLLCorner = Int;
     else
       InputGrid->XLLCorner = Float;

     if (Read_Number(InFile, &Int, &Float) == INT)
       InputGrid->YLLCorner = Int;
     else
       InputGrid->YLLCorner = Float;

     if (Read_Number(InFile, &Int, &Float) == INT)
       InputGrid->CellSize = Int;
     else
       InputGrid->CellSize = Float;

     if (Read_Number(InFile, &Int, &Float) == INT)
       InputGrid->NoData = Int;
     else
       InputGrid->NoData = Float;

     New_Data_Matrix(InputGrid);

     for (Row = 0; Row < InputGrid->NumRows; Row++)
        for (Col = 0; Col < InputGrid->NumCols; Col++)
          {  Read_Number(InFile, &Int, &Float);
             Put_Cell_Value(Row, Col, InputGrid, Int, Float);
          }

     fclose(InFile);
     return(InputGrid);
  }


void  Print_Grid(Grid PrintMap, char FileName[])
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Prints a raster map to an ASCII file in ARC/INFO      */
/*              GRIDASCII format.                                     */
/*                                                                    */
/*  ARGUMENTS:  PRINTMAP is a pointer to the raster map to be printed */
/*              to an ASCII file.                                     */
/*                                                                    */
/*              FILENAME is the name of the file to which PRINTMAP    */
/*              will be printed.                                      */
/*                                                                    */
/*  RETURNS:    Void.                                                 */
/*                                                                    */
/*  SIDE        (1) The contents of PRINTMAP are written in ARC/INFO  */
/*    EFFECTS:      GRIDASCII format to FILENAME.                     */
/*              (2) If an I/O error occurs, an error message is       */
/*                  printed to the screen and the program terminates. */
/*                                                                    */
/*  ALGORITHM:  FILENAME is opened for text output using a standard   */
/*              error-trapped FOPEN command.  The error handler       */
/*              simply prints an error message and terminates         */
/*              program execution.                                    */
/*                                                                    */
/*              Assuming FILENAME is opened correctly, a series of    */
/*              six standard FPRINTF statements are used to output    */
/*              the contents of PRINTMAP's header to FILENAME.        */
/*              A pair of nested FOR loops are then used to print     */
/*              PRINTMAP's actual raster data to FILENAME.  FILENAME  */
/*              is then closed, and the function terminates.          */
/*                                                                    */
/**********************************************************************/
  {  FILE * OutFile;              /*  System file pointer to output   */
     int    Row, Col;             /*  FOR loop counters for output    */
     int    Int;                  /*  Argument for GET_CELL_VALUE     */
     float  Float;                /*  Argument for GET_CELL_VALUE     */

     if ((OutFile = fopen(FileName, "wt")) == NULL)
       {  printf("\n\nERROR:  Could not open output file %s\n\n",
            FileName);
          exit(0);
       }

     fprintf(OutFile, "ncols       %d\n", PrintMap->NumCols);
     fprintf(OutFile, "nrows       %d\n", PrintMap->NumRows);
     fprintf(OutFile, "xllcorner   %f\n", PrintMap->XLLCorner);
     fprintf(OutFile, "yllcorner   %f\n", PrintMap->YLLCorner);
     fprintf(OutFile, "cellsize    %f\n", PrintMap->CellSize);
     fprintf(OutFile, "NODATA_value      %d\n", PrintMap->NoData);

     for (Row = 0; Row < PrintMap->NumRows; Row++)
       {  for (Col = 0; Col < PrintMap->NumCols; Col++)
            {  Get_Cell_Value(Row, Col, PrintMap, &Int, &Float);
               if (PrintMap->DataType == INT)
                 fprintf(OutFile, " %6d", Int);
               else
                 fprintf(OutFile, " %15.5f", Float);
            }

          fprintf(OutFile, "\n");
       }

     fclose(OutFile);
  }


Grid  Erase_Grid(Grid Map1)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Erases (frees the memory allocated to) a map.         */
/*                                                                    */
/*  ARGUMENTS:  MAP1 is the map to be erased.                         */
/*                                                                    */
/*  RETURNS:    A NULL pointer.                                       */
/*                                                                    */
/*  SIDE        (1) The memory allocated to MAP1 is freed.            */
/*    EFFECTS:                                                        */
/*                                                                    */
/*  ALGORITHM:  Simple FREE statements.                               */
/*                                                                    */
/**********************************************************************/
  {  if (Map1->IntData != NULL) free(Map1->IntData);
     if (Map1->FloatData != NULL) free(Map1->FloatData);
     free(Map1);
     return(NULL);
  }


Grid  Create_New_Grid(Grid Original, int DataType)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Creates a new, empty raster map with the same         */
/*              number of rows and columns, minimum X and Y,          */
/*              cellsize, and so on as found in an existing map.      */
/*                                                                    */
/*  ARGUMENTS:  ORIGINAL is the existing grid from which this         */
/*              function will copy number of rows, number of          */
/*              columns, and so on.                                   */
/*                                                                    */
/*              DATATYPE is the data type (integer or real) that      */
/*              will be contained in the new map.                     */
/*                                                                    */
/*  RETURNS:    The new map created by this function.                 */
/*                                                                    */
/*  SIDE        (1) Memory is allocated to hold the new map           */
/*    EFFECTS:      created by this function.                         */
/*                                                                    */
/*  ALGORITHM:  The NEW_GRID_HEADER function is called to             */
/*              allocate memory for the header of the new             */
/*              map created by this function.  A series of            */
/*              simple assignment statements are then used            */
/*              to fill the fields in the header node using           */
/*              parameters copied from ORIGINAL.  The                 */
/*              NEW_DATA_MATRIX function is then called to            */
/*              allocate memeory for the new map's data               */
/*              matrix.  The function then terminates,                */
/*              returning the new map.                                */
/*                                                                    */
/**********************************************************************/
  {  Grid  NewMap;          /*  New grid created by this function     */

     NewMap = New_Grid_Header();

     NewMap->NumRows = Original->NumRows;
     NewMap->NumCols = Original->NumCols;
     NewMap->XLLCorner = Original->XLLCorner;
     NewMap->YLLCorner = Original->YLLCorner;
     NewMap->CellSize = Original->CellSize;
     NewMap->NoData = Original->NoData;
     NewMap->DataType = DataType;
     NewMap->IntData = NULL;
     NewMap->FloatData = NULL;

     New_Data_Matrix(NewMap);

     return(NewMap);
  }
