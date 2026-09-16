#include <stdio.h>

int main(void) {
    int item_count;
    scanf("%d", &item_count);

    int values[1001] = {0};
    for (int position = 0; position < item_count; position++) {
        scanf("%d", &values[position]);
    }

    int target;
    scanf("%d", &target);
    int removed_count = 0;
    int position = 0;
    while (position < item_count) {
        if (values[position] == target) {
            for (int index = position; index < item_count - 1; index++) {
                values[index] = values[index + 1];
            }
            item_count--;
            removed_count++;
        } else {
            position++;
        }
    }

    printf("%d %d", removed_count, item_count);
    for (int index = 0; index < item_count; index++) {
        printf(" %d", values[index]);
    }
    printf("\n");
    return 0;
}
