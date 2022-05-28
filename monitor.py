#/usr/bin/python
#0x367d8d0
OFFSET_PRINTCODE = 0x135f904 #libv8 + 

#set breakpoint
#breakpoint handler
#search memory or get feedback_array
#who should handle feedback? mutator? monitor?
#crash handler

"""
       PTRACE_SYSEMU, PTRACE_SYSEMU_SINGLESTEP (since Linux 2.6.14)
              For PTRACE_SYSEMU, continue and stop on entry to the next sys‐
              tem call, which will not be executed.  See the documentation
              on syscall-stops below.  For PTRACE_SYSEMU_SINGLESTEP, do the
              same but also singlestep if not a system call.  This call is
              used by programs like User Mode Linux that want to emulate all
              the tracee's system calls.  The data argument is treated as
              for PTRACE_CONT.  The addr argument is ignored.  These
              requests are currently supported only on x86.
"""

"""
gef> xinfo 0x00007ffff73f0a1a
--------------------------------------- xinfo: 0x7ffff73f0a1a ---------------------------------------
Page: 0x00007ffff6091000 -> 0x00007ffff7cce000 (size=0x1c3d000)
Permissions: r-x
Pathname: /home/oxqo/research/jsfuzzer/v8/out/x64.debug/libv8.so
Offset (from page): 0x135fa1a
Inode: 2120762
Segment: .text (0x00007ffff6091000-0x00007ffff7b9d62e)
Symbol: v8::internal::compiler::(anonymous
gef> 

"""