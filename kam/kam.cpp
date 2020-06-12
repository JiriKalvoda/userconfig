#include <sys/types.h>
#include<map>
#include<string>
#include<cstring>
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
char domain [300] = "kam.mff.cuni.cz";
char help [] =
"KAM - ssh driver for kam.mff.cuni.cz servers\n"
"usage: kam [OPT] [SERVER/PORT]\n"
"\n"
"By default connect to main kam server by ssh.\n"
"If SERVER (string) is set, connection is made to SERVER.kam.mff.cuni.cz\n"
"'_' of the begin of SERVER is ignored (used for hinting not important server).\n"
"If PORT (number) is set, connection us made to localhost at PORT.\n"
"\n"
"OPT: -c=P        make ssh tunnel from SERVER by sneaky port 443 to port P\n"
"     -m          mount /aux/USER at DEVICE to ~/kam/SERVER_NAME\n"
"       -m=PATH   mount PATH instead of aux\n"
"       -home     mount ~ instead of aux to ~/kam/home\n"
"     -u          unmount ~/kam/SERVER_NAME\n"
"       -home     mount ~/kam/home\n"
"     -n=S        set SERVER_NAME to S manually (normal is used ask by ssh)\n"
"     -X          add option -X to ssh command (tunnel X server)\n"
"     -t=COMMAND  run COMMAND instead of bash\n"
"     -h --help   show this help\n"
"     -htop       run htop on every computation server\n"
"     -hint=W     autocomplete with W prefix"
;

char serversList [][123] = {
	"kamenolom",
	"kamenozrout",
	"kaminka",
	"kamna",
	"lomikamen",
	"_gimli",
	"_nikam",
	"_drahokam",
	"__camellia",
	"__camelot",
	"__kamenina",
	"__kaminek",
	"__kamoku",
	"__camarilla",
	"__carmina",
	"__corbu",
	"__kampelicka",
	"__kamran",
	"__tikam",
	"__camel",
	"__campfire",
	"__kamen",
	"__campari",
	"__kamzik",
	"__okamura",
	"__turing",
	"__atacama",
	"__kamber",
	"__kameyama",
	"__scam",
	"__scampo",
	"__smekam",
	"__caman",
	"__campbell",
	"__campione",
	"__comeon",
	"__hippocampus",
	"__kamase",
	"__kambrium",
	"__kamfen",
	"__kamil",
	"__kamyk",
	"__neklekam",
	"__ocampo",
	"__occam",
	"__predicament",
	"__sycamore",
	"__tokamak",
	"__camouflage",
	"__dekameron",
	"__kamarad",
	"__kampanila",
	"__cameo",
	"__camorra",
	"__kama",
	"__kamately",
	"__kameleon",
	"__secam",
	"__campus",
	"__kamakura",
	"__cambridge",
	"__camden",
	"__camaro",
	"__camembert",
	"__comeback",
	"__dekametr",
	"__eskamoter",
	"__kamacit",
	"__kamcatka",
	"__kamji",
""};

char posiblePar [][123] = {
	"-h ",
	"-help ",
	"-c=",
	"-m ",
	"-m=",
	"-home ",
	"-n=",
	"-X ",
	"-t=",
	"-htop ",
	"-hint=",
""};


int main(int argc,char ** argv)
{
	char server [LEN]="";
	char serverIN [LEN]="";
	int port=22;
	map<string,string> par;
	for(int i=1,j=0;i<argc;i++)
	{
		if(argv[i][0]!='-')
		{
			int p=0;
			while(argv[i][p]=='_') p++;
			if(j==0) strcpy(server,argv[i]+p);
			if(j==0) strcpy(serverIN,argv[i]+p);
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
			else if(!argv[i][r+1])
				par[string(argv[i]).substr(0,r)] = "NULL";
			else
				par[string(argv[i]).substr(0,r)] = argv[i]+r+1;
		}
	}
	if(strcmp(server,"gimli")==0)
	{
		strcpy(domain,"ms.mff.cuni.cz");
	}
	//D
	//{
	//	for(auto it : par) printf("%s:%s|\n",it.first.c_str(),it.second);
	//}
	if(par["-h"]!="" || par["--help"]!="")
	{
		printf("%s\n",help);
		exit(0);
	}
	if(par["-hint"]!="")
	{
		for(int i=0;i<argc;i++)
		{
			//fprintf(stderr,"ARGV %d => %s\n",i,argv[i]);
		}
		const char * world = (par["-hint"]!="NULL")?par["-hint"].c_str():"";
		for(int i=0;serversList[i][0];i++)
		{
			for(int j=0;;j++)
			{
				if(!world[j])
				{
					if(serversList[i][j]=='_')
						goto skip;

					break;
				}
				if(world[j] != serversList[i][j])
					goto skip;
			}
			printf("%s\n",serversList[i]);
			//fprintf(stderr,"HINT: %s\n",serversList[i]);
			skip:;
		}
		for(int i=0;posiblePar[i][0];i++)
		{
			for(int j=0;;j++)
			{
				if(!world[j])
				{
					if(posiblePar[i][j]=='-')
						goto skip2;

					break;
				}
				if(world[j] != posiblePar[i][j])
					goto skip2;
			}
			printf("%s\n",posiblePar[i]);
			//fprintf(stderr,"HINT: %s\n",serversList[i]);
			skip2:;
		}
		return 0;
	}
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
		sprintf(exe,"");
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
	else if(par["-htop"]!="")
	{
		char * exeP = exe;
		int first=-1;
		for(int i=0;serversList[i][0];i++)
		{
			if(serversList[i][0]=='_') continue;
			if(first==-1) first = i;
			else
				exeP += sprintf(exeP,"terminal -e bash -i -c \"kam %s -t=htop\" & ",serversList[i]);
		}
		exeP += sprintf(exeP,"bash -i -c \"kam %s -t=htop\" ",serversList[first]);
	}
	else
	{
		sprintf(exe,"ssh %s@%s -p %d %s%s%s",user,server,port,par["-X"]!=""?" -X":"",par["-t"]!=""?" -t ":"",par["-t"].c_str());
	}
	system("bash -i -c promt");
	puts(exe);
	system(exe);
	return 0;
}

