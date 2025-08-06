# Benchmark 2: Bubble Sort Algorithm
# This benchmark tests branch prediction with nested loops and data-dependent branches

.data
array:      .word 64, 34, 25, 12, 22, 11, 90, 88, 76, 50, 43, 8
array_size: .word 12

.text
.globl main

main:
    la $t0, array           # Load array base address
    lw $t1, array_size      # Load array size
    li $t2, 0               # i = 0 (outer loop counter)

outer_loop:
    # Check if i < array_size - 1
    addi $t3, $t1, -1       # t3 = array_size - 1
    bge $t2, $t3, exit      # if i >= array_size - 1, exit
    
    li $t4, 0               # j = 0 (inner loop counter)
    sub $t5, $t3, $t2       # t5 = array_size - 1 - i

inner_loop:
    # Check if j < array_size - 1 - i
    bge $t4, $t5, end_inner # if j >= array_size - 1 - i, end inner loop
    
    # Load array[j] and array[j+1]
    sll $t6, $t4, 2         # t6 = j * 4 (word offset)
    add $t7, $t0, $t6       # t7 = address of array[j]
    lw $s0, 0($t7)          # s0 = array[j]
    lw $s1, 4($t7)          # s1 = array[j+1]
    
    # Compare and swap if needed
    ble $s0, $s1, no_swap   # if array[j] <= array[j+1], don't swap
    
    # Swap array[j] and array[j+1]
    sw $s1, 0($t7)          # array[j] = array[j+1]
    sw $s0, 4($t7)          # array[j+1] = array[j]
    
no_swap:
    addi $t4, $t4, 1        # j++
    j inner_loop

end_inner:
    addi $t2, $t2, 1        # i++
    j outer_loop

exit:
    # Array is now sorted
    li $v0, 10              # Exit syscall
    syscall
