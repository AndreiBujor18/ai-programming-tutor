#include <stdio.h>

int main(void) {
    unsigned long long number;
    scanf("%llu", &number);

    int frequency = 0;
    do {
        int digit = (int) (number % 10);
        if (digit % 2 != 0) {
            frequency++;
        }
        number /= 10;
    } while (number != 0);

    printf("%d\n", frequency);
    return 0;
}
