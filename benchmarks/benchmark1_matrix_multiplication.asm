# Benchmark 1: Matrix Multiplication

# Matrix dimensions
.data
matrix_size: .word 4

# Matrix A (4x4)
matrix_a: .word 1, 2, 3, 4
          .word 5, 6, 7, 8
          .word 9, 10, 11, 12
          .word 13, 14, 15, 16

# Matrix B (4x4) - Identity matrix for easy verification
matrix_b: .word 1, 0, 0, 0
          .word 0, 1, 0, 0
          .word 0, 0, 1, 0
          .word 0, 0, 0, 1

# Result matrix
matrix_c: .space 64

# Expected result for verification
expected: .word 1, 2, 3, 4
          .word 5, 6, 7, 8
          .word 9, 10, 11, 12
          .word 13, 14, 15, 16

.text
.globl main

main:
    lw $t0, matrix_size
    la $a0, matrix_a
    la $a1, matrix_b
    la $a2, matrix_c
    
    # Initialize loop counters
    li $t1, 0               # i (row index)

outer_loop:
    beq $t1, $t0, verify_result
    li $t2, 0               # j (column index)

inner_loop:
    beq $t2, $t0, end_inner_loop
    li $t4, 0               # sum accumulator
    li $t3, 0               # k (inner product index)

multiply_loop:
    beq $t3, $t0, end_multiply_loop
    
    # Calculate address of A[i][k]
    mul $t5, $t1, $t0       # i * matrix_size
    add $t5, $t5, $t3       # i * matrix_size + k
    sll $t5, $t5, 2         # convert to byte offset
    add $t5, $a0, $t5       # base address + offset
    lw $t7, 0($t5)          # load A[i][k]
    
    # Calculate address of B[k][j]
    mul $t6, $t3, $t0       # k * matrix_size
    add $t6, $t6, $t2       # k * matrix_size + j
    sll $t6, $t6, 2         # convert to byte offset
    add $t6, $a1, $t6       # base address + offset
    lw $t8, 0($t6)          # load B[k][j]
    
    # Multiply and accumulate
    mul $t9, $t7, $t8       # A[i][k] * B[k][j]
    add $t4, $t4, $t9       # sum += product
    
    addi $t3, $t3, 1        # k++
    j multiply_loop

end_multiply_loop:
    # Store result in C[i][j]
    mul $t5, $t1, $t0       # i * matrix_size
    add $t5, $t5, $t2       # i * matrix_size + j
    sll $t5, $t5, 2         # convert to byte offset
    add $t5, $a2, $t5       # base address + offset
    sw $t4, 0($t5)          # store sum
    
    addi $t2, $t2, 1        # j++
    j inner_loop

end_inner_loop:
    addi $t1, $t1, 1        # i++
    j outer_loop

verify_result:
    # Simple verification: compare first element
    la $t0, matrix_c
    la $t1, expected
    lw $t2, 0($t0)          # C[0][0]
    lw $t3, 0($t1)          # Expected[0][0]
    
    # If equal, verification passed (simplified check)
    beq $t2, $t3, verification_passed
    
    # Verification failed
    li $v0, 1               # Exit with error code
    syscall

verification_passed:
    li $v0, 10              # Exit successfully
    syscall