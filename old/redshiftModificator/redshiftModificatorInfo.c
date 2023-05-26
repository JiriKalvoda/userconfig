#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>

const char adr [] = "/sys/devices/pci0000:00/0000:00:02.0/drm/card0/card0-eDP-1/intel_backlight/brightness";
const int lightMin = 2;
const int lightMax = 937;
int main(int argc,char ** argv)
{
	setuid(0);
	FILE * f = fopen(adr,"r");
	int realAct;
	fscanf(f,"%d",&realAct);
	double act=log(realAct);
	if(act<0) act = 0;
	printf("%d%% %d\n[",int(100*act/log(lightMax)+0.5),realAct);
	for(double i=0;i<log(lightMax);i+=0.3)
		printf("%s",act<i?"−":"+");
	printf("]");
	fclose(f);
}
