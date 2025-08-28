#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <pwd.h>
#include <grp.h>

int main(int argc, char *argv[]) {
    int ns_fd;
    uid_t real_uid, real_gid;
    struct passwd *pw;
    
    // Get the real user ID and group ID (the user who invoked the program)
    real_uid = getuid();
    real_gid = getgid();
    
    // Check if we have a command to execute
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        fprintf(stderr, "Execute command in network namespace '" TARGET_NAMESPACE "'.\n");
        exit(EXIT_FAILURE);
    }
    
    // Get user information for proper environment setup
    pw = getpwuid(real_uid);
    if (pw == NULL) {
        fprintf(stderr, "Failed to get user information: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    // Open the network namespace file (requires root privileges)
    ns_fd = open("/var/run/netns/" TARGET_NAMESPACE, O_RDONLY);
    if (ns_fd == -1) {
        fprintf(stderr, "Failed to open network namespace '" TARGET_NAMESPACE "': %s\n", 
                strerror(errno));
        fprintf(stderr, "Make sure the namespace exists (ip netns list)\n");
        exit(EXIT_FAILURE);
    }
    
    // Enter the network namespace (requires root privileges)
    if (setns(ns_fd, CLONE_NEWNET) == -1) {
        fprintf(stderr, "Failed to enter network namespace: %s\n", 
                strerror(errno));
        close(ns_fd);
        exit(EXIT_FAILURE);
    }
    
    // Close the file descriptor as we no longer need it
    close(ns_fd);
    
    // Now drop privileges back to the original user
    // First, initialize supplementary groups
    if (initgroups(pw->pw_name, real_gid) == -1) {
        fprintf(stderr, "Failed to initialize groups: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    // Set the group ID
    if (setgid(real_gid) == -1) {
        fprintf(stderr, "Failed to set group ID: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    // Set the user ID (this must be done last)
    if (setuid(real_uid) == -1) {
        fprintf(stderr, "Failed to set user ID: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    // Verify that we've successfully dropped privileges
    if (getuid() != real_uid || geteuid() != real_uid ||
        getgid() != real_gid || getegid() != real_gid) {
        fprintf(stderr, "Failed to properly drop privileges\n");
        exit(EXIT_FAILURE);
    }
    
    // Set environment variables for the user
    if (setenv("USER", pw->pw_name, 1) == -1 ||
        setenv("LOGNAME", pw->pw_name, 1) == -1 ||
        setenv("HOME", pw->pw_dir, 1) == -1) {
        fprintf(stderr, "Warning: Failed to set some environment variables\n");
    }
    
    // Execute the command with its arguments as the original user
    execvp(argv[1], &argv[1]);
    
    // If we reach here, exec failed
    fprintf(stderr, "Failed to execute '%s': %s\n", argv[1], strerror(errno));
    exit(EXIT_FAILURE);
}
