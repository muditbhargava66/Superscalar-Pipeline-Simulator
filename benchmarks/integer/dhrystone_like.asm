# Dhrystone-like Benchmark
# Integer-intensive workload with loops, arrays, string-like ops
# ~200 instructions for steady-state IPC measurement

.text
.globl main

main:
    # Initialize base pointers
    li $sp, 0x7FFC
    li $s0, 0           # Loop counter i
    li $s1, 50          # Outer loop limit
    li $s2, 0           # Accumulator
    li $s3, 100         # Array base offset

    # Initialize array region with known values
    li $t0, 0           # Array index
init_loop:
    beq $t0, $s3, init_done
    sw $t0, 0($sp)       # Store index as value
    addi $sp, $sp, -4
    addi $t0, $t0, 1
    j init_loop

init_done:
    # Reset stack pointer
    li $sp, 0x7FFC

    # ===== Outer computation loop =====
outer_loop:
    beq $s0, $s1, outer_done

    # Inner arithmetic chain (ALU-heavy)
    li $t0, 0           # Inner counter
    li $t1, 0           # Inner accumulator
    li $t2, 10          # Inner loop limit

inner_alu:
    beq $t0, $t2, inner_alu_done
    add $t1, $t1, $t0
    sub $t3, $t2, $t0
    and $t4, $t1, $t3
    or $t5, $t1, $t3
    xor $t6, $t4, $t5
    addi $t0, $t0, 1
    j inner_alu

inner_alu_done:
    # Store inner result
    add $s2, $s2, $t1
    sw $t1, 0($sp)
    addi $sp, $sp, -4

    # Memory access pattern (load/store mix)
    lw $t3, 4($sp)
    lw $t4, 8($sp)
    add $t5, $t3, $t4
    sw $t5, 12($sp)

    # Conditional chain
    slti $t6, $s0, 25
    bne $t6, $zero, first_half
    # Second half: different computation
    sub $s2, $s2, $s0
    j outer_next

first_half:
    add $s2, $s2, $s0

outer_next:
    addi $s0, $s0, 1
    j outer_loop

outer_done:
    # ===== String-like operations =====
    li $t0, 0           # String index
    li $t1, 20          # String length
    li $sp, 0x7FF0      # Reset SP for string area

string_loop:
    beq $t0, $t1, string_done
    # Simulate character comparison
    addi $t2, $t0, 65   # 'A' + index
    sw $t2, 0($sp)
    addi $sp, $sp, -4
    lw $t3, 0($sp)
    beq $t2, $t3, char_match
    addi $s2, $s2, 1
    j string_next

char_match:
    addi $s2, $s2, 2

string_next:
    addi $t0, $t0, 1
    j string_loop

string_done:
    # ===== Multi-level loop (nested) =====
    li $s4, 0           # Outer j
    li $s5, 10          # j limit
    li $s6, 0           # Grand total

nested_outer:
    beq $s4, $s5, nested_done
    li $s7, 0           # Inner k
    li $t9, 10          # k limit

nested_inner:
    beq $s7, $t9, nested_inner_done
    # Compute j*k + j using shifts and adds
    sll $t8, $s7, 2     # k * 4 (approximate multiply)
    add $t8, $t8, $s4   # + j
    add $s6, $s6, $t8
    addi $s7, $s7, 1
    j nested_inner

nested_inner_done:
    addi $s4, $s4, 1
    j nested_outer

nested_done:
    # Final accumulation
    add $s2, $s2, $s6

    # Store final result
    li $sp, 0x7FFC
    sw $s2, 0($sp)

    # Exit
    li $v0, 10
    syscall
