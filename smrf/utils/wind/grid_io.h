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
                      /* Define Global Constants */
                      /*                         */
                      /***************************/

#define INT 1             /*  Flag used to identify integer data      */
#define FLOAT 2           /*  Flag used to identify real data         */
#define NODATA -9999      /*  Flag used to mark no data value         */

                      /***************************/
                      /*                         */
                      /*  Define Variable Types  */
                      /*                         */
                      /***************************/

typedef struct GridStructure * Grid;

struct GridStructure
  {  int     NumRows;     /*  Number of rows in map                   */
     int     NumCols;     /*  Number of columns in map                */
     float   XLLCorner;   /*  X coordinate of lower left corner       */
     float   YLLCorner;   /*  Y coordinate of lower left corner       */
     float   CellSize;    /*  Size of raster cells                    */
     int     NoData;      /*  Flag used to mark cells without data    */
     int     DataType;    /*  Flag used to determine data type        */
     int   * IntData;     /*  Pointer to integer raster data matrix   */
     float * FloatData;   /*  Pointer to integer raster data matrix   */
  };

                      /***************************/
                      /*                         */
                      /*    Function Prototypes  */
                      /*                         */
                      /***************************/

void  Get_Cell_Value(int Row, int Col,      /*  Extracts a value from */
        Grid Map1, int * IntData,           /*    a specified cell in */
        float * FloatData);                 /*    a specified grid    */

void  Put_Cell_Value(int Row, int Col,      /*  Places a specified    */
        Grid Map1, int IntValue,            /*    value in a specifed */
        float FloatValue);                  /*    cell of a grid      */

int  Read_Number(FILE * Input, int *        /*  Reads the next number */
       IntNumber, float * FloatNumber);     /*    from an input file  */

Grid  New_Grid_Header();                    /*  Creates a new map     */
                                            /*    header node         */

int  File_Data_Type(char FileName[]);       /*  Determines if a       */
                                            /*    GRIDASCII file      */
                                            /*    contains integer or */
                                            /*    real data.          */

void  New_Data_Matrix(Grid Map1);           /*  Creates a new raster  */
                                            /*    data matrix         */

Grid  Read_Grid(char FileName[]);           /*  Reads a GRIDASCII     */
                                            /*    file into memory    */

Grid  Erase_Grid(Grid Map1);                /*  Erases the memory     */
                                            /*    resident portion of */
                                            /*    a grid              */

void  Print_Grid(Grid Map1, char            /*  Prints a grid to a    */
        FileName[]);                        /*    GRIDASCII file      */

Grid  Create_New_Grid(Grid Original,        /*  Creates a new,        */
        int DataType);                      /*    empty grid          */
