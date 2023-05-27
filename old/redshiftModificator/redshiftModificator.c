#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>

const double redMin =  1000;
const double redMax = 10000;
const double gammaMin =  0.1;
const double gammaMax = 2;

int main(int argc,char ** argv)
{
	if(argc<4) return 100;
	setuid(0);
	int disply = atoi(argv[1]);
	char configFile[1000];
	sprintf(configFile,"/home/jiri/.config/redshiftModificator/display%d",disply);
	printf("%s\n",configFile);;
	double red, gamma;
	{
		FILE * f = fopen(configFile,"r");
		if(!f || fscanf(f,"%lf%lf",&red,&gamma)!=2)
		{
			printf("BAD SCAN\n");
			red=6500;
			gamma=1;
		}
		if(f) fclose(f);
		else printf("FOPEN NULL\n");
	}
	char mod = argv[2][0];
	double val = atof(argv[3]);
	if(mod == '+')
		red += val;
	if(mod == '-')
		red -= val;
	if(mod == '=')
		red = val;
	if(mod == '<')
		gamma+= val;
	if(mod == '>')
		gamma-= val;
	if(mod == '~')
		gamma= val;
	if(red<1000 ) red = 1000;
	if(red>25000) red = 25000;
	if(gamma<0.1) gamma = 0.1;
	if(gamma>10) gamma = 10;
	char scall[1000];
	sprintf(scall,"redshift -O %lf -g %lf -m randr:crtc=%d",red,gamma,disply);
	system(scall);
	{
		FILE * f = fopen(configFile,"w");
		if(f)
		{
			fprintf(f,"%lf %lf\n",red,gamma);
			fclose(f);
		}
	}
}
