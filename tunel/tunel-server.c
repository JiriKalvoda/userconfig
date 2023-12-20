#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <pthread.h>
#include <unistd.h>
#include <unistd.h>
#include <stdbool.h>
#include <sys/types.h>
#include <signal.h>


#ifdef DEB
#define D if(1)
#else
#define D if(0)
#endif

#define fo(a,b) for(int a=0;a<(b);++a)
typedef long long ll;

int ppid;

void end()
{
	//char exe [1000];
	//sprintf(exe,"kill %d", ppid);
	//printf("%s\n",exe);
	//fflush(stdout);
	//system(exe);
	fflush(stdout);
	sleep(1);
	kill(ppid,15);
	exit(0);
}
int main(int argc, char ** argv)
{
	ppid = getppid();
	printf("ppid = %d\n",ppid);
	fflush(stdout);
	for(int i=1;i<argc;i++) if(!strcmp(argv[i],"--")) argc = i;
	bool no_end=0;
	if(argc>1 && !strcmp(argv[1],"no")) no_end=1;

	int timeout = 90;
	if(argc>1 && atoi(argv[1])) timeout = atoi(argv[1]);

	while(1)
	{
		fd_set rfds;
		FD_ZERO(&rfds);
		FD_SET(0, &rfds);

		struct timeval tv;
		tv.tv_sec = timeout;
		tv.tv_usec = 0;

		//printf("tv = %d\n",tv.tv_sec);
		int r = select(1, &rfds, NULL, NULL, &tv);

		if(!r && !no_end)
		{
			printf("%lld: Timeout (%d)\n", (long long)time(NULL), tv.tv_sec);
			end();
		}
		//printf("a\n");
		int ch = getchar();
		if(ch<0)
		{
			printf("%lld: EOF\n", (long long)time(NULL));
			end();
		}
		printf("%lld: Server read char %d\n", (long long)time(NULL), ch);
		fflush(stdout);
		//printf("|%d|\n",ch);
	}
	return 0;
}
