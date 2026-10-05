#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern uint64_t my_data_word;

int check_data(const char* msg) {
    if (my_data_word != 0xdeadbeefc0def00dULL) {
        return 1;
    }
    if (strcmp(msg, "Xin chào thế giới") != 0) {
        return 2;
    }
    return 0;
}
