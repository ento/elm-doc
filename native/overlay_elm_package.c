#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#if defined __APPLE__
#include <sys/syslimits.h>
#elif defined __linux__
#include <linux/limits.h>
#endif

int my_open(const char* pathname, int flags, mode_t mode);
FILE* my_fopen(const char* pathname, const char *mode);

typedef struct interposer {
  void* replacement;
  void* original;
} interpose_t;

__attribute__((used)) static const interpose_t interposers[] \
   __attribute__ ((section("__DATA, __interpose"))) = {
    { .replacement = my_open, .original = open },
    { .replacement = my_fopen, .original = fopen },
};

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
  //printf("replaced with %s\n", requested_replacement);
  return requested_replacement;
}

int my_open(const char* pathname, int flags, mode_t mode) {
  //printf("opening %s %d\n", pathname, flags);
  const char* actual = replace_path(pathname);
  return open(actual, flags, mode);
}

FILE* my_fopen(const char* pathname, const char* mode) {
  //printf("fopening %s\n", pathname);
  const char* actual = replace_path(pathname);
  return fopen(actual, mode);
}
