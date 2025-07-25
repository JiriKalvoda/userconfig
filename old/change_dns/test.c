#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#ifdef DEB
#define D if(1)
#else
#define D if(0)
#endif

#define fo(a,b) for(int a=0;a<(b);++a)
typedef long long ll;


int main(int argc, char ** argv)
{
	FILE * f = fopen("/etc/resolv.conf", "r");
	char c;
	while(fscanf(f, "%c", &c) == 1)
		printf("%c", c);
	return 0;
}
