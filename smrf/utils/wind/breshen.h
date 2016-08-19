/**********************************************************************/
/*                                                                    */
/*   This file contains the include data for an efficient implement-  */
/*   ation of Breshenham's algorithm for raster line drawing.         */
/*   Programs wishing to use this procedure should include this       */
/*   file and be linked to the system's main source code file         */
/*   (Breshen.C).                                                     */
/*                                                                    */
/**********************************************************************/

                         /*************************/
                         /*                       */
                         /*   Type Declarations   */
                         /*                       */
                         /*************************/

struct BreshenhamData
  {  short dx, dy, Inc1, Inc2, Inc3, Inc4, Inc5, d;
     char Octent, SlopeType;
  };

                         /*************************/
                         /*                       */
                         /*  Function Prototypes  */
                         /*                       */
                         /*************************/

void  GetNextCellCoordinate(short StartX, short StartY, short EndX,
   short EndY, short *X, short *Y, struct BreshenhamData *LineData);
