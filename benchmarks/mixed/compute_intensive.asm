# Compute-Intensive Mixed Benchmark
# Mixes ALU, memory, and branch operations for realistic IPC measurement
# ~300 instructions simulating a scientific computation kernel

.text
.globl main

main:
    li $sp, 0x7FFC

    # ===== Initialization =====
    li $s0, 0           # Grand accumulator
    li $s1, 0           # Loop variable
    li $s2, 30          # Outer loop iterations
    li $s3, 0x7FFC      # Array base

    # ===== Phase 1: Dot product simulation =====
    # Compute sum(a[i] * b[i]) for 16-element vectors
    li $t0, 0           # Index
    li $t1, 16          # Vector size
    li $t2, 0           # Dot product accumulator

    # Initialize vectors a and b
vec_init:
    beq $t0, $t1, vec_init_done
    sll $t3, $t0, 2
    sub $t4, $s3, $t3
    # a[i] = i + 1
    addi $t5, $t0, 1
    sw $t5, 0($t4)
    addi $t0, $t0, 1
    j vec_init

vec_init_done:
    # Compute dot product
    li $t0, 0
dot_product:
    beq $t0, $t1, dot_done
    sll $t3, $t0, 2
    sub $t4, $s3, $t3
    lw $t5, 0($t4)      # a[i]
    # b[i] = 16 - i (compute on the fly)
    sub $t6, $t1, $t0
    # a[i] * b[i] using repeated addition (no mult result available)
    li $t7, 0           # Product accumulator
    li $t8, 0           # Multiplication counter
mult_loop:
    beq $t8, $t6, mult_done
    add $t7, $t7, $t5
    addi $t8, $t8, 1
    j mult_loop

mult_done:
    add $t2, $t2, $t7
    addi $t0, $t0, 1
    j dot_product

dot_done:
    add $s0, $s0, $t2

    # ===== Phase 2: Matrix-vector multiply (4x4 matrix, 4-vector) =====
    li $s4, 0           # Row index
    li $s5, 4           # Matrix dimension
    li $s6, 0           # Result accumulator

    # Initialize 4x4 matrix and 4-vector in memory region starting at sp-256
    li $t0, 0           # Element index (0..15 for matrix, 16..19 for vector)
    li $t1, 16          # Matrix elements
mat_init:
    beq $t0, $t1, mat_init_done
    li $t2, 256
    sub $t3, $sp, $t2
    sll $t4, $t0, 2
    sub $t5, $t3, $t4
    # Matrix[i][j] = i + j (simplified)
    addi $t6, $t0, 1
    sw $t6, 0($t5)
    addi $t0, $t0, 1
    j mat_init

mat_init_done:
    # Initialize vector (elements 16-19)
    li $t0, 16
vec2_init:
    li $t1, 20
    beq $t0, $t1, vec2_init_done
    li $t2, 256
    sub $t3, $sp, $t2
    sll $t4, $t0, 2
    sub $t5, $t3, $t4
    addi $t6, $t0, -15  # vector[i] = i - 15
    sw $t6, 0($t5)
    addi $t0, $t0, 1
    j vec2_init

vec2_init_done:
    # Compute matrix-vector product (4 rows x 4 cols)
    li $s4, 0           # Row
mat_vec_outer:
    beq $s4, $s5, mat_vec_done
    li $s7, 0           # Col
    li $t9, 0           # Row sum

mat_vec_inner:
    beq $s7, $s5, mat_vec_inner_done

    # Matrix element at [row * 4 + col]
    sll $t0, $s4, 2     # row * 4 (manual calc)
    add $t0, $t0, $s7   # row * 4 + col
    li $t1, 256
    sub $t2, $sp, $t1
    sll $t3, $t0, 2
    sub $t4, $t2, $t3
    lw $t5, 0($t4)      # matrix[row][col]

    # Vector element at [16 + col]
    addi $t0, $s7, 16
    sll $t3, $t0, 2
    sub $t4, $t2, $t3
    lw $t6, 0($t4)      # vector[col]

    # Accumulate (simplified multiply)
    add $t9, $t9, $t5
    add $t9, $t9, $t6

    addi $s7, $s7, 1
    j mat_vec_inner

mat_vec_inner_done:
    add $s6, $s6, $t9
    addi $s4, $s4, 1
    j mat_vec_outer

mat_vec_done:
    add $s0, $s0, $s6

    # ===== Phase 3: Reduction (sum of array) =====
    li $t0, 0
    li $t1, 32          # 32 elements to sum
    li $t2, 0           # Sum
    li $t3, 0x7FFC      # Base

reduction:
    beq $t0, $t1, reduction_done
    sll $t4, $t0, 2
    sub $t5, $t3, $t4
    lw $t6, 0($t5)
    add $t2, $t2, $t6
    addi $t0, $t0, 1
    j reduction

reduction_done:
    add $s0, $s0, $t2

    # ===== Phase 4: Branch-heavy computation =====
    li $t0, 0
    li $t1, 40          # Iterations
    li $t2, 0           # Counter A
    li $t3, 0           # Counter B
    li $t4, 0           # Counter C

branch_heavy:
    beq $t0, $t1, branch_heavy_done

    # Multiple conditional branches
    andi $t5, $t0, 3    # t0 % 4
    beq $t5, $zero, case_0
    addi $t5, $t5, -1
    beq $t5, $zero, case_1
    addi $t5, $t5, -1
    beq $t5, $zero, case_2

    # case 3 (default)
    addi $t4, $t4, 3
    j branch_next

case_0:
    addi $t2, $t2, 1
    j branch_next

case_1:
    addi $t3, $t3, 2
    j branch_next

case_2:
    add $t2, $t2, $t3
    addi $t4, $t4, 1

branch_next:
    addi $t0, $t0, 1
    j branch_heavy

branch_heavy_done:
    add $s0, $s0, $t2
    add $s0, $s0, $t3
    add $s0, $s0, $t4

    # ===== Phase 5: Shift and logical operations =====
    li $t0, 0
    li $t1, 20
    li $t2, 0x12345678  # Test pattern
    li $t3, 0           # XOR accumulator

shift_loop:
    beq $t0, $t1, shift_done
    sll $t4, $t2, 1     # Shift left
    srl $t5, $t2, 1     # Shift right
    xor $t6, $t4, $t5
    and $t7, $t6, $t2
    or $t8, $t6, $t2
    xor $t3, $t3, $t6
    addi $t0, $t0, 1
    j shift_loop

shift_done:
    add $s0, $s0, $t3

    # ===== Store final result and exit =====
    li $sp, 0x7FFC
    sw $s0, 0($sp)

    li $v0, 10
    syscall
