# Simple Arithmetic Benchmark
# Tests basic arithmetic operations and control flow

.text
.globl main

main:
    # Initialize values
    li $t0, 10
    li $t1, 5
    li $t2, 3
    
    # Basic arithmetic
    add $t3, $t0, $t1       # 15
    sub $t4, $t0, $t1       # 5
    and $t5, $t0, $t1       # Bitwise AND
    or $t6, $t0, $t1        # Bitwise OR
    
    # Memory operations
    sw $t3, 0($sp)
    lw $t7, 0($sp)
    
    # Conditional branch
    beq $t3, $t7, equal
    li $t8, 0
    j continue
    
equal:
    li $t8, 1
    
continue:
    # Simple loop
    li $s0, 0               # Counter
    li $s1, 5               # Limit
    
loop:
    beq $s0, $s1, done
    addi $s0, $s0, 1
    j loop
    
done:
    # Exit
    li $v0, 10
    syscall