#include <stdio.h>
#include <string.h>

int main(void) {
    int identifier;
    scanf("%d", &identifier);

    int character;
    while ((character = getchar()) != '\n' && character != EOF) {
    }

    char text[1001];
    if (fgets(text, sizeof text, stdin) == NULL) {
        return 0;
    }
    text[strcspn(text, "\n")] = '\0';

    printf("%d:%s\n", identifier, text);
    return 0;
}
