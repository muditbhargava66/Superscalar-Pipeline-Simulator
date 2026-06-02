# Recursive Fibonacci Benchmark
# Calculates fibonacci numbers using recursion
# Tests function calls, stack management, and return address handling

.data
result:     .word 0

.text

main:
    li $4, 10               # Calculate fibonacci(10) - $a0 = $4
    jal fibonacci           # Call fibonacci function
    li $t0, 268435456       # Base address for result (0x10000000)
    sw $2, 0($t0)           # Store result - $v0 = $2
    
    # Exit program
    li $2, 10
    syscall

# Fibonacci function
# Input: $4 = n ($a0)
# Output: $2 = fibonacci(n) ($v0)
fibonacci:
    # Save registers on stack
    addi $29, $29, -12      # Allocate stack space - $sp = $29
    sw $31, 8($29)          # Save return address - $ra = $31
    sw $16, 4($29)          # Save s0 - $s0 = $16
    sw $17, 0($29)          # Save s1 - $s1 = $17
    
    # Base case: if n <= 1, return n
    li $2, 0                # Default return value - $v0 = $2
    beq $4, $0, fib_exit    # if n == 0, return 0
    
    li $t0, 1
    beq $4, $t0, fib_one    # if n == 1, return 1
    
    # Recursive case: fib(n) = fib(n-1) + fib(n-2)
    add $16, $4, $0         # Save n - move $s0, $a0
    
    # Calculate fib(n-1)
    addi $4, $16, -1        # n - 1
    jal fibonacci           # Recursive call
    add $17, $2, $0         # Save fib(n-1) - move $s1, $v0
    
    # Calculate fib(n-2)
    addi $4, $16, -2        # n - 2
    jal fibonacci           # Recursive call
    
    # Add results
    add $2, $17, $2         # fib(n-1) + fib(n-2)
    j fib_exit

fib_one:
    li $2, 1                # Return 1

fib_exit:
    # Restore registers
    lw $17, 0($29)          # Restore s1
    lw $16, 4($29)          # Restore s0
    lw $31, 8($29)          # Restore return address
    addi $29, $29, 12       # Deallocate stack
    jr $31                  # Return