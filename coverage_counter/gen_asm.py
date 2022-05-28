data1 ="""mapped_je:
mov [rbp-0x1008], rsp
mov rsp, 0xdeadbeefdeadbeef
push rax
push rbx
push rcx
push rdx
push rdi
push rsi
push r8
push r9
push r10
push r11
push r12
push r13
push r14
push r15
push rbp

mov rax, 0
je here
not_here:
inc rax
here:
inc rax 
mov rbx, 0x1234567812345678
loop:
mov rcx, [rbx] 
mov rdi, [rbp-0x1008]
mov rsi, [rdi]
sub rsi, 6
add rbx, 0x20
cmp rsi, rcx
jne loop
sub rbx, 0x20
mov rdi, [rbx+8]
mov edx, [rdi]
add edx, eax
mov [rdi], edx

pop rbp
cmp rax, 1
je taken

mov rsi, [rbx+0x18]
mov rdi, [rbp-0x1008]
mov [rdi], rsi
jmp epilogue

taken:
mov rsi, [rbx+0x10]
mov rdi, [rbp-0x1008]
mov [rdi], rsi

epilogue:
pop r15
pop r14
pop r13
pop r12
pop r11
pop r10
pop r9
pop r8
pop rsi
pop rdi
pop rdx
pop rcx
pop rbx
pop rax

mov rsp, [rbp-0x1008]
ret

"""
data ="""mapped_je:
mov [rbp-0x1008], rsp
mov rsp, 0xdeadbeefdeadbeef
push rax
push rbx
push rcx
push rdx
push rdi
push rsi
push r8
push r9
push r10
push r11
push r12
push r13
push r14
push r15
push rbp

mov rax, 0
je here
jmp not_here

"""

for i, op in enumerate(['jne', 'js', 'jns', 'jg', 'jge', 'jle', 'ja', 'jae', 'jb', 'jbe', 'jo', 'jp']):
	tmp = data.replace('mapped_je', 'mapped_' + op)
	tmp = tmp.replace('je here', op + ' here')

