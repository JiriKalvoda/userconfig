/*
 *	From: On-screen Display -- Support Functions for Clients
 *
 *	(c) 2010 Martin Mares <mj@ucw.cz>
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <poll.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <getopt.h>

#define IS_IN(s, list, opt_name) \
do\
{\
	bool find = false;\
	for(int i=0; i<(int)(sizeof(list)/sizeof(list[0])); i++)\
		if(!strcmp(list[i], (s)))\
			find = true;\
	if(!find)\
	{\
		fprintf(stderr, "Option %s must by only one of following:\n", (opt_name));\
		for(int i=0; i<(int)(sizeof(list)/sizeof(list[0])); i++)\
			fprintf(stderr, "%s%s", i?", ":"", list[i]);\
		fprintf(stderr, "\n");\
		exit(1);\
	}\
} while(0)

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

static void help(FILE *f, char *prog, int exit_code);
static void die_help(char * prog, char *fmt, ...)
{
	va_list args;
	va_start(args, fmt);
	fputs("i3-workspace: ", stderr);
	vfprintf(stderr, fmt, args);
	fputc('\n', stderr);
	help(stderr, prog, 1);
}

#include "data.c"

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

static void help(FILE *f, char * prog, int exit_code)
{
	fprintf(f, "usage:\n");
	fprintf(f, "    %s [-h/--help]     Show this help.\n", prog);
	fprintf(f, "    %s -H/--usage      Show text about how to use whole i3-workspace manager.\n", prog);
	fprintf(f, "    %s -l/--license    Show license of this program.\n", prog);
	fprintf(f, "    %s <CMD> [OPT]     Process subcommand.\n", prog);
	fprintf(f, "    %s -d <CMD> [OPT]  Process subcommand without prevalidation (directly send to daemon).\n", prog);
	fprintf(f, "\n");
	fprintf(f, "subcommands:\n");
	puts(SUBCOMMANDS_HELP);
	fprintf(f, "\n");
	fprintf(f, "See -H option for more information about i3-workspace.\n");
	exit(exit_code);
}

int main(int argc, char ** argv)
{
	int arg_index = 1;
	if(argc == 1 || !strcmp(argv[arg_index], "-h") || !strcmp(argv[1], "--help"))
		help(stdout, argv[0], 0);
	if(!strcmp(argv[1], "-H") || !strcmp(argv[arg_index], "--usage"))
	{
		puts(USAGE);
		exit(0);
	}
	if(!strcmp(argv[1], "-l") || !strcmp(argv[arg_index], "--license"))
	{
		puts(LICENSE);
		exit(0);
	}
	if(!strcmp(argv[arg_index], "-d"))
		arg_index++;
	else
		check(argc, argv);
	char buf[BLEN+10];
	char * it = buf;
	for(;arg_index<argc;arg_index++)
	{
		*it++ = '>';
		for(int j=0; argv[arg_index][j]; j++)
		{
			if(it >= buf+BLEN) die("Too long message");
			if(argv[arg_index][j]=='\n')
				die("Unsupported char '\n' in arguments.");
			else
				*it++ = argv[arg_index][j];
		}
		*it++ = '\n';
	}
	*it++ = '\n';

	init();
	if (!XChangeProperty(dpy, DefaultRootWindow(dpy), pty, XA_STRING, 8, PropModeAppend, (unsigned char *) buf, strlen(buf)))
		die("XChangeProperty failed");
	XFlush(dpy);
}

