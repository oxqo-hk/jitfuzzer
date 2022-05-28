#include<stdio.h>
#include<stdlib.h>
#include<sys/syscall.h>
#include<sys/mman.h>
#include<fcntl.h>
#include<unistd.h>

int main(int argc, char* argv[]){
	int fd = open("./hello", O_RDONLY);
	mmap(0x41414141, 0x1000, PROT_READ | PROT_EXEC | PROT_WRITE, MAP_PRIVATE, fd, 0);
	return 0;
}