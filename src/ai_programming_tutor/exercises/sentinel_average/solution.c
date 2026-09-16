#include <stdio.h>

int main(void) {
    int value;
    long long total = 0;
    int item_count = 0;

    do {
        scanf("%d", &value);
        if (value != 0) {
            total += value;
            item_count++;
        }
    } while (value != 0);

    if (item_count == 0) {
        printf("EMPTY\n");
    } else {
        printf("%.2f\n", (double) total / item_count);
    }
    return 0;
}
