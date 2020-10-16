#include<bits/stdc++.h>
#include<unistd.h>
using namespace std;
#ifdef DEB
#define D if(1)
#else
#define D if(0)
#endif

#define fo(a,b) for(int a=0;a<(b);++a)
using ll = long long;

const int LEN = 5000;
ll t;

#define TIME_P "%lld%s"
#define TIME(a) ((a)<180?a:(a)/60<180?a/60:a/60/60),((a)<180?"s":(a)/60<180?"min":"h")

#define ERR(a,b) {sprintf(out,"{\"name\":\"error\",\"color\":\"#FF0000\",\"full_text\":\"%s\"}" b,a);return;}
void loadOsdd(char * out)
{
	*out=0;
	static char color[LEN],line[LEN];
	FILE * f = fopen(".osdd_last","r");
	if(!f) ERR("Open f",",");
	ll ti;
	fscanf(f,"%lld",&ti);
	ti = t-ti;
	for(int i=0;fscanf(f," %s%[^\n]",color,line)==2;i++)
	{
		if(line[1]) 
		{
			out+=sprintf(out,"{\"name\":\"osdd%d\",\"color\":\"#%s\",\"full_text\":\"",i,color);
			if(!i) 
				out+=sprintf(out,"[" TIME_P "] ",TIME(ti));
			out+=sprintf(out,"%s\"},",line+1);
		}
		
	}
	fclose(f);
}
void loadMail(char * out)
{
	out[0]=0;
	FILE * f = fopen(".cm","r");
	if(!f) ERR("Open f",",");
	ll lastUpTime=0;
	int newMails=0;
	if(fscanf(f,"%lld%d",&lastUpTime,&newMails)!=2) ERR("read",",");
	ll delay = t-lastUpTime;
	if(-5 < delay && delay > 90)
		if(newMails)
			out += sprintf(out,"{\"name\":\"mail\",\"color\":\"#%s\",\"full_text\":\"NO CONNECTION " TIME_P " [%d]\"},",t%2?"FF0000":"3333FF",TIME(delay),newMails);
		else
			out += sprintf(out,"{\"name\":\"mail\",\"color\":\"#FF0000\",\"full_text\":\"NO CONNECTION " TIME_P "\"},",TIME(delay));
	else 
		if(newMails)
			out += sprintf(out,"{\"name\":\"mail\",\"color\":\"#%s\",\"full_text\":\"[%d NEW]\"},",t%2?"FF7000":"3333FF",newMails);
		else
			out += sprintf(out,"{\"name\":\"mail\",\"color\":\"#00FF00\",\"full_text\":\"OK\"},");
	fclose(f);
	f = fopen(".offlineimap.log","r");
	if(!f) ERR("Open IMAP log",",");
	char in [123];
	if(fscanf(f,"%100s",in)!=1) ERR("read",",");
	if(strcmp(in,"DOING")==0)
		out += sprintf(out,"{\"name\":\"imap\",\"color\":\"#%s\",\"full_text\":\"%s\"},","00FF00","IMAP");
	if(strcmp(in,"WAITING")==0)
		out += sprintf(out,"{\"name\":\"imap\",\"color\":\"#%s\",\"full_text\":\"%s\"},","FF0000","IMAP");
	int val;
	if(sscanf(in,"%d",&val))
	{
		if(val)
		out += sprintf(out,"{\"name\":\"imap\",\"color\":\"#%s\",\"full_text\":\"IMAP %d\"},","FF0000",val);
	}
	fclose(f);

}
char i3status_aloc[LEN];
char mail[LEN];
char osdd[LEN];

int main()
{
	assert(chdir(getenv("HOME"))==0);
	FILE * f = popen("i3status -c ~/.config/i3/i3status.conf","r");
	char * i3status;
	while(fgets(i3status=i3status_aloc,LEN-2,f))
	{
		{
			ll lastt = t;
			t=time(0);
			if(t==lastt) t++;

		}
		if(!memcmp(i3status,"{\"ver",sizeof("{\"ver")-1)||!strcmp(i3status,"[\n")||!strcmp(i3status,"]\n"))
		{
			printf("%s",i3status);
			fprintf(stderr,"%s",i3status);
		}
		else
		{
			if(i3status[0]==',') {putc(*i3status,stderr);putchar(i3status++[0]);}
			if(i3status[0]=='[') {putc(*i3status,stderr);putchar(i3status++[0]);}
			loadMail(mail);
			loadOsdd(osdd);
			printf("%s%s%s",osdd,mail,i3status);
			fprintf(stderr,"%s%s%s",osdd,mail,i3status);
		}
		fflush(stdout);
		fflush(stderr);
	}
	return 0;
}

