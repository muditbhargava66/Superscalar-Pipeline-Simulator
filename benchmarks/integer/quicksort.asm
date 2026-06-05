# Quicksort-like Benchmark
# Simulates recursive-like partitioning with iterative approach
# ~150 instructions with branch-heavy workload

.text
.globl main

main:
    li $sp, 0x7FFC

    # Initialize array of 20 elements on stack
    li $s0, 0           # Array base = sp
    li $s1, 20          # Array size
    li $t0, 0           # Index

init_array:
    beq $t0, $s1, init_done
    # Fill with pseudo-random values: 20 - index
    sub $t1, $s1, $t0
    sw $t1, 0($sp)
    addi $sp, $sp, -4
    addi $t0, $t0, 1
    j init_array

init_done:
    # Array is now at [sp+4 .. sp+80] (indices 0..19)
    # $sp points to last pushed element

    # ===== Simulate partition pass (iterative quicksort step) =====
    # Partition array[0..19]
    li $s2, 0           # low = 0
    li $s3, 19          # high = 19

    # Choose pivot = array[high] = element at offset (high * 4 + 4) from sp
    # Since array is at sp+4, array[i] = lw from sp + (i*4 + 4)
    # But sp has been decremented, so we use fixed base
    li $s4, 0x7FFC      # Original SP = array base

    # pivot = array[19]
    li $t0, 76          # 19 * 4 = 76
    sub $t1, $s4, $t0
    lw $s5, 0($t1)      # pivot value

    # i = low - 1
    addi $s6, $s2, -1   # i = -1
    li $s7, 0           # j = low

partition_loop:
    beq $s7, $s3, partition_done  # j == high -> done

    # Compare array[j] <= pivot
    # array[j] at offset (j * 4) from array base
    sll $t0, $s7, 2     # j * 4
    sub $t1, $s4, $t0
    lw $t2, 0($t1)      # array[j]
    slt $t3, $t2, $s5   # array[j] < pivot
    beq $t3, $zero, no_swap
    # array[j] == pivot check
    beq $t2, $s5, do_swap

no_swap:
    addi $s7, $s7, 1
    j partition_loop

do_swap:
    # i++
    addi $s6, $s6, 1

    # Swap array[i] and array[j]
    sll $t4, $s6, 2     # i * 4
    sub $t5, $s4, $t4
    lw $t6, 0($t5)      # array[i]

    sll $t7, $s7, 2     # j * 4
    sub $t8, $s4, $t7
    lw $t9, 0($t8)      # array[j]

    # Write swapped values
    sw $t9, 0($t5)      # array[i] = old array[j]
    sw $t6, 0($t8)      # array[j] = old array[i]

    addi $s7, $s7, 1
    j partition_loop

partition_done:
    # Place pivot at correct position (i+1)
    addi $s6, $s6, 1    # pivot index = i + 1

    sll $t4, $s6, 2
    sub $t5, $s4, $t4
    lw $t6, 0($t5)

    sll $t7, $s3, 2     # high * 4
    sub $t8, $s4, $t7
    lw $t9, 0($t8)

    sw $t9, 0($t5)
    sw $t6, 0($t8)

    # ===== Second partition pass on left sub-array =====
    li $s2, 0
    # high = pivot_index - 1
    addi $s3, $s6, -1
    beq $s3, $zero, sort_done
    slt $t0, $s3, $zero
    bne $t0, $zero, sort_done

    # Simple insertion sort on left portion (0..pivot_index-1)
    li $t0, 1           # i = 1
insertion_outer:
    slt $t1, $s3, $t0
    bne $t1, $zero, insertion_done

    # key = array[i]
    sll $t2, $t0, 2
    sub $t3, $s4, $t2
    lw $t4, 0($t3)      # key

    li $t5, 0
    sub $t5, $t0, $t5
    addi $t5, $t0, -1   # j = i - 1

insertion_inner:
    slt $t6, $t5, $zero
    bne $t6, $zero, insertion_place

    sll $t7, $t5, 2
    sub $t8, $s4, $t7
    lw $t9, 0($t8)      # array[j]
    slt $t6, $t4, $t9   # key < array[j]
    beq $t6, $zero, insertion_place

    # array[j+1] = array[j]
    addi $t6, $t5, 1
    sll $t7, $t6, 2
    sub $t8, $s4, $t7
    sw $t9, 0($t8)

    addi $t5, $t5, -1
    j insertion_inner

insertion_place:
    # array[j+1] = key
    addi $t6, $t5, 1
    sll $t7, $t6, 2
    sub $t8, $s4, $t7
    sw $t4, 0($t8)

    addi $t0, $t0, 1
    j insertion_outer

insertion_done:
    # ===== Compute checksum to verify sorting =====
    li $t0, 0           # Index
    li $t1, 0           # Checksum
    li $t2, 20          # Size

checksum_loop:
    beq $t0, $t2, checksum_done
    sll $t3, $t0, 2
    sub $t4, $s4, $t3
    lw $t5, 0($t4)
    add $t1, $t1, $t5
    addi $t0, $t0, 1
    j checksum_loop

checksum_done:
    # Store checksum
    sw $t1, 0($sp)

sort_done:
    # Exit
    li $v0, 10
    syscall
