#include <assert.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>

#include <semaphore.h>
#include <pthread.h>



char * file = ".wacom/button";

sem_t sem;
volatile int x=0, y=0;

const int C = 2;

void * thread()
{
	while(1)
	{
		//printf("T\n");
		if(!x &&  !y) sem_wait(&sem);
		struct timespec ts;
		{
		assert(!clock_gettime(CLOCK_REALTIME, &ts));
		long long x = ts.tv_nsec + 50000000;
		ts.tv_sec +=  x/1000000000;
		ts.tv_nsec = x%1000000000;
		}
		if(sem_timedwait(&sem, &ts))
		{
			int X = x;
			int Y = y;
			x=y=0;
			//printf("%d %d\n",X,Y);
			if(X*X + Y*Y > 10*10)
			{
				if(X<0 && -(-X)/2 <= Y && Y <= (-X)/2)
					system("(xdotool mousedown 2;  xdotool mouseup 2) &");
				else
				if(X>0 && -(X)/C <= Y && Y <= (X)/C)
					system("wacom-config next &");
				else
				if(Y<0 && -(-Y)/2 <= X && X <= (-Y)/2)
					system("onboard &");
				else
				if(Y>0 && -(Y)/C <= X && X <= (Y)/C)
					system("wacom-config output 0");
				else
				if(0<X && 0<Y)
					system("wacom-config output 1");
				else
				if(X<0 && Y<0)
					system("wacom-config outputmapped");
				else
				if(X>0 && Y<0)
					system("wacom-config map 0");
				else
				if(X<0 && Y>0)
					system("wacom-config map 1");
			}
		}
	}
}

int main(int argc, char ** argv)
{
	assert(!chdir(getenv("HOME")));
	sem_init(&sem, 0, 0);
	pthread_t th;
	pthread_create(&th, NULL, thread, NULL);
	unlink(file);
	assert(!mkfifo(file, 0600));
	printf("ZDE0\n");
	int rfd = open(file,O_RDONLY);
	printf("ZDE1\n");
	int wfd = open(file,O_WRONLY);
	printf("ZDE2\n");
	assert(wfd > 0 && rfd > 0);
	while(1)
	{
		char in;
		assert(1==read(rfd,&in,1));
		printf("%c\n", in);
		if(in=='4') y--;
		if(in=='5') y++;
		if(in=='6') x++;
		if(in=='7') x--;
		sem_post(&sem);
	}
	pthread_join(th, NULL);
	return 0;
}
