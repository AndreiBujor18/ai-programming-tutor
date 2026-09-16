#include <stdio.h>

int main(void) {
    int item_count;
    scanf("%d", &item_count);

    int values[1000];
    for (int position = 0; position < item_count; position++) {
        scanf("%d", &values[position]);
    }

    int minimum = values[0];
    int maximum = values[0];
    for (int position = 1; position < item_count; position++) {
        if (values[position] < minimum) {
            minimum = values[position];
        }
        if (values[position] > maximum) {
            maximum = values[position];
        }
    }

    printf("%d %d\n", minimum, maximum);
    return 0;
}
