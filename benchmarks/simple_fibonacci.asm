# Simple Fibonacci Benchmark
# Calculates fibonacci numbers iteratively

.text
.globl main

main:
    # Calculate fibonacci(6) iteratively
    li $t0, 0               # fib(0) = 0
    li $t1, 1               # fib(1) = 1
    li $t2, 6               # n = 6
    li $t3, 2               # counter = 2
    
    # Handle base cases
    beq $t2, $zero, return_t0
    li $t4, 1
    beq $t2, $t4, return_t1
    
    # Iterative calculation
fib_loop:
    beq $t3, $t2, fib_done
    
    # Calculate next fibonacci number
    add $t4, $t0, $t1       # fib(n) = fib(n-1) + fib(n-2)
    
    # Update for next iteration
    add $t0, $t1, $zero     # fib(n-2) = fib(n-1)
    add $t1, $t4, $zero     # fib(n-1) = fib(n)
    
    # Increment counter
    addi $t3, $t3, 1
    j fib_loop
    
fib_done:
    # Result is in $t1
    add $v0, $t1, $zero
    j exit
    
return_t0:
    add $v0, $t0, $zero
    j exit
    
return_t1:
    add $v0, $t1, $zero
    
exit:
    # Exit
    li $v0, 10
    syscall