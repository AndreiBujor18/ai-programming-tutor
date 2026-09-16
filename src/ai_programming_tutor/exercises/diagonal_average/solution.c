#include <stdio.h>

int main(void) {
    int item_count;
    scanf("%d", &item_count);

    int matrix[50][50];
    for (int row = 0; row < item_count; row++) {
        for (int column = 0; column < item_count; column++) {
            scanf("%d", &matrix[row][column]);
        }
    }

    long long total = 0;
    for (int position = 0; position < item_count; position++) {
        total += matrix[position][position];
    }

    printf("%.2f\n", (double) total / item_count);
    return 0;
}
