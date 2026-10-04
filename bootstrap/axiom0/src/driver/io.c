#include "driver/driver.h"

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

void ax_io_set_binary(void) {
#ifdef _WIN32
    /* UCRT text mode would turn "\n" into "\r\n" and make dumps/diagnostics differ from git. */
    (void)_setmode(_fileno(stdout), _O_BINARY);
    (void)_setmode(_fileno(stderr), _O_BINARY);
#endif
}
