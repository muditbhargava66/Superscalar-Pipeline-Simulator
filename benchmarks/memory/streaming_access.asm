# Streaming Memory Access Benchmark
# Tests sequential, strided, and random-like memory access patterns
# ~120 instructions for cache behavior measurement

.text
.globl main

main:
    li $sp, 0x7FFC
    li $s0, 0           # Accumulator
    li $s1, 64          # Array size (64 words = 256 bytes)

    # ===== Phase 1: Sequential write =====
    li $t0, 0           # Index
    li $t1, 0x7FFC      # Base address

seq_write:
    beq $t0, $s1, seq_write_done
    sll $t2, $t0, 2     # index * 4
    sub $t3, $t1, $t2
    add $t4, $t0, $t0   # value = 2 * index
    sw $t4, 0($t3)
    addi $t0, $t0, 1
    j seq_write

seq_write_done:
    # ===== Phase 2: Sequential read (should hit cache) =====
    li $t0, 0
seq_read:
    beq $t0, $s1, seq_read_done
    sll $t2, $t0, 2
    sub $t3, $t1, $t2
    lw $t4, 0($t3)
    add $s0, $s0, $t4
    addi $t0, $t0, 1
    j seq_read

seq_read_done:
    # ===== Phase 3: Strided access (stride = 4) =====
    li $t0, 0           # Index
    li $t5, 4           # Stride
strided_read:
    slt $t6, $t0, $s1
    beq $t6, $zero, strided_done
    sll $t2, $t0, 2
    sub $t3, $t1, $t2
    lw $t4, 0($t3)
    add $s0, $s0, $t4
    add $t0, $t0, $t5   # Index += stride
    j strided_read

strided_done:
    # ===== Phase 4: Reverse sequential read =====
    addi $t0, $s1, -1   # Start from end
reverse_read:
    slt $t6, $t0, $zero
    bne $t6, $zero, reverse_done
    sll $t2, $t0, 2
    sub $t3, $t1, $t2
    lw $t4, 0($t3)
    add $s0, $s0, $t4
    addi $t0, $t0, -1
    j reverse_read

reverse_done:
    # ===== Phase 5: Write-back pattern (modify and store) =====
    li $t0, 0
modify_loop:
    beq $t0, $s1, modify_done
    sll $t2, $t0, 2
    sub $t3, $t1, $t2
    lw $t4, 0($t3)      # Load
    addi $t4, $t4, 1    # Modify
    sw $t4, 0($t3)      # Store back
    addi $t0, $t0, 1
    j modify_loop

modify_done:
    # ===== Phase 6: Copy pattern (source to destination) =====
    li $t0, 0
    li $t7, 0x7C00      # Destination base (separate region)
copy_loop:
    beq $t0, $s1, copy_done
    sll $t2, $t0, 2
    # Load from source
    sub $t3, $t1, $t2
    lw $t4, 0($t3)
    # Store to destination
    sub $t5, $t7, $t2
    sw $t4, 0($t5)
    addi $t0, $t0, 1
    j copy_loop

copy_done:
    # Final checksum
    li $sp, 0x7FFC
    sw $s0, 0($sp)

    # Exit
    li $v0, 10
    syscall
