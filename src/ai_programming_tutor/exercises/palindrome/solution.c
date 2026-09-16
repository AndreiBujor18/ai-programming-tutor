#include <stdio.h>
#include <string.h>

int main(void) {
    char word[1001];
    scanf("%1000s", word);

    int length = (int) strlen(word);
    int is_palindrome = 1;
    for (int position = 0; position < length / 2 && is_palindrome; position++) {
        if (word[position] != word[length - position - 1]) {
            is_palindrome = 0;
        }
    }

    printf("%s\n", is_palindrome ? "YES" : "NO");
    return 0;
}
