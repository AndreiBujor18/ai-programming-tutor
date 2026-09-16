#include <stdio.h>

int main(void) {
    int limit;
    scanf("%d", &limit);

    int printed = 0;
    for (int root = 1; (long long) root * root <= limit; root++) {
        long long square = (long long) root * root;
        if (printed) {
            printf(" ");
        }
        printf("%lld", square);
        printed = 1;
    }
    if (!printed) {
        printf("NONE");
    }
    printf("\n");
    return 0;
}
