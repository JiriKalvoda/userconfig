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
#include <sys/capability.h>
#include <sys/prctl.h>

void drop_all_capabilities() {
    cap_t caps;
    
    // Get current capabilities
    caps = cap_get_proc();
    if (caps == NULL) {
        perror("cap_get_proc");
        exit(1);
    }
    
    // Clear all capabilities
    if (cap_clear(caps) == -1) {
        perror("cap_clear");
        cap_free(caps);
        exit(1);
    }
    
    // Apply the cleared capabilities
    if (cap_set_proc(caps) == -1) {
        perror("cap_set_proc");
        cap_free(caps);
        exit(1);
    }
    
    cap_free(caps);
    
    // Also clear the bounding set to prevent re-acquisition
    //if (prctl(PR_CAPBSET_DROP, CAP_SYS_ADMIN, 0, 0, 0) == -1) {
    //    perror("prctl PR_CAPBSET_DROP");
    //    exit(1);
    //}
}

int main(int argc, char *argv[]) {
    int ns_fd;
    uid_t real_uid, real_gid;
    struct passwd *pw;
    cap_t caps;
    
    // Get the real user ID and group ID
    real_uid = getuid();
    real_gid = getgid();
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        fprintf(stderr, "Execute command in network namespace '" TARGET_NAMESPACE "' as original user\n");
        exit(EXIT_FAILURE);
    }
    
    pw = getpwuid(real_uid);
    if (pw == NULL) {
        fprintf(stderr, "Failed to get user information: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    // Open and enter the network namespace
    ns_fd = open("/var/run/netns/" TARGET_NAMESPACE, O_RDONLY);
    if (ns_fd == -1) {
        fprintf(stderr, "Failed to open network namespace: %s\n", 
                strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    if (setns(ns_fd, CLONE_NEWNET) == -1) {
        fprintf(stderr, "Failed to enter network namespace: %s\n", 
                strerror(errno));
        close(ns_fd);
        exit(EXIT_FAILURE);
    }
    close(ns_fd);
    
    // Set up capabilities to preserve CAP_NET_RAW
//    caps = cap_get_proc();
//    if (caps == NULL) {
//        fprintf(stderr, "Failed to get capabilities: %s\n", strerror(errno));
//        exit(EXIT_FAILURE);
//    }
    
	drop_all_capabilities();

    // Clear all capabilities except CAP_NET_RAW
    //cap_clear(caps);
    //cap_value_t cap_list[] = {CAP_NET_RAW};
    //if (cap_set_flag(caps, CAP_INHERITABLE, 1, cap_list, CAP_SET) == -1 ||
    //    cap_set_flag(caps, CAP_PERMITTED, 1, cap_list, CAP_SET) == -1 ||
    //    cap_set_flag(caps, CAP_EFFECTIVE, 1, cap_list, CAP_SET) == -1) {
    //    fprintf(stderr, "Failed to set capabilities: %s\n", strerror(errno));
    //    cap_free(caps);
    //    exit(EXIT_FAILURE);
    //}
    
   // // Enable capability inheritance
   // if (prctl(PR_SET_KEEPCAPS, 1, 0, 0, 0) == -1) {
   //     fprintf(stderr, "Failed to set keepcaps: %s\n", strerror(errno));
   //     cap_free(caps);
   //     exit(EXIT_FAILURE);
   // }
    
    //// Drop privileges
    //if (initgroups(pw->pw_name, real_gid) == -1 ||
    //    setgid(real_gid) == -1 ||
    //    setuid(real_uid) == -1) {
    //    fprintf(stderr, "Failed to drop privileges: %s\n", strerror(errno));
    //    cap_free(caps);
    //    exit(EXIT_FAILURE);
    //}
    
    // Restore the capabilities after dropping privileges
    // if (cap_set_proc(caps) == -1) {
    //     fprintf(stderr, "Failed to restore capabilities: %s\n", strerror(errno));
    //     cap_free(caps);
    //     exit(EXIT_FAILURE);
    // }
    // cap_free(caps);
    
    // Set environment variables
    //setenv("USER", pw->pw_name, 1);
    //setenv("LOGNAME", pw->pw_name, 1);
    //setenv("HOME", pw->pw_dir, 1);
    
    execvp(argv[1], &argv[1]);
    
    fprintf(stderr, "Failed to execute '%s': %s\n", argv[1], strerror(errno));
    exit(EXIT_FAILURE);
}
