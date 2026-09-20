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

    int item_count;
    if (fscanf(input_file, "%d", &item_count) != 1 || item_count < 1 || item_count > 1000) {
        fclose(input_file);
        fclose(output_file);
        return 1;
    }

    char current_word[101];
    if (fscanf(input_file, "%100s", current_word) != 1) {
        fclose(input_file);
        fclose(output_file);
        return 1;
    }

    char longest_word[101];
    strcpy(longest_word, current_word);
    int longest_length = (int) strlen(longest_word);
    for (int position = 1; position < item_count; position++) {
        if (fscanf(input_file, "%100s", current_word) != 1) {
            fclose(input_file);
            fclose(output_file);
            return 1;
        }
        int current_length = (int) strlen(current_word);
        if (current_length > longest_length) {
            strcpy(longest_word, current_word);
            longest_length = current_length;
        }
    }

    fprintf(output_file, "%s %d\n", longest_word, longest_length);
    fclose(input_file);
    fclose(output_file);
    return 0;
}
