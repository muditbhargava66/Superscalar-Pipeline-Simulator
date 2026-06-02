# Memory Access Patterns Benchmark
# Tests various memory access patterns including sequential,
# random, and strided access to evaluate cache performance

.data
# Large array for testing memory patterns (64 words for simplicity)
test_array: .word 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
            .word 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31
            .word 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47
            .word 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63
array_size: .word 64

.text

main:
    # Initialize base addresses
    li $16, 268435456       # Base address of test_array (0x10000000) - $s0 = $16
    li $17, 64              # Array size - $s1 = $17
    
    # Test 1: Sequential access pattern
    li $t0, 0               # Counter
    li $t3, 0               # Sum
    
sequential_loop:
    sub $t8, $t0, $17       # counter - size
    bgez $t8, sequential_done # if counter >= size, done
    sll $t1, $t0, 2         # counter * 4
    add $t2, $16, $t1       # Address
    lw $t4, 0($t2)          # Load value
    add $t3, $t3, $t4       # Accumulate
    addi $t0, $t0, 1        # Increment
    j sequential_loop
    
sequential_done:
    # Test 2: Strided access pattern (stride = 4)
    li $t0, 0               # Counter
    li $t3, 0               # Sum
    li $t5, 4               # Stride
    
strided_loop:
    sub $t8, $t0, $17       # counter - size
    bgez $t8, strided_done  # if counter >= size, done
    sll $t1, $t0, 2         # counter * 4
    add $t2, $16, $t1       # Address
    lw $t4, 0($t2)          # Load value
    add $t3, $t3, $t4       # Accumulate
    add $t0, $t0, $t5       # Add stride
    j strided_loop
    
strided_done:
    # Test 3: Reverse access pattern
    addi $t0, $17, -1       # Start from end (size - 1)
    li $t3, 0               # Sum
    
reverse_loop:
    bltz $t0, reverse_done  # if counter < 0, done
    sll $t1, $t0, 2         # counter * 4
    add $t2, $16, $t1       # Address
    lw $t4, 0($t2)          # Load value
    add $t3, $t3, $t4       # Accumulate
    addi $t0, $t0, -1       # Decrement
    j reverse_loop
    
reverse_done:
    # Exit program
    li $2, 10
    syscall