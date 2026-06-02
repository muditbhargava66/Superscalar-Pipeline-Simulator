# Validation Suite
# Comprehensive test program for validating simulator functionality
# Tests all major instruction types and pipeline features

.data
test_data:  .word 1, 2, 3, 4, 5
result:     .word 0

.text
.globl main

main:
    # Test arithmetic instructions
    li $t0, 10
    li $t1, 5
    add $t2, $t0, $t1       # 15
    sub $t3, $t0, $t1       # 5
    # Simulate multiplication with shifts and adds
    add $t4, $t0, $t0       # t4 = t0 * 2
    add $t4, $t4, $t1       # t4 = t0 * 2 + t1 (simplified)
    
    # Test logical instructions
    and $t5, $t0, $t1       # Bitwise AND
    or $t6, $t0, $t1        # Bitwise OR
    xor $t7, $t0, $t1       # Bitwise XOR
    
    # Test additional arithmetic (shift not supported with immediates)
    add $t8, $t0, $t0       # Double t0
    add $t8, $t8, $t8       # Quadruple t0 (simulates left shift by 2)
    
    # Test memory instructions (using stack pointer)
    lw $s1, 0($sp)          # Load from stack
    sw $t2, 4($sp)          # Store to stack
    
    # Test branch instructions
    beq $s1, $t0, skip1     # Should not branch
    li $a0, 1               # Executed
    
skip1:
    bne $s1, $t0, skip2     # Should branch
    li $a0, 2               # Not executed
    
skip2:
    # Test jump instructions
    jal test_function
    
    # Exit
    li $v0, 10
    syscall

test_function:
    # Simple function test
    li $v0, 42
    jr $ra