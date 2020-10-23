#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>

const char adr [] = "amixer sget Master";
char out[1234];
int main(int argc,char ** argv)
{
	//setuid(0);
	FILE * f = popen(adr,"r");
	double realAct;
	int act;
	char str[1000];
	fscanf(f,"%[^[][%d%%] [%lf",str,&act,&realAct);
	//printf("%d%% %.1lfdB\n[",act,realAct);
	//printf("%d%%d\n[",int(100*act/log(lightMax)+0.5),realAct);
	//for(double i=0;i<100;i+=5)
		//printf("%s",act<=i?"−":"+");
	//printf("]");
	sprintf(out,"osdc --color=red --log=0 \"%d%% %.1lfdB\" --percent=%d",act,realAct,act);
	system(out);
	fclose(f);
}
