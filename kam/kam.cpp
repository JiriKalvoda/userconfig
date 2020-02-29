#include <sys/types.h>
#include<map>
#include<string>
#include<cstdio>
using namespace std;
#ifdef DEB
#define D if(1)
#else
#define D if(0)
#endif


const int LEN = 1234;

using ll = long long;
char user [] = "jirikalvoda";
char domain [] = "kam.mff.cuni.cz";

int main(int argc,char ** argv)
{
	char server [LEN];
	char serverIN [LEN];
	int port=22;
	map<string,string> par;
	for(int i=1,j=0;i<argc;i++)
	{
		if(argv[i][0]!='-')
		{
			if(j==0) strcpy(server,argv[i]);
			if(j==0) strcpy(serverIN,argv[i]);
			j++;
		}
		else
		{
			int r=-1;
			for(int k=0;argv[i][k];k++)
				if(argv[i][k]=='=') 
				{
					r=k;break;
				}
			if(r==-1)
				par[argv[i]]="TRUE";
			else
				par[string(argv[i]).substr(0,r)] = argv[i]+r+1;
		}
	}
	//D
	//{
	//	for(auto it : par) printf("%s:%s|\n",it.first.c_str(),it.second);
	//}
	if(strcmp(server,"kam")==0 || strcmp(server,"")==0)
		sprintf(server,"%s",domain);
	else
	{
		if(atoi(server))
		{
			port = atoi(server);
			sprintf(server,"localhost");
		}
		else
			sprintf(server,"%s.%s",server,domain);
	}
	char exe [LEN];
	if(par["-c"]!="")
	{
		int portC=atoi(par["-c"].c_str());
		sprintf(exe,"sudo ssh -L %d:%s:22"
				" %s@sneaky.%s -p 443 \" echo START OK;read -p run \"" 
				,portC,server,user,domain);
		
	}
	else if(par["-m"]!="")
	{
		char from[LEN],to[LEN];
		if(par["-home"]!="")
		{
			sprintf(from,"/home/%s",user);
			sprintf(to,"~/kam/home");
		}
		else if(par["-m"]=="TRUE")
			sprintf(from,"/aux/%s",user);
		else
			sprintf(from,"%s",par["-m"].c_str());
		if(par["-home"]!="")
			;
		else if(par["-n"]=="")
		{
			sprintf(to,"~/kam/$NAME");
			sprintf(exe,
			"NAME=`ssh -p %d %s@%s 's=\"\\\\h\";echo ${s@P}'`;"
			"echo server name is $NAME;",
				port,user,server
			);
		}
		else
			sprintf(to,"%s",par["-n"].c_str());
		sprintf(exe,
			"%smkdir %s;"
			"sshfs -p %d %s@%s:%s %s",
			exe,to,port,user,server,from,to);
	}
	else if(par["-u"]!="")
	{
		char to[LEN];
		if(par["-home"]!="")
			sprintf(to,"~/kam/home");
		else if(par["-n"]=="")
		{
			sprintf(to,"~/kam/$NAME");
			sprintf(exe,
			"NAME=`ssh -p %d %s@%s 's=\"\\\\h\";echo ${s@P}'`;"
			"echo server name is $NAME;",
				port,user,server
			);
		}
		else
			sprintf(to,"%s",par["-n"].c_str());
		sprintf(exe,"%sfusermount -u %s; rmdir %s",exe,to,to);
	}
	else
	{
		sprintf(exe,"ssh %s@%s -p %d",user,server,port);
	}
	system("bash -i -c promt");
	puts(exe);
	system(exe);
	return 0;
}

