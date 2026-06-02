# Bubble Sort Benchmark
# Sorts an array of integers using bubble sort algorithm
# Tests branch prediction, memory access patterns, and loop performance

.data
# Array to sort (10 elements)
array:      .word 64, 34, 25, 12, 22, 11, 90, 88, 76, 50
array_size: .word 10

.text

main:
    li $s0, 268435456       # Base address of array (0x10000000)
    li $s1, 10              # Array size
    
    # Outer loop: i from 0 to n-2
    li $t0, 0               # i = 0
    
outer_loop:
    addi $t1, $s1, -1       # n - 1
    sub $t8, $t0, $t1       # t8 = i - (n-1)
    bgez $t8, sort_done     # if i >= n-1, done
    
    # Inner loop: j from 0 to n-i-2
    li $t2, 0               # j = 0
    sub $t3, $t1, $t0       # n - 1 - i
    
inner_loop:
    sub $t9, $t2, $t3       # t9 = j - (n-i-1)
    bgez $t9, inner_done    # if j >= n-i-1, done
    
    # Load array[j] and array[j+1]
    sll $t4, $t2, 2         # j * 4
    add $t5, $s0, $t4       # Address of array[j]
    lw $t6, 0($t5)          # array[j]
    lw $t7, 4($t5)          # array[j+1]
    
    # Compare and swap if necessary
    sub $t8, $t6, $t7       # t8 = array[j] - array[j+1]
    blez $t8, no_swap       # if array[j] <= array[j+1], no swap
    
    # Swap elements
    sw $t7, 0($t5)          # array[j] = array[j+1]
    sw $t6, 4($t5)          # array[j+1] = array[j]
    
no_swap:
    addi $t2, $t2, 1        # j++
    j inner_loop
    
inner_done:
    addi $t0, $t0, 1        # i++
    j outer_loop
    
sort_done:
    # Exit program
    li $2, 10
    syscall