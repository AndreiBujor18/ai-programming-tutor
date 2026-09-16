#include <stdio.h>

int main(void) {
    long long lower_bound;
    long long upper_bound;
    scanf("%lld %lld", &lower_bound, &upper_bound);

    long long item_count = upper_bound - lower_bound + 1;
    if (item_count % 2 == 0) {
        printf("EVEN\n");
    } else {
        printf("ODD\n");
    }
    return 0;
}
