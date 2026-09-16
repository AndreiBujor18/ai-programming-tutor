#include <stdio.h>
#include <string.h>

int main(void) {
    int identifier;
    scanf("%d", &identifier);

    char text[1001];
    fgets(text, sizeof text, stdin);
    text[strcspn(text, "\n")] = '\0';

    printf("%d:%s\n", identifier, text);
    return 0;
}
