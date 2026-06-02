# Basic Operations Benchmark
# Tests fundamental processor operations including arithmetic,
# logical operations, and basic control flow

.data
test_value1: .word 42
test_value2: .word 17
result:      .word 0

.text
.globl main

main:
    # Load test values
    li $t0, 42              # Load 42
    li $t1, 17              # Load 17
    
    # Arithmetic operations
    add $t2, $t0, $t1       # Addition: 42 + 17 = 59
    sub $t3, $t0, $t1       # Subtraction: 42 - 17 = 25
    
    # Logical operations
    and $t5, $t0, $t1       # Bitwise AND
    or $t6, $t0, $t1        # Bitwise OR
    xor $t7, $t0, $t1       # Bitwise XOR
    
    # Memory operations
    sw $t2, 0($sp)          # Store addition result
    lw $s0, 0($sp)          # Load it back
    
    # Conditional operations
    beq $t2, $s0, values_equal
    li $s1, 0               # Not equal
    j continue_test
    
values_equal:
    li $s1, 1               # Equal
    
continue_test:
    # Branch prediction test
    li $s2, 0               # Counter
    li $s3, 10              # Limit
    
loop_test:
    beq $s2, $s3, loop_done # Branch taken when counter == 10
    addi $s2, $s2, 1        # Increment counter
    j loop_test             # Jump back
    
loop_done:
    # Function call test
    jal simple_function
    
    # Exit program
    li $v0, 10
    syscall

# Simple function for testing function calls
simple_function:
    # Save return address
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    
    # Simple computation
    li $t0, 100
    li $t1, 50
    add $v0, $t0, $t1       # Return 150
    
    # Restore and return
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra