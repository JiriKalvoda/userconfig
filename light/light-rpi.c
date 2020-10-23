#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>

const int lightMin = 2;
const int lightMax = 100;

void writeB(int val)
{
	char exec [1234];
	snprintf(exec,1230,"rpi-backlight -b %d",val);
	system(exec);
}
int main(int argc,char ** argv)
{
	if(argc<=2) return 100;
	setuid(0);
	{
		{
			if(argv[1][0]=='H')
			{
				writeB(atoi(argv[2]));
				return 0;
			}
			double argv2 = atof(argv[2]);
			double light;
			if(argv[1][0]=='=')
				light = argv2;
			else
			{
				FILE * f = popen("rpi-backlight --get-brightness","r");
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
			writeB(intLight);
			return notInLimit;
		}
		nextAdr:;
	}
}
