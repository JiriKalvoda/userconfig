#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#ifdef DEB
#define D if(1)
#else
#define D if(0)
#endif

#define fo(a,b) for(int a=0;a<(b);++a)
typedef long long ll;


int main(int argc, char ** argv)
{
	while(1)
	{
		printf("a");
		fflush(stdout);
		sleep(30);
	}
	return 0;
}
