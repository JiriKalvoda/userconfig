#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>

char logName[1234];
#define LOG(a...) {FILE *f = fopen(logName,"w");fprintf(f,a);fclose(f);}
using ll = long long;
int pipeFd;

void initPipe()
{
	char fileName[1000];
	sprintf(fileName,"%s/.offlineimap.pipe",getenv("HOME"));
	printf("make pipe: %s\n",fileName);
	remove(fileName);
	assert(mkfifo(fileName, 0666)==0);
	close(0);
	pipeFd = open(fileName, O_RDONLY);
	assert(pipeFd == 0);
	open(fileName, O_WRONLY);
}

#include <dirent.h>
#include <stdio.h>

struct Maildir
{
	char name[1000];
	int ctotal=-1;
	int cnew=-1;
	bool needAct=1;
};
void getDir
{
    DIR *d;
    struct dirent *dir;
    d = opendir(".");
    if (d)
    {
        while ((dir = readdir(d)) != NULL)
        {
            printf("%s\n", dir->d_name);
        }
        closedir(d);
    }
    return(0);
}

int ret=0;
int main()
{
	assert(chdir(getenv("HOME"))==0);
	initPipe();
	sprintf(logName,"%s/.offlineimap.log",getenv("HOME"));
	char in[1234];
	int lNew=-1,lTotal=-1;
	int aNew=-1,aTotal=-1;
	while(scanf(" %[^\n]",in)==1)
	{
		{
			FILE * f = fopen(".cm","r");
			if(f)
			{
				ll t;
				fscanf(f,"%lld%d%d",&t,&aNew,&aTotal);
				fclose(f);
			}
		}
		if(strcmp(in,"if RUN") || aNew!=lNew || aTotal!=lTotal)
		{
			LOG("DOING '%s'\n",in);
			ret = system("offlineimap 2> ~/.offlineimap.output");
			LOG("%d\n",ret);
		}
		else
			LOG("%d\n",ret);
		lNew=aNew;lTotal=aTotal;
	}

}
