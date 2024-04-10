# Benchmark 1: Matrix Multiplication

# Matrix dimensions
.data
matrix_size: .word 4

# Matrix A
matrix_a: .word 1, 2, 3, 4
          .word 5, 6, 7, 8
          .word 9, 10, 11, 12
          .word 13, 14, 15, 16

# Matrix B
matrix_b: .word 1, 2, 3, 4
          .word 5, 6, 7, 8
          .word 9, 10, 11, 12
          .word 13, 14, 15, 16

# Result matrix
matrix_c: .space 64

.text
.globl main

main:
    # Load matrix dimensions
    lw $t0, matrix_size

    # Initialize pointers to matrices
    la $a0, matrix_a
    la $a1, matrix_b
    la $a2, matrix_c

    # Initialize loop counters
    li $t1, 0  # i
    li $t2, 0  # j
    li $t3, 0  # k

outer_loop:
    beq $t1, $t0, end_outer_loop

inner_loop:
    beq $t2, $t0, end_inner_loop

    # Initialize sum to 0
    li $t4, 0

    # Perform matrix multiplication
    li $t3, 0
multiply_loop:
    beq $t3, $t0, end_multiply_loop

    # Calculate addresses of elements
    mul $t5, $t1, $t0
    add $t5, $t5, $t3
    sll $t5, $t5, 2
    add $t5, $a0, $t5  # Address of matrix_a[i][k]

    mul $t6, $t3, $t0
    add $t6, $t6, $t2
    sll $t6, $t6, 2
    add $t6, $a1, $t6  # Address of matrix_b[k][j]

    # Load elements from matrices
    lw $t7, 0($t5)
    lw $t8, 0($t6)

    # Multiply elements and accumulate sum
    mul $t9, $t7, $t8
    add $t4, $t4, $t9

    # Increment k
    addi $t3, $t3, 1
    j multiply_loop
end_multiply_loop:

    # Store the result in matrix_c
    mul $t5, $t1, $t0
    add $t5, $t5, $t2
    sll $t5, $t5, 2
    add $t5, $a2, $t5  # Address of matrix_c[i][j]
    sw $t4, 0($t5)

    # Increment j
    addi $t2, $t2, 1
    j inner_loop
end_inner_loop:

    # Reset j and increment i
    li $t2, 0
    addi $t1, $t1, 1
    j outer_loop
end_outer_loop:

    # End of benchmark
    li $v0, 10
    syscall