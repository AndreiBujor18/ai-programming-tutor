#include <stdio.h>

int main(void) {
    int item_count;
    scanf("%d", &item_count);

    int values[1000];
    long long total = 0;
    for (int position = 0; position < item_count; position++) {
        scanf("%d", &values[position]);
        total += values[position];
    }

    /* Print the computed average. */
    printf("%.2f\n", (double) (total / item_count));
    return 0;
}
