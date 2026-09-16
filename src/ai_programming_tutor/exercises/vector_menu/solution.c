#include <ctype.h>
#include <stdio.h>

void read_vector(int values[100], int *item_count) {
    scanf("%d", item_count);
    for (int position = 0; position < *item_count; position++) {
        scanf("%d", &values[position]);
    }
}

long long vector_sum(const int values[100], int item_count) {
    long long total = 0;
    for (int position = 0; position < item_count; position++) {
        total += values[position];
    }
    return total;
}

int vector_maximum(const int values[100], int item_count) {
    int maximum = values[0];
    for (int position = 1; position < item_count; position++) {
        if (values[position] > maximum) {
            maximum = values[position];
        }
    }
    return maximum;
}

int main(void) {
    int values[100] = {0};
    int item_count = 0;
    int has_values = 0;
    int command_count;
    scanf("%d", &command_count);

    for (int command_index = 0; command_index < command_count; command_index++) {
        char command;
        scanf(" %c", &command);
        switch (toupper((unsigned char) command)) {
        case 'R':
            read_vector(values, &item_count);
            has_values = 1;
            break;
        case 'S':
            if (!has_values) {
                printf("EMPTY\n");
                break;
            }
            printf("%lld\n", vector_sum(values, item_count));
            break;
        case 'M':
            if (!has_values) {
                printf("EMPTY\n");
                break;
            }
            printf("%d\n", vector_maximum(values, item_count));
            break;
        default:
            printf("INVALID\n");
        }
    }
    return 0;
}
