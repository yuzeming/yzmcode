#第一次作业1
俞则明 2012013318

##asm.h
定义了段描述符。

`SEG_NULLASM` 空段描述符
`SEG_ASM(type,base,lim)` 普通段描述符。

并定义了段属性常量。

##types.h
定义了`uint`,`ushort`,`uchar`,`pde_t`四种类型。
其中`pde_t`实际为`uint`类型。

##x86.h
使用GCC内联汇编将汇编操作包装为函数。所有函数都是静态内联的。
以便实现读取端口等汇编操作。

```c
//读取某个端口
uchar inb(ushort port);
//写入某个端口
void outb(ushort port, uchar data);
//从端口读取cnt*4个字节存入addr内。
void insl(int port, void *addr, int cnt);
//用data的低8位填充addr，长度为cnt
void stosb(void *addr, int data, int cnt);
```

##elf.h
用结构体定义了ELF文件的文件头和程序段头。用于方便读取ELF文件。
值得注意的是以下这些属性。其他属性已经被略去。

```c
// File header
struct elfhdr {
  uint magic;  // must equal ELF_MAGIC 文件头
  /* 省略无关内容 */
  uint entry;   // 程序入口点
  uint phoff;   // 程序段头 偏移
  /* 省略无关内容 */
  ushort phnum; // 程序段头 数量
  /* 省略无关内容 */
};

// Program section header
struct proghdr {
  /* 省略无关内容 */
  uint off; // 文件偏移
  /* 省略无关内容 */
  uint paddr; // 载入的物理地址
  uint filesz; // 文件大小
  uint memsz; // 内存占用大小
  /* 省略无关内容 */
};

```

##bootasm.S
该文件将和bootmain.c被编译为引导扇区，即bootblock文件。

1. 调用`cil`禁用中断。（在载入内核后会重新打开)
2. 清零`ax`,`ds`,`es`,`ss`寄存器。
3. 向特定端口发送数据以开启高位数据总线。这是一个兼容性问题。
4. 使用`lgdt`指令载入GDT，并设置`cr0`的`CR0_PE`位为1。GDT仅仅是将全部内存地址映射到虚拟地址上。
5. 执行一个`ljmp`以重载cs和eip寄存器。系统正式进入保护模式。在保护模式下，cs寄存器都是段选择子。
6. 初始化`de`,`es`,`ss`。在保护模式下，这些寄存器都是段选择子。选择子决定了段的属性。`fs`,`gs`清零。
7. 选择一块空内存作为栈。文中使用了0x7c00作为栈底。栈是向负方向增长的，不会覆盖现有代码。
8. 调用`bootmain`函数
9. 如果`bootmain`函数返回，在发送调试信息后进入死循环。

代码的最后定义了GDT和GDT描述符。可以看到代码段可读可执行不可写，数据段可写。
但是载入内核时直接写入并执行了。GDT作用未知。


##bootmain.C
该文件与bootasm.S被编译为引导扇区，即bootblock文件。

```c
//从磁盘读取接下来的若干个扇区中包含的ELF格式内核，并跳转到内核执行。
void bootmain(void)
{
  struct elfhdr *elf; // 文件头结构体指针
  struct proghdr *ph, *eph; //程序段头结构体 数组开始，结束指针
  void (*entry)(void); //入口点
  uchar* pa;

  elf = (struct elfhdr*)0x10000;  // 指定一个加载位置

  // 载入第一页 载入ELF文件头
  readseg((uchar*)elf, 4096, 0);

  // 检查MAGIC
  if(elf->magic != ELF_MAGIC)
    return;  // 返回bootasm.S

  // 载入每一个程序段
  ph = (struct proghdr*)((uchar*)elf + elf->phoff); //定位程序段头数组的起始位置
  eph = ph + elf->phnum;  //结束位置
  for(; ph < eph; ph++){
    pa = (uchar*)ph->paddr; //读取程序段的载入位置
    readseg(pa, ph->filesz, ph->off); //在载入位置写入数据
    if(ph->memsz > ph->filesz) //如果内存大小和物理大小不相等，用零补齐。
      stosb(pa + ph->filesz, 0, ph->memsz - ph->filesz);
  }

  // 跳转到入口点，不再返回。
  entry = (void(*)(void))(elf->entry);
  entry();
}

void waitdisk(void); //等待磁盘空闲
void readsect(void *dst, uint offset); //读取一个offset扇区
void readseg(uchar* pa, uint count, uint offset)
{
  uchar* epa;

  epa = pa + count; //结束位置
  pa -= offset % SECTSIZE; //起始位置退回一部分以便和扇区对齐
  offset = (offset / SECTSIZE) + 1; //将offset转换为扇区数。请注意第一个扇区为启动扇区，跳过。

  // 逐一读取扇区，注意在起始位置之前和结束位置之后都有可能超出一部分。
  for(; pa < epa; pa += SECTSIZE, offset++)
    readsect(pa, offset);
}

```

##Makefile分析
Makefile 首先会查找系统中的elf-i386编译器和Qume模拟器。

```makefile
xv6.img: bootblock kernel fs.img
  dd if=/dev/zero of=xv6.img count=10000 #生成一个512*10000的全零镜像文件
  dd if=bootblock of=xv6.img conv=notrunc #将引导扇区复制到第一个扇区，不截断文件。
  dd if=kernel of=xv6.img seek=1 conv=notrunc #将内核复制到镜像文件上，并跳过第一个扇区，不截断文件。

bootblock: bootasm.S bootmain.c
  $(CC) $(CFLAGS) -fno-pic -O -nostdinc -I. -c bootmain.c
  $(CC) $(CFLAGS) -fno-pic -nostdinc -I. -c bootasm.S

  #-fno-pic 不生成 地址无关代码
  #-nostdinc 不在系统内查找头文件
  #-c 仅汇编

  $(LD) $(LDFLAGS) -N -e start -Ttext 0x7C00 -o bootblock.o bootasm.o bootmain.o

  #-N 不对齐，不使得text段只读。
  #-e 指定入口点，以便程序的地址与实际载入地址相同。
  #-Ttext 设置text段地址

  $(OBJDUMP) -S bootblock.o > bootblock.asm #这个文件在生成的过程中没有用
  $(OBJCOPY) -S -O binary -j .text bootblock.o bootblock
  # -S 移出所有符号和重定位数据
  # -O 创建指定格式文件
  # -j 指定复制的段。

  ./sign.pl bootblock
  #检查生成的引导扇区大小，并补全为512字节，并加入引导扇区标记。即最后2个字节为AA55
```

##简答题

###1. 仔细阅读 Makefile,分析 xv6.img 是如何一步一步生成的。
详见 Makefile分析

###2. xv6 如何做准备(建立 GDT 表等)并进入保护模式的。
详见 bootasm.S分析

###3. 引导程序如何读取硬盘扇区的?又是如何加载 ELF 格式的 OS 的?
详见 bootmain.C分析。
读取磁盘扇区通过对特定端口读写的方法。

| I/O地址 | 读(主机从硬盘读数据) | 写(主机数据写入硬盘) |
|--|--|--|
| 1F0H | 数据寄存器 | 数据寄存器 |
| 1F1H | 错误寄存器(只读寄存器) | 特征寄存器 |
| 1F2H | 扇区计数寄存器 | 扇区计数寄存器 |
| 1F3H | 扇区号寄存器或LBA块地址0~7 | 扇区号或LBA块地址0~7 |
| 1F4H | 磁道数低8位或LBA块地址8~15 | 磁道数低8位或LBA块地址8~15 |
| 1F5H | 磁道数高8位或LBA块地址16~23 | 磁道数高8位或LBA块地址16~23 |
| 1F6H | 驱动器/磁头或LBA块地址24~27 | 驱动器/磁头或LBA块地址24~27 |
| 1F7H | 状态寄存器 | 命令寄存器 |

##疑惑之处
1. GDT表的段描述 为什么没有起作用。
2. x86.h中void insl函数的内联汇编是如何绑定参数的。
3. kernel 在链接的时候使用了链接脚本是什么意思。
