#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <map>
#include <string>
#include <thread>

char logName[1234];
#define LOG(a...) {FILE *f = fopen(logName,"w");fprintf(f,a);fclose(f);}
using ll = long long;
int pipeFd;

void openPipe(char * fileName)
{
	int fd = open(fileName, O_WRONLY);
	FILE * f = fdopen(fd,"w");
	fprintf(f,"if RUN\n");
	fflush(f);
}
void initPipe()
{
	char fileName[1000];
	sprintf(fileName,"%s/.offlineimap.pipe",getenv("HOME"));
	printf("make pipe: %s\n",fileName);
	remove(fileName);
	assert(mkfifo(fileName, 0666)==0);
	std::thread th(openPipe,fileName);
	close(0);
	pipeFd = open(fileName, O_RDONLY);
	assert(pipeFd == 0);
	th.join();
}

#include <dirent.h>
#include <stdio.h>

struct Maildir
{
	int ctotal=-1;
	int cnew=-1;
	bool needAct=0;
};
std::map<std::string,Maildir> dirs;

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
				int ctotal,cnew;
				char name [1234];
				int r=0;
				while((r=fscanf(f," %[^>]>%d%d",name,&cnew,&ctotal))==3)
				{
					if(name[1]==0) strcpy(name,"<INBOX");
					//printf("|%s| %d %d\n",name+1,cnew,ctotal);
					auto &it  = dirs[name+1];
					if(it.ctotal != ctotal || it.cnew != cnew)
						it.needAct=1;
					it.ctotal=ctotal;
					it.cnew=cnew;
				}
				//printf("R=%d\n",r);
				fclose(f);
			}
			//else printf("NO .cm !!!\n");
		}
		if(strcmp(in,"<if> RUN"))
		{
			char name [1234];
			int r=0;
			r=sscanf(in," %[^>]>",name);
			if(name[1]==0) strcpy(name,"<.INBOX");
			//printf("IN |%s| |%s|\n",name+2,in);
			auto &it  = dirs[name+2];
			it.needAct=1;
			dirs["Sent"].needAct=1;
		}
		bool run=0;
		for(auto & it : dirs)
			if(it.second.needAct) run=1;
		if(run) 
		{
			LOG("DOING '%s'\n",in);
			char sys[12345];
			char * sysit = sys;
			sysit += sprintf(sysit,"offlineimap 2> ~/.offlineimap.output -f ");
			for(auto it : dirs)
				if(it.second.needAct)
					sysit += sprintf(sysit,"%s,",it.first.c_str());
			//printf("%s\n",sys);
			ret = system(sys);
			if(ret==0)
				for(auto & it : dirs)
					it.second.needAct=0;


			LOG("%d\n",ret);
		}
		else
			LOG("%d\n",ret);
		lNew=aNew;lTotal=aTotal;
	}

}
