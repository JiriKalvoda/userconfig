#include <linux/input.h>
#include <stdio.h>
#include <errno.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>

#include <unistd.h>

#include <stdbool.h>

#include <xdo.h>

#define fo(a,b) for(int a=0; a < (b); a++)

#define K0 330
#define K1 331
#define K2 332
#define KON 320

#define SCROLLSIZE 40
#define MODECHSIZE 500
#define MINGEST 1000

bool key[400];


int p[3];
int origp[3];
int scrolorigp[3];

int lasts[3];

xdo_t * xdo;

void xdo_m(int k)
{
	xdo_mouse_down(xdo,CURRENTWINDOW,k);
	xdo_mouse_up(xdo,CURRENTWINDOW,k);
}

enum MODE
{
	MNO,
	MBUT,
	MCLICK,
	MSCROLL,
	MGEST,
} mode;

int mouse[2];

int main(int argc, char ** argv)
{
	system("wacom-config init");
	xdo = xdo_new(0);
	char * dev = "/dev/input/by-id/usb-Wacom_Co._Ltd._CTL-672_0ME00M1038175-event-mouse";
	//char * dev = "/dev/input/by-id/usb-Wacom_Co._Ltd._CTL-672_0LE00M1089419-event-mouse";
	if(argc > 1) dev =argv[1];
    struct input_event ev;
    ssize_t n;
    int fd;

    fd = open(dev, O_RDONLY);
    if (fd == -1) {
        fprintf(stderr, "KEYINPUT ERR: Cannot open %s: %s.\n", dev, strerror(errno));
        return 1;
    }
	while (1)
	{
		n = read(fd, &ev, sizeof ev);
		if (n == (ssize_t)-1)
		{
			if (errno == EINTR)
				continue;
			else
				break;
		}
		else if (n != sizeof ev)
		{
			errno = EIO;
			break;
		}
		if (ev.type == EV_KEY)
		{
			if(ev.value >= 0 && ev.value < 2)
			//printf("%s 0x%04x (%d)\n","RELEASED\0PRESSED \0REPATED"+(ev.value*9), (int)ev.code, (int)ev.code);
			//else
			printf("KEY%d 0x%04x (%d)\n",ev.value, (int)ev.code, (int)ev.code);
			key[ev.code] = ev.value;
			if(ev.code == K0 || ev.code == K2)
			{
				if(key[K0] && key[K2]) 
				{
					mode=MCLICK;
					fo(i,2) origp[i]=p[i];
					fo(i,2) lasts[i]=0;
				}
				else 
				if(key[K2] && ev.code == K2 && mode == MNO)
				{
					mode=MBUT;
				}
				else
				{
					if(mode == MBUT)
						xdo_m(2);
					if(mode == MGEST)
					{
						int x = p[0]-origp[0];
						int y = p[1]-origp[1];
						if(x*x+y*y > MINGEST)
						{
							char sys[1234];
							if(x > 0)
							{
								if(y < -3*abs(x))
								{
									printf("RUU\n");
									system("wacom-config outputmapped &");
								}
								else
								if(y > 3*abs(x))
								{
									printf("RDD\n");
									sprintf(sys, "wacom-config map 0 %d %d", mouse[0], mouse[1]);
									system(sys);
								}
								else
								if(2*y < -abs(x))
								{
									printf("RU\n");
									system("wacom-config output 1 &");
								}
								else
								if(2*y > abs(x))
								{
									printf("RD\n");
									system("wacom-config output 0 &");
								}
								else
								{
									printf("R\n");
									system("wacom-config next &");
								}
							}
							else
							{
								if(y < -3*abs(x))
								{
									printf("LUU\n");
									sprintf(sys, "wacom-config map 1 %d %d", mouse[0], mouse[1]);
									system(sys);
								}
								else
								if(y > 3*abs(x))
									printf("LDD\n");
								else
								if(2*y < -abs(x))
								{
									system("xournalppp &" );
									printf("LU\n");
								}
								else
								if(2*y > abs(x))
								{
									system("maim -suo | tee ~/screenshot.png | xclip -selection clipboard -t image/png");
									printf("LD\n");
								}
								else
								{
									printf("L\n");
									system("onboard &");
								}
							}
						}
					}
					mode=MNO;
				}
			}
		}
		//else
			//printf("T %5d C %5d V %5d\n",ev.type, ev.code, ev.value);

			if(ev.type == 3)
			{
				if(ev.code==0) p[0] = ev.value;
				if(ev.code==1) p[1] = ev.value;
				if(ev.code==24) p[2] = ev.value;
				if(ev.code==25) p[2] = -ev.value;

				int s[3];
				fo(i,2) s[i]=(p[i]-scrolorigp[i]+SCROLLSIZE/2 + 1000*SCROLLSIZE)/SCROLLSIZE-1000;
				if(mode == MSCROLL)
				{
					while(s[0]>lasts[0]) {xdo_m(6);printf("RIGHT\n");lasts[0]++;}
					while(s[0]<lasts[0]) {xdo_m(7);printf("LEFT\n");lasts[0]--;}
					while(s[1]>lasts[1]) {xdo_m(4);printf("DOWN\n");lasts[1]++;}
					while(s[1]<lasts[1]) {xdo_m(5);printf("UP\n");lasts[1]--;}
				}
				if(mode == MCLICK || mode == MSCROLL)
				{
				}
				if(mode == MCLICK)
				{
					if(abs(p[0] - origp[0]) > MODECHSIZE)
					{
						mode = MGEST;
						int tmp;
						xdo_get_mouse_location(xdo, mouse, mouse+1, &tmp);
						printf("MGEST %d %d %d\n", mouse[0],mouse[1], tmp);

					}
					else
					if(abs(p[1] - origp[1]) > MODECHSIZE)
					{
						mode = MSCROLL;printf("MSCROLL");
						fo(i,2) scrolorigp[i]=p[i];
					}
				}

			}

		fflush(stdout);
    }
    fflush(stdout);
    fprintf(stderr, "KEYINPUT ERR: %s.\n", strerror(errno));
}

