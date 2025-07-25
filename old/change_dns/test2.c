#include <fcntl.h>
#include <stdio.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main() {
    // Test open
    int fd = open("/path/to/original/file", O_RDONLY);

    // Test openat
    int dirfd = open("/", O_RDONLY);

    int fd_at = openat(dirfd, "/path/to/original/file", O_RDONLY);

	fopen("/tmp/x", "r");

    close(dirfd);
    return 0;
}
