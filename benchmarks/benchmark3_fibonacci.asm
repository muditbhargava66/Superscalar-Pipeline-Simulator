# Benchmark 3: Recursive Fibonacci
# This benchmark tests the pipeline with recursive function calls,
# return address handling, and deep call stacks

.data
n:          .word 10        # Calculate fibonacci(10)
result:     .word 0

.text
.globl main

main:
    lw $a0, n               # Load n into argument register
    jal fibonacci           # Call fibonacci(n)
    sw $v0, result          # Store result
    
    # Exit program
    li $v0, 10
    syscall

# Fibonacci function
# Input: $a0 = n
# Output: $v0 = fibonacci(n)
fibonacci:
    # Save return address and s-registers
    addi $sp, $sp, -12      # Allocate stack space
    sw $ra, 8($sp)          # Save return address
    sw $s0, 4($sp)          # Save s0
    sw $s1, 0($sp)          # Save s1
    
    # Base cases
    li $v0, 0               # Default return value
    beq $a0, $zero, fib_exit # if n == 0, return 0
    
    li $t0, 1
    beq $a0, $t0, fib_one   # if n == 1, return 1
    
    # Recursive case: fib(n) = fib(n-1) + fib(n-2)
    move $s0, $a0           # Save n in s0
    
    # Calculate fib(n-1)
    addi $a0, $s0, -1       # a0 = n - 1
    jal fibonacci           # Call fibonacci(n-1)
    move $s1, $v0           # Save result in s1
    
    # Calculate fib(n-2)
    addi $a0, $s0, -2       # a0 = n - 2
    jal fibonacci           # Call fibonacci(n-2)
    
    # Add results
    add $v0, $s1, $v0       # v0 = fib(n-1) + fib(n-2)
    j fib_exit

fib_one:
    li $v0, 1               # Return 1

fib_exit:
    # Restore registers and return
    lw $s1, 0($sp)          # Restore s1
    lw $s0, 4($sp)          # Restore s0
    lw $ra, 8($sp)          # Restore return address
    addi $sp, $sp, 12       # Deallocate stack space
    jr $ra                  # Return

# Additional test: Iterative sum for comparison
# This tests loop performance vs recursion
iterative_sum:
    # Input: $a0 = n
    # Output: $v0 = sum(1 to n)
    li $v0, 0               # sum = 0
    li $t0, 1               # i = 1
    
sum_loop:
    bgt $t0, $a0, sum_done  # if i > n, done
    add $v0, $v0, $t0       # sum += i
    addi $t0, $t0, 1        # i++
    j sum_loop

sum_done:
    jr $ra                  # Return
