#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>
#include "adr.h"

const int lightMin = 2;
const int lightMax = 937;
int main(int argc,char ** argv)
{
	if(argc<=2) return 100;
	setuid(0);
	if(argv[1][0]=='H')
	{
		FILE * f = fopen(adr[adri],"w");
		if(!f) goto nextAdr;
		fprintf(f,"%d",atoi(argv[2]));
		fclose(f);
		return 0;
	}
	double argv2 = atof(argv[2]);
	double light;
	if(argv[1][0]=='=')
		light = argv2;
	else
	{
		FILE * f = fopen(adr[adri],"r");
		if(!f) goto nextAdr;
		fprintf(f,"%d",atoi(argv[2]));
		int realAct;
		fscanf(f,"%d",&realAct);
		if(realAct<light) realAct=lightMin;
		double act=log(realAct);
		if(argv[1][0]=='+')
			light = act+argv2;
		else
		if(argv[1][0]=='-')
			light = act-argv2;
		else return 100;
		fclose(f);
	}
	int notInLimit=0;
	double realLight=pow(M_E,light);
	if(realLight>lightMax)
	{
		realLight=lightMax;
		notInLimit=1;
	}
	if(realLight<lightMin)
	{
		realLight=lightMin;
		notInLimit=1;
	}
	int intLight = realLight+0.7;
	FILE * f = fopen(adr[adri],"w");
	if(!f) goto nextAdr;
	//printf("light=%d\n",intLight);
	fprintf(f,"%d",intLight);
	fclose(f);
	//char exe [1000];
	//sprintf( exe,"echo %d  > /sys/devices/pci0000:00/0000:00:02.0/drm/card0/card0-eDP-1/intel_backlight/brightness",light);
	//system(exe);
	return notInLimit;
}
