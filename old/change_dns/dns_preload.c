#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <stdarg.h>

static int (*original_open)(const char *pathname, int flags, ...) = NULL;
static int (*original_openat)(int dirfd, const char *pathname, int flags, ...) = NULL;

static const char * redirect(const char * orig)
{
    if (strcmp(orig, "/etc/resolv.conf") == 0) {
		printf("XXXXXXXXXXXXXXx redirecting\n");
        return "/etc/resolv_direct.conf";
    }
	return orig;
}

int open(const char *pathname, int flags, ...) {
    if (!original_open) {
        original_open = dlsym(RTLD_NEXT, "open");
    }

	pathname = redirect(pathname);

    // Handle variable arguments for mode (optional argument)
    if (flags & O_CREAT) {
        va_list args;
        va_start(args, flags);
        mode_t mode = va_arg(args, mode_t);
        va_end(args);
        return original_open(pathname, flags, mode);
    } else {
        return original_open(pathname, flags);
    }
}

// Overridden openat function
int openat(int dirfd, const char *pathname, int flags, ...) {
	printf("XXXXXXXXXXXXXXx in openat\n");
    // Initialize the original openat function pointer if not already done
    if (!original_openat) {
        original_openat = dlsym(RTLD_NEXT, "openat");
    }

	pathname = redirect(pathname);

    // Handle the variadic arguments for openat
    if (flags & O_CREAT) {
        va_list args;
        va_start(args, flags);
        mode_t mode = va_arg(args, mode_t);
        va_end(args);
        return original_openat(dirfd, pathname, flags, mode);
    } else {
        return original_openat(dirfd, pathname, flags);
    }
}
