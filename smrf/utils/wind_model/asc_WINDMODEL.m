function asc_WINDMODEL(basename,angle,range,dmax,sepdist,inst,path)
%{
Runs WINDMODEL.m wrapper function created by Andrew Hedrick.  The wrapper 
calls C-code written by Adam Winstral which creates terrain parameters for
wind redistribution of snow from a DEM of a given pixel size.

basename    = name of centimeter .asc DEM file to be used w/o extension (string).
angle       = middle upwind direction around which to run model (degrees).
range       = size of upwind angle directions to analyze* (degrees).
    * Will be in increments of 5 degrees.
dmax        = length of outlying upwind search vector (meters).
sepdist     = length of local max upwind slope search vector (meters). 
path        = location where files will end up (string).
    Example: '/home/......../Modelrun_2m'
%}

%% Import elevation data from DEM
filename=[basename '.asc'];
[Z,R]=arcgridread(filename); %Import refmat info

%% Define all model and wrapper inputs.

Pix=R(2)/100; % Cell size converted to meters.
wid=30; % Defined window width for windower function (degree).
inc=5; % Defined increment between successive calculations (degrees).
h=num2str((inst).*100); % Anemometer height in centimeters
dmx=num2str((dmax).*100); % dmax search vector in centimeters.
sep=num2str((sepdist).*100); % Separation distance string in centimeters.
Sep=num2str(sepdist); %Separation distance string in meters
swa=angle-range/2:inc:angle+range/2; % All angles that model will consider.
dir=min(swa)+wid/2:inc:max(swa)-wid/2; % Vector of final windowed directions. 
for j=1:length(swa); %Account for circular nature of wind directions.
    if (swa(j)<0)
        swa(j)=swa(j)+360;
    end
end
if sum(ismember(swa,0)) == 1 && sum(ismember(swa,360)) == 1 % pk modified to take out 360 if 0 is there.
    swa(swa==360) = [];
end
%% Run model over range of wind directions.
for i=1:length(swa);
    v=num2str(swa(i));
    system(['./maxus -a ' v ' -z ' dmx ' -d ' filename ...
        ' -h ' h]);
    system(['./topobreak -s ' sep ' -a ' v ' -d ' filename]);
    %Organize file structure and prepare filenames for windower function.    
    if (0<=swa(i)<360)
        system(['mv tbreak' sep '_' v '.asc tbreak' Sep '_' v '.asc']);
    elseif (swa(i)==360)
        system(['mv tbreak' sep '_0.asc tbreak' Sep '_0.asc']);
    elseif (swa(i)<0) %For less than zero angles
        system(['mv tbreak' sep '_' num2str(swa(i)) '.asc tbreak' Sep...
            '_' num2str(swa(i)) '.asc']);
    elseif (swa(i)>360)              %For greater than 360 angles
        system(['mv tbreak' sep '_' num2str(swa(i)) '.asc tbreak' Sep...
            '_' num2str(swa(i)-360) '.asc']);
    end
end
prefix1='maxus'; %Provide proper name for C-code
prefix2=['tbreak' Sep];
dir1=num2str(min(dir)); %Determine min angle to average around
for j=1:length(dir1); % Change negative values to circular degrees.
    if (dir1(j)<0)
        dir1(j)=dir1(j)+360;
    end
end
dir2=num2str(max(dir)); % Determine max angle to average around
system(['./windower -i ' num2str(inc) ' -w ' num2str(wid) ' -a ' dir1 ',' dir2 ' -p ' prefix1]);
system(['./windower -i ' num2str(inc) ' -w ' num2str(wid) ' -a ' dir1 ',' dir2 ' -p ' prefix2]);

%% Clean up step
%{ 
Rename all maxus files to include the dmax value while moving all the files
to the output path defined above.  

Next, read the files into matlab arrays one by one and crop out the buffer
regions.

Finally, recreate .asc files of each calculation w/o the buffer and
overwrite the original file.
%}

%Move input DEM to path.
% system(['mv ' basename '.asc ' path]);

[y1,x1]=size(Z); %Get dimensions of full array.
xmin=R(3)/100; %Convert values back to meters
ymax=R(6)/100; %    "       "   "    "    "
x=xmin+0.5*Pix:Pix:x1*Pix+xmin-0.5*Pix; %Define x vector of Easting
y=ymax-y1*Pix:Pix:ymax-Pix; %Define y vector of Northing.
c=((dmax)*0.8)/Pix; % Define cropped buffer to be 80% of dmax (pixels).
xISA=x(c:end-c-2); %Cropped Easting vector
yISA=y(c:end-c-2); %Cropped Northing vector
[X,Y]=meshgrid(xISA,fliplr(yISA)); %Create mesh arrays of Easting and Northing.
for i=1:length(swa);
    v=num2str(swa(i));
    %Define the path and name of new files:
    maxus=[path '/maxus' num2str(dmax) '_' v '.asc'];
    maxusavg=[path '/maxus' num2str(dmax) '_' num2str(wid) '.' v '.asc'];
    tbreak=[path '/tbreak' Sep '_' v '.asc'];
    tbreakavg=[path '/tbreak' Sep '_' num2str(wid) '.' v '.asc'];
    system(['mv maxus_' v '.asc ' maxus]);%Rename files.
    system(['mv maxus_' num2str(wid) '.' v '.asc ' maxusavg]);
    system(['mv tbreak' Sep '_' v '.asc ' tbreak]);
    system(['mv tbreak' Sep '_' num2str(wid) '.' v '.asc ' tbreakavg]);
    m=arcgridread(maxus); %Read maxus files into and array
    mavg=arcgridread(maxusavg); %Read averaged maxus files into an array.
    t=arcgridread(tbreak); %Read topobreak files into an array.
    tavg=arcgridread(tbreakavg); %Read averaged topobreak files into an array.
    mcrop=m(c:end-c-2,c:end-c-2); %Cropped maxus array.
    mavgcrop=mavg(c:end-c-2,c:end-c-2); %Cropped averaged maxus array.
    tcrop=t(c:end-c-2,c:end-c-2); %Cropped topobreak array.
    tavgcrop=tavg(c:end-c-2,c:end-c-2); %Cropped averaged topobreak array.
    arcgridwrite(maxus,X,Y,flipud(mcrop)); %Overwrite original file.
    arcgridwrite(maxusavg,X,Y,flipud(mavgcrop)); %Overwrite original file.
    arcgridwrite(tbreak,X,Y,flipud(tcrop)); %Overwrite original file.
    arcgridwrite(tbreakavg,X,Y,flipud(tavgcrop)); %Overwrite original file.
end
    
