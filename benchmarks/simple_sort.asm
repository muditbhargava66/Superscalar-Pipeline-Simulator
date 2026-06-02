# Simple Sort Benchmark
# Sorts a small array using simple comparisons

.text
.globl main

main:
    # Initialize array values on stack
    li $t0, 5               # Array[0] = 5
    sw $t0, 0($sp)
    li $t0, 2               # Array[1] = 2
    sw $t0, 4($sp)
    li $t0, 8               # Array[2] = 8
    sw $t0, 8($sp)
    li $t0, 1               # Array[3] = 1
    sw $t0, 12($sp)
    
    # Simple bubble sort (one pass)
    # Compare and swap elements 0 and 1
    lw $t0, 0($sp)          # Load array[0]
    lw $t1, 4($sp)          # Load array[1]
    
    # If array[0] > array[1], swap
    sub $t2, $t0, $t1       # t2 = array[0] - array[1]
    beq $t2, $zero, no_swap1
    
    # Swap elements
    sw $t1, 0($sp)          # array[0] = array[1]
    sw $t0, 4($sp)          # array[1] = array[0]
    
no_swap1:
    # Compare and swap elements 1 and 2
    lw $t0, 4($sp)          # Load array[1]
    lw $t1, 8($sp)          # Load array[2]
    
    sub $t2, $t0, $t1       # t2 = array[1] - array[2]
    beq $t2, $zero, no_swap2
    
    # Swap elements
    sw $t1, 4($sp)          # array[1] = array[2]
    sw $t0, 8($sp)          # array[2] = array[1]
    
no_swap2:
    # Compare and swap elements 2 and 3
    lw $t0, 8($sp)          # Load array[2]
    lw $t1, 12($sp)         # Load array[3]
    
    sub $t2, $t0, $t1       # t2 = array[2] - array[3]
    beq $t2, $zero, no_swap3
    
    # Swap elements
    sw $t1, 8($sp)          # array[2] = array[3]
    sw $t0, 12($sp)         # array[3] = array[2]
    
no_swap3:
    # Exit
    li $v0, 10
    syscall