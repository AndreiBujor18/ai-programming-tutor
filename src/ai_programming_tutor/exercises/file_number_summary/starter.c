#include <stdio.h>

int main(void) {
    FILE *input_file = fopen("numbers.txt", "r");
    if (input_file == NULL) {
        return 1;
    }

    FILE *output_file = fopen("summary.txt", "w");
    if (output_file == NULL) {
        fclose(input_file);
        return 1;
    }

    /* Read the numbers, then write their minimum, maximum, and sum. */

    fclose(input_file);
    fclose(output_file);
    return 0;
}
