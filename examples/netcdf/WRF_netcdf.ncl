load "/usr/lib/ncarg/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "/usr/lib/ncarg/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "/usr/lib/ncarg/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin

;---------------------------------------------------------------------
;---Input file, weight file, and grid information (WRF data)
;---------------------------------------------------------------------

; for remote access
fileName = "WRF_test.nc"
fname = "wrfout_d02_2015-03-02.nc"

print("File -- " + fileName)

;t = ispan(18,22,1)
lon = ispan(40,55,1)
lat = ispan(45,55,1)

;if (isfilepresent(fname))

    sfile = addfile(fname, "r")

    outDirName = "./"

    ;---------------------------------------------------------------------
    ;---Set up NetCDF output file
    ;---------------------------------------------------------------------

    ofile = outDirName + fileName

    system("/bin/rm -f " + ofile)                   ; remove any old version
    setfileoption("nc","Format","NetCDF4Classic")
    ncdf  = addfile(ofile,"c")                      ; create a new NetCDF

    ;---------------------------------------------------------------------
    ;---LAT LON HGT Time
    ;---------------------------------------------------------------------

    ;--- Times
    print("    Times...")
    ncdf->Times = sfile->Times

    ;--- Lat
    print("    XLAT...")
    ncdf->XLAT = sfile->XLAT(lat,lon)

    ;--- Long
    print("    XLONG...")
    ncdf->XLONG = sfile->XLONG(lat,lon)

    ;--- Terrain height
    print("    HGT...")
    ncdf->HGT = sfile->HGT(lat,lon)


    ;---------------------------------------------------------------------
    ;--- VARIABLES DESIRED
    ;---------------------------------------------------------------------


    ;--- Short wave down at surface
    ;print("    SWDOWN...")
    ;ncdf->SWDOWN = sfile->SWDOWN(:,lat,lon)

    ;--- Long wave down at surface
    print("    GLW...")
    ncdf->GLW = sfile->GLW(:,lat,lon)

    ;--- Temperature at 2m
    print("    T2...")
    ncdf->T2 = sfile->T2(:,lat,lon)

    ;--- Dew point 2m
    print("    DWPT...")
    ncdf->DWPT = sfile->DWPT(:,lat,lon)

    ;--- Precip accumulated
    print("    RAINNC...")
    ncdf->RAINNC = sfile->RAINNC(:,lat,lon)

    print("    CLDFRA...")
    ncdf->CLDFRA = sfile->CLDFRA(:,:,lat,lon)

    ;---------------------------------------------------------------------
    ;---WIND VARIABLES
    ;  10m U and V components of wind rotated to earth coordinates
    ;---------------------------------------------------------------------

    print("    WIND...")
    ncdf->UGRD = sfile->UGRD(:,lat,lon)
    ncdf->VGRD = sfile->UGRD(:,lat,lon)

;endif



end
