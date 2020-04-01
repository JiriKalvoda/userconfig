#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>
#include <cstring>

const double redMin =  1000;
const double redMax = 10000;
const double gammaMin =  0.1;
const double gammaMax = 2;

int main(int argc,char ** argv)
{
	if(argc<3) return 100;
	char * name = argv[1];
	for(int i=0;name[i];i++)
	{
		if(i>300 ||
			!( name[i]=='/' 
			|| (name[i]>='A' && name[i]<='Z')
			|| (name[i]>='a' && name[i]<='z')
			|| (name[i]>='0' && name[i]<='9')
			|| name[i] == '-' || name[i] == '_'
			)
		  )
			exit(101);
	}
	setuid(0);
	char scall[1000];
	if(strcmp(argv[2],"Y")==0)
		sprintf(scall,"hdparm -Y /dev/%s",name);
	else
	if(strcmp(argv[2],"off")==0)
	{
		printf("doing POWER-OFF /dev/%s\n",name);
		sprintf(scall,"udisksctl power-off -b /dev/%s",name);
	}
	else if(strcmp(argv[2],"umount")==0)
	{
		printf("doing umount /dev/%s\n",name);
		sprintf(scall,"umount /dev/%s?*",name);
	}
	else
	{
		int s = atoi(argv[2]);
		sprintf(scall,"hdparm -S %d /dev/%s",s,name);
	}
	fflush(stdout);
	system(scall);
}
