# Benchmark 4: Memory Access Patterns (Fixed Version)
# This benchmark tests various memory access patterns to evaluate
# cache performance and memory system behavior

.data
# Arrays for different access patterns (properly sized)
sequential_array:   .space 1024     # 256 words
random_indices:     .word 0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60
                   .word 1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61
stride_array:      .space 2048      # Larger array for stride access
matrix_a:          .space 256       # 8x8 matrix (64 words * 4 bytes)
matrix_b:          .space 256       # 8x8 matrix
matrix_c:          .space 256       # Result matrix

.text
.globl main

main:
    # Test 1: Sequential Access Pattern
    jal test_sequential_access
    
    # Test 2: Random Access Pattern  
    jal test_random_access
    
    # Test 3: Strided Access Pattern (Fixed)
    jal test_strided_access
    
    # Test 4: Matrix Traversal
    jal test_matrix_access
    
    # Exit
    li $v0, 10
    syscall

# Test 1: Sequential memory access (cache-friendly)
test_sequential_access:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    
    la $t0, sequential_array    # Base address
    li $t1, 0                   # Counter
    li $t2, 256                 # Array size in words
    li $t3, 0                   # Sum accumulator
    
seq_loop:
    bge $t1, $t2, seq_done      # Check loop condition
    
    sll $t4, $t1, 2             # t4 = i * 4 (byte offset)
    add $t5, $t0, $t4           # Address = base + offset
    
    # Write then read (test both operations)
    sw $t1, 0($t5)              # Store index value
    lw $t6, 0($t5)              # Load it back
    add $t3, $t3, $t6           # Accumulate sum
    
    addi $t1, $t1, 1            # i++
    j seq_loop

seq_done:
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra

# Test 2: Random memory access (cache-unfriendly)
test_random_access:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    
    la $t0, sequential_array    # Base array
    la $t1, random_indices      # Random index array
    li $t2, 0                   # Counter
    li $t3, 32                  # Number of accesses
    li $t4, 0                   # Sum accumulator
    
rand_loop:
    bge $t2, $t3, rand_done     # Check loop condition
    
    sll $t5, $t2, 2             # t5 = i * 4
    add $t6, $t1, $t5           # Address of random_indices[i]
    lw $t7, 0($t6)              # Load random index
    
    # Bounds check: ensure index < 256
    li $t8, 256
    bge $t7, $t8, skip_access   # Skip if index >= 256
    
    sll $t7, $t7, 2             # Convert to byte offset
    add $t8, $t0, $t7           # Random address in array
    
    # Access random location
    lw $t9, 0($t8)              # Load from random location
    add $t4, $t4, $t9           # Accumulate
    
skip_access:
    addi $t2, $t2, 1            # i++
    j rand_loop

rand_done:
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra

# Test 3: Strided memory access (Fixed)
test_strided_access:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    
    la $t0, stride_array        # Base address
    li $t1, 0                   # Counter
    li $t2, 32                  # Number of accesses (reduced)
    li $t3, 4                   # Stride (1 word = 4 bytes)
    li $t4, 0                   # Sum accumulator
    
stride_loop:
    bge $t1, $t2, stride_done   # Check loop condition
    
    mul $t5, $t1, $t3           # t5 = i * stride (in bytes)
    add $t6, $t0, $t5           # Strided address
    
    # Bounds check: ensure we don't exceed array bounds
    la $t7, stride_array
    addi $t7, $t7, 2048         # End of array
    bge $t6, $t7, skip_stride   # Skip if address >= end
    
    # Access with stride
    sw $t1, 0($t6)              # Store
    lw $t7, 0($t6)              # Load back
    add $t4, $t4, $t7           # Accumulate
    
skip_stride:
    addi $t1, $t1, 1            # i++
    j stride_loop

stride_done:
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra

# Test 4: Matrix access patterns
test_matrix_access:
    addi $sp, $sp, -8
    sw $ra, 4($sp)
    sw $s0, 0($sp)
    
    # Initialize matrices
    jal init_matrices
    
    # Test row-major access (cache-friendly)
    la $a0, matrix_a
    la $a1, matrix_b
    la $a2, matrix_c
    li $a3, 8                   # Matrix dimension
    jal matrix_multiply_row_major
    
    lw $s0, 0($sp)
    lw $ra, 4($sp)
    addi $sp, $sp, 8
    jr $ra

# Initialize matrices with test data
init_matrices:
    la $t0, matrix_a
    la $t1, matrix_b
    li $t2, 0                   # Counter
    li $t3, 64                  # 8x8 = 64 elements
    
init_loop:
    bge $t2, $t3, init_done
    
    sll $t4, $t2, 2             # Byte offset
    add $t5, $t0, $t4
    add $t6, $t1, $t4
    
    # Initialize with simple pattern
    addi $t7, $t2, 1            # t7 = i + 1
    sw $t7, 0($t5)              # matrix_a[i] = i + 1
    sw $t7, 0($t6)              # matrix_b[i] = i + 1
    
    addi $t2, $t2, 1
    j init_loop

init_done:
    jr $ra

# Row-major matrix multiplication (cache-friendly)
matrix_multiply_row_major:
    # a0 = matrix A, a1 = matrix B, a2 = matrix C, a3 = dimension
    move $t0, $a3               # n = dimension
    li $t1, 0                   # i = 0
    
row_i_loop:
    bge $t1, $t0, row_done      # if i >= n, done
    li $t2, 0                   # j = 0
    
row_j_loop:
    bge $t2, $t0, row_j_done    # if j >= n, next i
    
    li $t3, 0                   # sum = 0
    li $t4, 0                   # k = 0
    
row_k_loop:
    bge $t4, $t0, row_k_done    # if k >= n, done with k
    
    # Calculate addresses with bounds checking
    # A[i][k] = A + (i*n + k)*4
    mul $t5, $t1, $t0           # i * n
    add $t5, $t5, $t4           # i * n + k
    sll $t5, $t5, 2             # * 4 for byte offset
    add $t5, $a0, $t5           # Address of A[i][k]
    lw $t6, 0($t5)              # Load A[i][k]
    
    # B[k][j] = B + (k*n + j)*4
    mul $t5, $t4, $t0           # k * n
    add $t5, $t5, $t2           # k * n + j
    sll $t5, $t5, 2             # * 4
    add $t5, $a1, $t5           # Address of B[k][j]
    lw $t7, 0($t5)              # Load B[k][j]
    
    # Multiply and accumulate
    mul $t8, $t6, $t7           # A[i][k] * B[k][j]
    add $t3, $t3, $t8           # sum += product
    
    addi $t4, $t4, 1            # k++
    j row_k_loop

row_k_done:
    # Store result in C[i][j]
    mul $t5, $t1, $t0           # i * n
    add $t5, $t5, $t2           # i * n + j
    sll $t5, $t5, 2             # * 4
    add $t5, $a2, $t5           # Address of C[i][j]
    sw $t3, 0($t5)              # Store sum
    
    addi $t2, $t2, 1            # j++
    j row_j_loop

row_j_done:
    addi $t1, $t1, 1            # i++
    j row_i_loop

row_done:
    jr $ra