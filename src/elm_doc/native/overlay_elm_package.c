#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>

#if defined __APPLE__

#include <sys/syslimits.h>

#elif defined __linux__

#include <linux/limits.h>
#include <stdarg.h>
#include <dlfcn.h>

#endif

const char* replace_path(const char* pathname) {
  // relies on elm-make changing cwd to package directory before reading elm-package.json
  if (strcmp(pathname, "elm-package.json") != 0) {
    return pathname;
  }
  const char* requested_replacement = getenv("USE_ELM_PACKAGE");
  if (!requested_replacement) {
    // not enough config
    return pathname;
  }
  const char* requested_replacee = getenv("INSTEAD_OF_ELM_PACKAGE");
  if (!requested_replacee) {
    // not enough config
    return pathname;
  }
  // resolve to absolute path
  char abspath[PATH_MAX];
  realpath(pathname, abspath);
  if (strcmp(requested_replacee, abspath) != 0) {
    // not the elm-package.json to be replaced
    return pathname;
  }
  // fprintf(stderr, "replaced with %s\n", requested_replacement);
  return requested_replacement;
}

#if defined __APPLE__

int my_open(const char* pathname, int flags, mode_t mode);

typedef struct interposer {
  void* replacement;
  void* original;
} interpose_t;

__attribute__((used)) static const interpose_t interposers[] \
   __attribute__ ((section("__DATA, __interpose"))) = {
    { .replacement = my_open, .original = open },
};

int my_open(const char* pathname, int flags, mode_t mode) {
  //fprintf(stderr, "opening %s %d\n", pathname, flags);
  const char* actual = replace_path(pathname);
  return open(actual, flags, mode);
}

#elif defined __linux__

typedef int (*orig_open_type)(const char* pathname, int oflag, ...);

#ifndef __OPEN_NEEDS_MODE

// taken from glibc's io/fcntl.h
/* Detect if open needs mode as a third argument (or for openat as a fourth
   argument).  */
#ifdef __O_TMPFILE
# define __OPEN_NEEDS_MODE(oflag) \
  (((oflag) & O_CREAT) != 0 || ((oflag) & __O_TMPFILE) == __O_TMPFILE)
#else
# define __OPEN_NEEDS_MODE(oflag) (((oflag) & O_CREAT) != 0)
#endif

#endif

int open(const char* pathname, int oflag, ...) {
  int mode;

  //fprintf(stderr, "opening %s\n", pathname);

  const char* actual = replace_path(pathname);

  orig_open_type orig_open;
  orig_open = (orig_open_type)dlsym(RTLD_NEXT, "open");

  if (__OPEN_NEEDS_MODE (oflag)) {
    va_list arg;
    va_start(arg, oflag);
    mode = va_arg(arg, int);
    va_end(arg);
    return orig_open(actual, oflag, mode);
  } else {
    return orig_open(actual, oflag);
  }
}

#endif
