#include "ck001_logic.h"
#include <assert.h>
#include <stdio.h>

static int run(ck001_gray_state_t *state, const uint8_t *samples, size_t count) {
    int total = 0;
    for (size_t i = 0; i < count; ++i) total += ck001_gray_update(state, samples[i]);
    return total;
}

int main(void) {
    ck001_gray_state_t state;
    const uint8_t cw[] = {1, 3, 2, 0};
    const uint8_t ccw[] = {2, 3, 1, 0};
    ck001_gray_init(&state, 0); assert(run(&state, cw, 4) == 1);
    ck001_gray_init(&state, 0); assert(run(&state, ccw, 4) == -1);

    const uint8_t bounce[] = {1, 0, 1, 3, 2, 0};
    ck001_gray_init(&state, 0); assert(run(&state, bounce, 6) == 1);
    const uint8_t invalid[] = {3, 0};
    ck001_gray_init(&state, 0); assert(run(&state, invalid, 2) == 0);

    uint8_t row = 99, col = 99;
    assert(ck001_matrix_cell(0, &row, &col) && row == 0 && col == 0);
    assert(ck001_matrix_cell(57, &row, &col) && row == 5 && col == 7);
    assert(!ck001_matrix_cell(58, &row, &col));
    assert(!ck001_matrix_cell(10, 0, &col));
    assert(!ck001_matrix_cell(10, &row, 0));
    puts("CK001_LOGIC_PASS gray_cw=1 gray_ccw=-1 matrix=58");
    return 0;
}
