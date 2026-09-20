#include <stdio.h>
#include <string.h>

int main(void) {
    FILE *input_file = fopen("words.txt", "r");
    if (input_file == NULL) {
        return 1;
    }

    FILE *output_file = fopen("longest.txt", "w");
    if (output_file == NULL) {
        fclose(input_file);
        return 1;
    }

    /* Read the words, then write the first longest word and its length. */

    fclose(input_file);
    fclose(output_file);
    return 0;
}
