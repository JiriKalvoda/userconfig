#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>
#include "adr.h"

const int lightMin = 2;
const int lightMax = 100;
char out[1234];
int main(int argc,char ** argv)
{
	setuid(0);
	{
		{
			FILE * f = popen("rpi-backlight --get-brightness","r");
			if(!f) goto nextAdr;
			int realAct;
			fscanf(f,"%d",&realAct);
			double act=log(realAct);
			if(act<0) act = 0;
			//printf("%d%% %d\n[",int(100*act/log(lightMax)+0.5),realAct);
			//for(double i=0;i<log(lightMax);i+=0.3)
				//printf("%s",act<i?"−":"+");
			//printf("]");
			sprintf(out,"osdc --output=display --color=red --duration=500 --min-duration=1 \"%d%% %d\" --percent=%d",int(100*act/log(lightMax)+0.5),realAct,int(100*act/log(lightMax)+0.5));
			system(out);
			fclose(f);
			return 0;
		}
		nextAdr:;
	}
	return 1;

}
