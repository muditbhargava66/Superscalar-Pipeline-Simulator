# Simple Test Program
# Basic functionality test for the superscalar pipeline simulator
.text
.globl main

main:
    # Simple arithmetic operations
    li $t0, 10
    li $t1, 20
    add $t2, $t0, $t1
    
    # Memory operations
    sw $t2, 0($sp)
    lw $t3, 0($sp)
    
    # Branch operation
    beq $t2, $t3, end
    
    # More arithmetic
    sub $t4, $t2, $t1
    
end:
    # System call to exit
    li $v0, 10
    syscall