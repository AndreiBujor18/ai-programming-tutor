#include <stdio.h>

int main(void) {
    int item_count;
    scanf("%d", &item_count);

    int values[101] = {0};
    for (int position = 0; position < item_count; position++) {
        scanf("%d", &values[position]);
    }

    int inserted_value;
    int insertion_position;
    scanf("%d%d", &inserted_value, &insertion_position);

    for (int index = item_count; index > insertion_position; index--) {
        values[index] = values[index - 1];
    }
    values[insertion_position] = inserted_value;
    item_count++;

    for (int position = 0; position < item_count; position++) {
        if (position > 0) {
            printf(" ");
        }
        printf("%d", values[position]);
    }
    printf("\n");
    return 0;
}
