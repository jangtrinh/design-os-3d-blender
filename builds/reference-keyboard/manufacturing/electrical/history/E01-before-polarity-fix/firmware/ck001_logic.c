#include "ck001_logic.h"

static const int8_t gray_delta[16] = {
     0,  1, -1,  0,
    -1,  0,  0,  1,
     1,  0,  0, -1,
     0, -1,  1,  0,
};

void ck001_gray_init(ck001_gray_state_t *state, uint8_t initial_ab) {
    state->previous = initial_ab & 0x03u;
    state->accumulator = 0;
}

int8_t ck001_gray_update(ck001_gray_state_t *state, uint8_t current_ab) {
    current_ab &= 0x03u;
    const uint8_t prior = state->previous;
    const uint8_t changed = (uint8_t)(prior ^ current_ab);
    state->previous = current_ab;
    if (changed == 0u) return 0;
    if (changed == 3u) {
        state->accumulator = 0;
        return 0;
    }
    state->accumulator += gray_delta[(prior << 2) | current_ab];
    if (state->accumulator >= 4) {
        state->accumulator = 0;
        return 1;
    }
    if (state->accumulator <= -4) {
        state->accumulator = 0;
        return -1;
    }
    return 0;
}

bool ck001_matrix_cell(uint8_t key_index, uint8_t *row, uint8_t *col) {
    if (key_index >= 58u || row == 0 || col == 0) return false;
    *row = (uint8_t)(key_index / 10u);
    *col = (uint8_t)(key_index % 10u);
    return true;
}
