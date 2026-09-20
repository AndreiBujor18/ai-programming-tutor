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

    int item_count;
    if (fscanf(input_file, "%d", &item_count) != 1 || item_count < 1) {
        fclose(input_file);
        fclose(output_file);
        return 1;
    }

    long long value;
    if (fscanf(input_file, "%lld", &value) != 1) {
        fclose(input_file);
        fclose(output_file);
        return 1;
    }

    long long minimum = value;
    long long maximum = value;
    long long total = value;
    for (int position = 1; position < item_count; position++) {
        if (fscanf(input_file, "%lld", &value) != 1) {
            fclose(input_file);
            fclose(output_file);
            return 1;
        }
        if (value < minimum) {
            minimum = value;
        }
        if (value > maximum) {
            maximum = value;
        }
        total += value;
    }

    fprintf(output_file, "%lld %lld %lld\n", minimum, maximum, total);
    fclose(input_file);
    fclose(output_file);
    return 0;
}
