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
	if(argc<2) return 100;
	setuid(0);
	long long f = atoll(argv[1]);
	f *= 1000;
	char scall[1000];
	sprintf(scall,"cpupower frequency-set --max %lld",f);
	system(scall);
}
