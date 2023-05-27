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
	setuid(0);
	for(int adri=0;adri<adrlen;adri++)
	{
		{
			FILE * f = fopen(adr[adri],"r");
			if(!f) goto nextAdr;
			int realAct;
			fscanf(f,"%d",&realAct);
			double act=log(realAct);
			if(act<0) act = 0;
			printf("%d%% %d\n[",int(100*act/log(lightMax)+0.5),realAct);
			for(double i=0;i<log(lightMax);i+=0.3)
				printf("%s",act<i?"−":"+");
			printf("]");
			fclose(f);
			return 0;
		}
		nextAdr:;
	}
	return 1;

}
