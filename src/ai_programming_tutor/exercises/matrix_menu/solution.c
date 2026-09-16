#include <ctype.h>
#include <stdio.h>

void read_matrix(int matrix[20][20], int *row_count, int *column_count) {
    scanf("%d%d", row_count, column_count);
    for (int row = 0; row < *row_count; row++) {
        for (int column = 0; column < *column_count; column++) {
            scanf("%d", &matrix[row][column]);
        }
    }
}

void print_row_maxima(int matrix[20][20], int row_count, int column_count) {
    for (int row = 0; row < row_count; row++) {
        int maximum = matrix[row][0];
        for (int column = 1; column < column_count; column++) {
            if (matrix[row][column] > maximum) {
                maximum = matrix[row][column];
            }
        }
        if (row > 0) {
            printf(" ");
        }
        printf("%d", maximum);
    }
    printf("\n");
}

int main(void) {
    int matrix[20][20] = {{0}};
    int row_count = 0;
    int column_count = 0;
    int has_matrix = 0;
    int command_count;
    scanf("%d", &command_count);

    for (int command_index = 0; command_index < command_count; command_index++) {
        char command;
        scanf(" %c", &command);
        switch (toupper((unsigned char) command)) {
        case 'R':
            read_matrix(matrix, &row_count, &column_count);
            has_matrix = 1;
            break;
        case 'X':
            if (!has_matrix) {
                printf("EMPTY\n");
                break;
            }
            print_row_maxima(matrix, row_count, column_count);
            break;
        default:
            printf("INVALID\n");
        }
    }
    return 0;
}
