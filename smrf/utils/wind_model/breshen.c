/**********************************************************************/
/*                                                                    */
/*   This file contains the source code for an efficient implement-   */
/*   ation of Breshenham's algorithm for raster line drawing.         */
/*   Programs wishing to use this procedure should include this       */
/*   system's include file (Breshen.H) and be linked to this file.    */
/*                                                                    */
/**********************************************************************/

                         /*************************/
                         /*                       */
                         /*     Include Files     */
                         /*                       */
                         /*************************/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "breshen.h"

                         /*************************/
                         /*                       */
                         /*  Function Prototypes  */
                         /*                       */
                         /*************************/

void  InitializeLineData(short StartX, short StartY, short EndX,
   short EndY, short *X, short *Y, struct BreshenhamData *LineData);

                         /*************************/
                         /*                       */
                         /*      Source Code      */
                         /*                       */
                         /*************************/

void  GetNextCellCoordinate(short StartX, short StartY, short EndX,
   short EndY, short *X, short *Y, struct BreshenhamData *LineData)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Uses Breshenham's Algorithm to find the next cell     */
/*              that lies in a line of cells connecting two specified */
/*              points.                                               */
/*                                                                    */
/*  ARGUMENTS:  (STARTX, STARTY) and (ENDX, ENDY) are the coordinates */
/*              of the two cells that identify the endpoints of the   */
/*              line segment being traced by this algorithm.  X and   */
/*              Y are pointers to variables that on input contain     */
/*              either (1) the coordinates of the last cell in the    */
/*              (STARTX, STARTY)-to-(ENDX, ENDY) line segment that    */
/*              was identified by this function, or (2) are undefined */
/*              (if no previous cell was identified via an earlier    */
/*              call to this function).  On output, X and Y contain   */
/*              the coordinates of the new cell identified by this    */
/*              function.                                             */
/*                                                                    */
/*              LINEDATA is a pointer to a structure that contains    */
/*              the data used by Breshenham's Algorithm.  This data   */
/*              should not be altered between calls to this function. */
/*              Note that when this function is called for the first  */
/*              time for any particular line segment, the SLOPETYPE   */
/*              field on LINEDATA should be set to zero (all other    */
/*              fields can be left undefined).                        */
/*                                                                    */
/*  RETURNS:    Void.                                                 */
/*                                                                    */
/*  SIDE        X and Y are assigned their proper values, and the     */
/*    EFFECTS:  contents of the LINEDATA structure are updated.       */
/*                                                                    */
/*  ALGORITHM:  This function uses a slightly modified version of the */
/*              implementation of Breshenham's algorithm shown in the */
/*              flow chart on page 595 of Nabajyoti Barkakati's book, */
/*              THE WAITE GROUP'S MICROSOFT MACRO ASSEMBLER BIBLE     */
/*              (1990).  The modifications made to the algorithm are  */
/*              as follows:                                           */
/*                                                                    */
/*                (1) No I/O takes place, this function simply        */
/*                    identfies cells along the (STARTX, STARTY)      */
/*                    to (ENDX, ENDY) line.  This results in the      */
/*                    elimination of any code designed to perform     */
/*                    the output functions implied in Barkakati's     */
/*                    flowchart.                                      */
/*                                                                    */
/*                (2) Each call to this function identifies only one  */
/*                    cell that lies along the (STARTX, STARTY) to    */
/*                    (ENDX, ENDY) line (unlike the algorithm in the  */
/*                    flow chart, which loops through all cells in    */
/*                    the line segment).  This eliminates the final   */
/*                    looping mechanism shown in Barkakati's flow     */
/*                    chart and neccissitates the use of the LINE-    */
/*                    DATA structure, so that subsequent calls to     */
/*                    this function will have access to the local     */
/*                    variables created by the function durring the   */
/*                    preceeding iteration.                           */
/*                                                                    */
/*                (3) The algorithm described in Barkakati's flow-    */
/*                    chart is designed to switch the direction of    */
/*                    the line being drawn (i.e., draw a line from    */
/*                    (ENDX, ENDY) to (STARTX, STARTY) rather than    */
/*                    the other way around) to ensure that the        */
/*                    coordinate altered on each iteration is always  */
/*                    incremented rather than incremented for some    */
/*                    line segements and decremented for others       */
/*                    (depending on the line segment's slope).  This  */
/*                    works well from an efficency point of view      */
/*                    but is not appropriate for conducting linear    */
/*                    viewshed analyses.  Thus, the implementation    */
/*                    of Breshenham's Algorithm used in this function */
/*                    preserves the original direction of the         */
/*                    (STARTX, STARTY)-to-(ENDX, ENDY) line.  This    */
/*                    requires keeping track of whether to increment  */
/*                    or decrement the coordinates, and requires      */
/*                    testing the accumulated error value for both    */
/*                    positive and negative variations.  Thus, some   */
/*                    of the conditionals in this function are more   */
/*                    complex than those shown in Barkakati's flow-   */
/*                    chart, and an additional local variable (the    */
/*                    INC4 field of LINEDATA) has been added to keep  */
/*                    track of whether the coordinate values should   */
/*                    be incremented or decremented.                  */
/*                                                                    */
/**********************************************************************/
  {  short Temp;

     if (LineData->SlopeType == 0)
       InitializeLineData(StartX, StartY, EndX, EndY, X, Y, LineData);

     if (LineData->SlopeType == 1)
       {  Temp = StartX;
          StartX = StartY;
          StartY = Temp;

          Temp = EndX;
          EndX = EndY;
          EndY = Temp;

          Temp = *X;
          *X = *Y;
          *Y = Temp;
       }

     if ((LineData->Octent == 5) || (LineData->Octent == 8))
       {  *Y += LineData->Inc4;
          if (((StartX <= EndX) && (LineData->d >= 0)) || ((StartX >
            EndX) && (LineData->d <= 0)))
            {  if (((StartX >= EndX) && (LineData->dx <= 0)) ||
                ((StartX < EndX) && (LineData->dx >= 0)))
                 LineData->d -= LineData->Inc1;
               else
                 {  *X += LineData->Inc5;
                    LineData->d += LineData->Inc2;
                 }
            }
          else
            {  if (((StartX >= EndX) && (LineData->dx >= 0)) ||
                ((StartX < EndX) && (LineData->dx <= 0)))
                 LineData->d += LineData->Inc1;
               else
                 {  *X += LineData->Inc5;
                    LineData->d -= LineData->Inc3;
                 }
            }
       }

     else if ((LineData->Octent == 1) || (LineData->Octent == 4))
       {  *Y += LineData->Inc4;
          if (((StartX <= EndX) && (LineData->d <= 0)) || ((StartX >
            EndX) && (LineData->d >= 0)))
            {  if (((StartX >= EndX) && (LineData->dx <= 0)) ||
                ((StartX < EndX) && (LineData->dx >= 0)))
                 LineData->d += LineData->Inc1;
               else
                 {  *X += LineData->Inc5;
                    LineData->d -= LineData->Inc2;
                 }
            }
          else
            {  if (((StartX >= EndX) && (LineData->dx >= 0)) ||
                ((StartX < EndX) && (LineData->dx <= 0)))
                 LineData->d += LineData->Inc1;
               else
                 {  *X += LineData->Inc5;
                    LineData->d += LineData->Inc3;
                 }
            }
       }

     if (LineData->SlopeType == 1)
       {  Temp = *X;
          *X = *Y;
          *Y = Temp;
       }

  }


void  InitializeLineData(short StartX, short StartY, short EndX,
   short EndY, short *X, short *Y, struct BreshenhamData *LineData)
/**********************************************************************/
/*                                                                    */
/*  PURPOSE:    Initializes the local variables for uses by the       */
/*              implementation of Breshenham's Algorithm contained    */
/*              in the function GETNEXTCELLCOORDINATE.                */
/*                                                                    */
/*  ARGUMENTS:  (STARTX, STARTY) and (ENDX, ENDY) are the coordinates */
/*              of the two cells that identify the endpoints of the   */
/*              line segment being traced by this algorithm.  X and   */
/*              Y are pointers to variables that on input contain     */
/*              either (1) the coordinates of the last cell in the    */
/*              (STARTX, STARTY)-to-(ENDX, ENDY) line segment that    */
/*              was identified by this function, or (2) are undefined */
/*              (if no previous cell was identified via an earlier    */
/*              call to this function).  On output, X and Y contain   */
/*              the coordinates of the new cell identified by this    */
/*              function.                                             */
/*                                                                    */
/*              LINEDATA is a pointer to a structure that contains    */
/*              the data used by Breshenham's Algorithm.  This data   */
/*              should not be altered between calls to this function. */
/*              Note that when this function is called for the first  */
/*              time for any particular line segment, the SLOPETYPE   */
/*              field on LINEDATA should be set to zero (all other    */
/*              fields can be left undefined).                        */
/*                                                                    */
/*  RETURNS:    Void.                                                 */
/*                                                                    */
/*  SIDE        X and Y are assigned the values of STARTX and STARY   */
/*    EFFECTS:  (respectively) and the LINEDATE structure is updated  */
/*              to contain the initial values used by Breshenham's    */
/*              algorithm.                                            */
/*                                                                    */
/*  ALGORITHM:  This function uses a slightly modified version of the */
/*              implementation of Breshenham's algorithm shown in the */
/*              flow chart on page 595 of Nabajyoti Barkakati's book, */
/*              THE WAITE GROUP'S MICROSOFT MACRO ASSEMBLER BIBLE     */
/*              (1990).  The modifications made to the algorithm are  */
/*              as follows:                                           */
/*                                                                    */
/*                (1) No I/O takes place, this function simply        */
/*                    identfies cells in along the (STARTX, STARTY)   */
/*                    to (ENDX, ENDY) line.  This results in the      */
/*                    elimination of any code designed to perform     */
/*                    the output functions implied in Barkakati's     */
/*                    flowchart.                                      */
/*                                                                    */
/*                (2) Each call to this function identifies only one  */
/*                    cell that lies along the (STARTX, STARTY) to    */
/*                    (ENDX, ENDY) line (unlike the algorithm in the  */
/*                    flow chart, which loops through all cells in    */
/*                    the line segment).  This eliminates the final   */
/*                    looping mechanism shown in Barkakati's flow     */
/*                    chart and neccissitates the use of the LINE-    */
/*                    DATA structure, so that subsequent calls to     */
/*                    this function will have access to the local     */
/*                    variables created by the function durring the   */
/*                    preceeding iteration.                           */
/*                                                                    */
/*                (3) The algorithm described in Barkakati's flow-    */
/*                    chart is designed to switch the direction of    */
/*                    the line being drawn (i.e., draw a line from    */
/*                    (ENDX, ENDY) to (STARTX, STARTY) rather than    */
/*                    the other way around) to ensure that the        */
/*                    coordinate altered on each iteration is always  */
/*                    incremented rather than incremented for some    */
/*                    line segements and decremented for others       */
/*                    (depending on the line segment's slope).  This  */
/*                    works well from an efficency point of view      */
/*                    but is not appropriate for conducting linear    */
/*                    viewshed analyses.  Thus, the implementation    */
/*                    of Breshenham's Algorithm used in this function */
/*                    preserves the original direction of the         */
/*                    (STARTX, STARTY)-to-(ENDX, ENDY) line.  This    */
/*                    requires keeping track of whether to increment  */
/*                    or decrement the coordinates, and requires      */
/*                    testing the accumulated error value for both    */
/*                    positive and negative variations.  Thus, some   */
/*                    of the conditionals in this function are more   */
/*                    complex than those shown in Barkakati's flow-   */
/*                    chart, and an additional local variable (the    */
/*                    INC4 field of LINEDATA) has been added to keep  */
/*                    track of whether the coordinate values should   */
/*                    be incremented or decremented.                  */
/*                                                                    */
/**********************************************************************/
  {  short Temp;

     *X = StartX;
     *Y = StartY;

     LineData->dx = abs(StartX - EndX);
     LineData->dy = abs(StartY - EndY);

     if (LineData->dx > LineData->dy)
       {  LineData->SlopeType = 1;

          Temp = LineData->dx;
          LineData->dx = LineData->dy;
          LineData->dy = Temp;

          Temp = StartX;
          StartX = StartY;
          StartY = Temp;

          Temp = EndX;
          EndX = EndY;
          EndY = Temp;
       }
     else LineData->SlopeType = -1;

     if (StartY > EndY)
       {  LineData->dy = StartY - EndY;                     /*    C    */
          if (StartX >= EndX)                               /*  Upper  */
            {  LineData->d = -1 * ((2 * LineData->dx) -
                 LineData->dy);
               LineData->Inc1 = -2 * (LineData->dx);
               LineData->Inc2 = -2 * (LineData->dx - LineData->dy);
               LineData->Inc3 = -2 * (LineData->dx + LineData->dy);
               LineData->Inc4 = -1;
               LineData->Inc5 = -1;
               LineData->Octent = 5;
            }
          else                                              /*  Lower  */
            {  LineData->d = 1 * ((2 * LineData->dx) -
                 LineData->dy);
               LineData->Inc1 = 2 * (LineData->dx);
               LineData->Inc2 = 2 * (LineData->dx + LineData->dy);
               LineData->Inc3 = 2 * (LineData->dx - LineData->dy);
               LineData->Inc4 = -1;
               LineData->Inc5 = 1;
               LineData->Octent = 4;
            }
       }

     else
       {  LineData->dy = EndY - StartY;                     /*   D     */
          if (StartX >= EndX)                               /*  Upper  */
            {  LineData->d = -1 * ((2 * LineData->dx) -
                 LineData->dy);
               LineData->Inc1 = -2 * (LineData->dx);
               LineData->Inc2 = -2 * (LineData->dx - LineData->dy);
               LineData->Inc3 = -2 * (LineData->dx + LineData->dy);
               LineData->Inc4 = 1;
               LineData->Inc5 = -1;
               LineData->Octent = 8;
            }
          else                                              /*  Lower  */
            {  LineData->d = 1 * ((2 * LineData->dx) -
                 LineData->dy);
               LineData->Inc1 = 2 * (LineData->dx);
               LineData->Inc2 = 2 * (LineData->dx + LineData->dy);
               LineData->Inc3 = 2 * (LineData->dx - LineData->dy);
               LineData->Inc4 = 1;
               LineData->Inc5 = 1;
               LineData->Octent = 1;
            }
       }
  }
