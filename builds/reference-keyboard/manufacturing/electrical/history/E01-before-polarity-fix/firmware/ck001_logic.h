#ifndef CK001_LOGIC_H
#define CK001_LOGIC_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint8_t previous;
    int8_t accumulator;
} ck001_gray_state_t;

void ck001_gray_init(ck001_gray_state_t *state, uint8_t initial_ab);
int8_t ck001_gray_update(ck001_gray_state_t *state, uint8_t current_ab);
bool ck001_matrix_cell(uint8_t key_index, uint8_t *row, uint8_t *col);

#endif
