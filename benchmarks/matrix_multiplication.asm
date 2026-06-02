# Matrix Multiplication Benchmark
# Performs 4x4 matrix multiplication to test ALU operations,
# memory access patterns, and loop performance

.data
# Matrix A (4x4)
matrix_a:   .word 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16

# Matrix B (4x4)  
matrix_b:   .word 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1

# Result matrix C (4x4)
matrix_c:   .word 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

.text

main:
    # Initialize matrix multiplication
    li $16, 0               # i = 0 (row counter) - $s0 = $16
    
outer_loop:
    li $17, 0               # j = 0 (column counter) - $s1 = $17
    
inner_loop:
    li $18, 0               # k = 0 (dot product counter) - $s2 = $18
    li $t0, 0               # sum = 0
    
dot_product:
    # Calculate address of A[i][k] = base + (i*4 + k)*4
    sll $t1, $16, 2         # i * 4
    add $t1, $t1, $18       # i*4 + k
    sll $t1, $t1, 2         # (i*4 + k) * 4
    li $t2, 268435456       # Base address of matrix_a (0x10000000)
    add $t3, $t2, $t1       # Address of A[i][k]
    lw $t4, 0($t3)          # Load A[i][k]
    
    # Calculate address of B[k][j] = base + (k*4 + j)*4
    sll $t1, $18, 2         # k * 4
    add $t1, $t1, $17       # k*4 + j
    sll $t1, $t1, 2         # (k*4 + j) * 4
    li $t2, 268435520       # Base address of matrix_b (0x10000040)
    add $t3, $t2, $t1       # Address of B[k][j]
    lw $t5, 0($t3)          # Load B[k][j]
    
    # Multiply and accumulate (simplified multiplication)
    add $t6, $t4, $t4       # A[i][k] * 2 (simplified)
    add $t0, $t0, $t6       # sum += product
    
    # Increment k
    addi $18, $18, 1
    li $t7, 4
    sub $t8, $18, $t7       # k - 4
    bltz $t8, dot_product   # if k < 4, continue
    
    # Store result C[i][j] = base + (i*4 + j)*4
    sll $t1, $16, 2         # i * 4
    add $t1, $t1, $17       # i*4 + j
    sll $t1, $t1, 2         # (i*4 + j) * 4
    li $t2, 268435584       # Base address of matrix_c (0x10000080)
    add $t3, $t2, $t1       # Address of C[i][j]
    sw $t0, 0($t3)          # Store result
    
    # Increment j
    addi $17, $17, 1
    li $t7, 4
    sub $t8, $17, $t7       # j - 4
    bltz $t8, inner_loop    # if j < 4, continue
    
    # Increment i
    addi $16, $16, 1
    li $t7, 4
    sub $t8, $16, $t7       # i - 4
    bltz $t8, outer_loop    # if i < 4, continue

    # Exit program
    li $2, 10
    syscall