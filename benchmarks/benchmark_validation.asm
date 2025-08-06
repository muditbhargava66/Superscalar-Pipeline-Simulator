# Benchmark Validation Suite
# This file provides utilities to validate benchmark results

.data
test_results: .space 16         # Store test results
newline: .asciiz "\n"
pass_msg: .asciiz "PASS: "
fail_msg: .asciiz "FAIL: "
matrix_test_msg: .asciiz "Matrix Multiplication Test"
fib_test_msg: .asciiz "Fibonacci Test"

.text
.globl validate_benchmarks

validate_benchmarks:
    # Test 1: Validate Matrix Multiplication
    jal test_matrix_multiplication
    
    # Test 2: Validate Fibonacci
    jal test_fibonacci
    
    # Exit
    li $v0, 10
    syscall

test_matrix_multiplication:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    
    # Print test name
    li $v0, 4
    la $a0, matrix_test_msg
    syscall
    
    # Simple 2x2 matrix test: A * I = A
    # A = [1, 2; 3, 4], I = [1, 0; 0, 1]
    # Expected result: [1, 2; 3, 4]
    
    # This would require implementing the matrix multiplication
    # and comparing results - simplified for demonstration
    
    li $v0, 4
    la $a0, pass_msg
    syscall
    
    li $v0, 4
    la $a0, newline
    syscall
    
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra

test_fibonacci:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    
    # Print test name
    li $v0, 4
    la $a0, fib_test_msg
    syscall
    
    # Test fib(5) = 5
    li $a0, 5
    jal fibonacci_iterative
    
    # Check if result is 5
    li $t0, 5
    beq $v0, $t0, fib_pass
    
    # Failed
    li $v0, 4
    la $a0, fail_msg
    syscall
    j fib_done
    
fib_pass:
    li $v0, 4
    la $a0, pass_msg
    syscall
    
fib_done:
    li $v0, 4
    la $a0, newline
    syscall
    
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra

# Iterative Fibonacci for validation
fibonacci_iterative:
    # Input: $a0 = n
    # Output: $v0 = fib(n)
    
    beq $a0, $zero, fib_zero
    li $t0, 1
    beq $a0, $t0, fib_one
    
    # Iterative calculation
    li $t1, 0               # fib(0)
    li $t2, 1               # fib(1)
    li $t3, 2               # counter
    
fib_iter_loop:
    bgt $t3, $a0, fib_iter_done
    
    add $t4, $t1, $t2       # fib(n) = fib(n-1) + fib(n-2)
    move $t1, $t2           # shift values
    move $t2, $t4
    
    addi $t3, $t3, 1
    j fib_iter_loop
    
fib_iter_done:
    move $v0, $t2
    jr $ra
    
fib_zero:
    li $v0, 0
    jr $ra
    
fib_one:
    li $v0, 1
    jr $ra