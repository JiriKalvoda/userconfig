/*
 *	From: On-screen Display -- Support Functions for Clients
 *
 *	(c) 2010 Martin Mares <mj@ucw.cz>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <poll.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>

static Display *dpy;
static Atom pty;

static void __attribute__((noreturn)) __attribute__((format(printf,1,2)))
die(char *fmt, ...)
{
	va_list args;
	va_start(args, fmt);
	fputs("i3-workspace: ", stderr);
	vfprintf(stderr, fmt, args);
	fputc('\n', stderr);
	exit(1);
}

static void init(void)
{
	if (dpy)
		return;

	dpy = XOpenDisplay(NULL);
	if (!dpy)
		die("Cannot open display");

	pty = XInternAtom(dpy, "WS_QUEUE", False);
	if (!pty)
		die("Cannot intern WS_QUEUE atom");
}

#define BLEN 12345

int main(int argc, char ** argv)
{
	char buf[BLEN+10];
	char * it = buf;
	for(int i=1;i<argc;i++)
	{
		*it++ = '>';
		for(int j=0; argv[i][j]; j++)
		{
			if(it >= buf+BLEN) die("Too long message");
			if(argv[i][j]!='\n')
				*it++ = argv[i][j];
		}
		*it++ = '\n';
	}
	*it++ = '\n';

	init();
	if (!XChangeProperty(dpy, DefaultRootWindow(dpy), pty, XA_STRING, 8, PropModeAppend, (unsigned char *) buf, strlen(buf)))
		die("XChangeProperty failed");
	XFlush(dpy);
}

