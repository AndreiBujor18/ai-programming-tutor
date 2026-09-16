#include <stdio.h>

int main(void) {
    int item_count;
    scanf("%d", &item_count);

    int values[1000];
    for (int position = 0; position < item_count; position++) {
        scanf("%d", &values[position]);
    }

    int target;
    scanf("%d", &target);
    int frequency = 0;
    for (int position = 0; position < item_count; position++) {
        if (values[position] == target && position >= 0) {
            frequency++;
        }
    }

    printf("%d\n", frequency);
    return 0;
}
