/*
 * *** 加密算法很弱，不能保证加密的安全性。 ***
 * MyZIP.cpp 一个压缩/解压缩 加密/解密程序
 * 压缩算法 霍夫曼编码
 * 加密算法 XOR HASH(Password)
 * 版权申明 BSD
 * 2012-12-20 于 清华园
 * 
 * 编译 g++ MyZIP.cpp -O2 -o MyZIP
 * 压缩文件 MyZIP p input.txt zip.dat [password]
 * 解压文件 MyZIP x zip.dat output.txt [password]
 *
 * 密码是可选的。
 * 如果密码错误，程序有较小可能崩溃
 *
 * 我就在文件头里卖个萌吧 ^_^
 *
 */

#include <iostream>
#include <cstdlib>
#include <cstdio>
#include <cstring>

using namespace std;

const int LBYTE=1;
const int RBYTE=0;
const int HASHSRAND=12211;
const int HASHMOD=1383983;
const int BYTE=8; //bit
const int NBYTE=1<<(BYTE);

const int header_len=2;
const char header[header_len+1]="FK";
const char TEMP_FILE[]="temp.dat";

char * pswd=NULL;

short table[NBYTE][NBYTE*2+1];    //编码表
int cnt[NBYTE*2],tot;
short fa[NBYTE*2],L[NBYTE*2],R[NBYTE*2]; //霍夫曼编码树

void BuildTable(short root,short len,short tmp[])
{
    if (root==-1)    return ;
    if (root<=NBYTE)
    {   //这是一个实际的节点，必然是一个叶子节点
        table[root][0]=len;
        memcpy(table[root]+1,tmp,len*sizeof(tmp[0]));
        return ;
    }
    tmp[len]=LBYTE;
    BuildTable(L[root],len+1,tmp);
    tmp[len]=RBYTE;
    BuildTable(R[root],len+1,tmp);
}

void WriteTo(short buff[],short &Used,FILE * fout)
{
    int len=Used/BYTE;
    char * data=new char [len+1];
    memset(data,0,len+1);
    for (int i=0;i<Used;++i)
        data[i/BYTE]=(data[i/BYTE]<<1)+buff[i];
    fwrite(data,sizeof(data[0]),len,fout);
    Used%=BYTE;
    memmove(buff,&buff[len*BYTE],Used*sizeof(buff[0]));
}

int ReadBit(char buff[],const int bs,int &used,FILE *fin)
{
    if (used==bs*BYTE)
    {
        int nbyte=fread(buff,sizeof(buff[0]),bs,fin);
        if (nbyte==0)   return -1;
        used=0;
    }
    int ret=(buff[used/BYTE]>>((BYTE-1)-used%BYTE))&1;
    ++used;
    return ret;
}

void Decode(FILE * in,FILE * out)
{
    int fsize; //文件总长
    short tsize; //霍夫曼树节点数
    fread(&fsize,sizeof(fsize),1,in);
    fread(&tsize,sizeof(tsize),1,in);
    fread(&L[NBYTE+1],sizeof(L[0]),tsize,in);
    fread(&R[NBYTE+1],sizeof(R[0]),tsize,in);
    char buff[BUFSIZ],buff2[BUFSIZ];
    int bfused=BUFSIZ*BYTE,bf2used=0;
    short Root=NBYTE+tsize;
    for (int i=1;i<=fsize;++i)
    {
        short Now=Root;
        while (Now>NBYTE)
		{
			int byte=ReadBit(buff,BUFSIZ,bfused,in);
			//printf("%d",byte);
            Now=(byte==LBYTE)?L[Now]:R[Now];
		}
        buff2[bf2used++]=char(Now);
        if (bf2used==BUFSIZ)
        {
            fwrite(buff2,sizeof(buff2[0]),bf2used,out);
            bf2used=0;
        }
    }
    fwrite(buff2,sizeof(buff2[0]),bf2used,out);
}

void Encode(FILE * in,FILE * out)
{
    unsigned char buff[BUFSIZ];

    //统计出现次数
    int nbyte;
    while ( (nbyte=fread(buff,1,BUFSIZ,in)) )
        for (int i=0;i<nbyte;++i)
        {
            tot++;
            cnt[buff[i]]++;
        }

    short used=NBYTE;
    //构建霍夫曼编码树
    //注意单个节点的情况
    while (true)
    {
        short min1=-1,min2=-1;
        for (short i=0;i<=used;++i)
            if (cnt[i]&&fa[i]==0)
            {
                short tmp=i;
                if (min1==-1||cnt[min1]>cnt[tmp])
                    swap(min1,tmp);
                if (tmp!=-1&&(min2==-1||cnt[min2]>cnt[tmp]))
                    swap(min2,tmp);
            }
        if (min1!=-1&&min2!=-1)
        {
            ++used;
            cnt[used]=cnt[min1]+cnt[min2];
            L[used]=min1;
            R[used]=min2;
            fa[min1]=fa[min2]=used;
        }
        else
        {
            if (min1<NBYTE)
            {   //单个节点特殊情况
                ++used;
                cnt[used]=cnt[min1];
                L[used]=min1;
                R[used]=-1;
                fa[min1]=used;
            }
            break;
        }
    }

    short tmp[NBYTE*2];
    BuildTable(used,0,tmp);

    //文件总长
    fwrite(&tot,sizeof(tot),1,out);

    //树结构写入
    short tmplen=used-NBYTE;
    fwrite(&tmplen,sizeof(tmplen),1,out);
    fwrite(&L[NBYTE+1],sizeof(L[0]),tmplen,out);
    fwrite(&R[NBYTE+1],sizeof(R[0]),tmplen,out);

    //翻译输入文件
    rewind(in);
    short buff2[BUFSIZ*2],b2used=0;
    while ( (nbyte=fread(buff,1,BUFSIZ,in)) )
    {
        for (int i=0;i<nbyte;++i)
        {
            if (b2used+table[buff[i]][0]>=BUFSIZ*2)
                WriteTo(buff2,b2used,out);
            memcpy(&buff2[b2used],table[buff[i]]+1,table[buff[i]][0]*sizeof(buff2[0]));
            b2used+=table[buff[i]][0];
        }
    }
    //末尾补全
    if (b2used%BYTE!=0)
    {
        short need=BYTE-b2used%BYTE;
        memset(&buff2[b2used],0,need*sizeof(buff2[0]));
        b2used+=need;
    }
    WriteTo(buff2,b2used,out);
}

void XorFile(FILE * in,FILE *out,char Xor[],int Size)
{
	char * buff = new char [Size];
	int nbyte;
    while ( (nbyte=fread(buff,sizeof(buff[0]),Size,in)) )
    {
        for (int i=0;i<nbyte;++i)
            buff[i]^=Xor[i];
        fwrite(buff,sizeof(buff[0]),nbyte,out);
    }
	delete buff;
}

int MKXorTable(char Xor[],char pwd[],int XorSize)
{
	int lenpwd=(pwd==NULL)?0:strlen(pwd);
	if (lenpwd>XorSize)	lenpwd=XorSize;
	memset(Xor,0,XorSize);
	memcpy(Xor,pwd,lenpwd);
	srand(HASHSRAND);
	for (int i=0;i<XorSize;++i)
	{
		int tmp=((Xor[i])+rand())%HASHMOD;
		Xor[i]+=tmp%256;
		srand(tmp);
	}
	return rand();
}

void Encrypt(FILE * in,FILE *out,char pwd[])
{
	char Xor[BUFSIZ];
	int fpass=MKXorTable(Xor,pwd,BUFSIZ);
	fwrite(&fpass,sizeof(fpass),1,out);
    XorFile(in,out,Xor,BUFSIZ);
}

int Decrypt(FILE * in,FILE *out,char pwd[])
{
    char Xor[BUFSIZ];
	int fpass1=MKXorTable(Xor,pwd,BUFSIZ),fpass2;
	fread(&fpass2,sizeof(fpass2),1,in);
	if (fpass1!=fpass2)
	{
		printf("Password incorrect!");
		return 1;
	}
    XorFile(in,out,Xor,BUFSIZ);
	return 0;
}

int main(int argc,char *argv[])
{
    if (argc==1)
    {
        printf("usage:%s [op] fileinput fileoutput [password]\n",argv[0]);
        printf("op:\n");
        printf("p to pack a file with password\n");
        printf("x to unpack a file with password\n");
        return 1;
    }
    char *pswd=NULL;
    if (argc==5)
	{
        pswd=argv[4];
		printf("Password %s\n",pswd);
	}
    FILE * fin=fopen(argv[2],"rb");
    FILE * fout=fopen(argv[3],"wb");
    //FILE * tmpf=tmpfile();
	FILE * tmpf=fopen(TEMP_FILE,"wb+");
    if (fin==NULL)
    {
        printf("unable open %s",argv[2]);
        return 1;
    }
    if (fout==NULL)
    {
        printf("unable open %s",argv[3]);
        return 1;
    }
    if (strcmp(argv[1],"p")==0)
    {     //pack
       Encode(fin,tmpf);
       rewind(tmpf);
       fwrite(header,sizeof(header[0]),strlen(header),fout);
       Encrypt(tmpf,fout,pswd);
    }

    if (strcmp(argv[1],"x")==0)
    {     //unpack
        char _header[header_len+1];
        fread(_header,sizeof(_header[0]),header_len,fin);
        if (memcmp(_header,header,header_len)!=0)
        {
            printf("error format! %s",argv[2]);
            return 1;
        }
        if (Decrypt(fin,tmpf,pswd)==0)
		{
			rewind(tmpf);
			Decode(tmpf,fout);
		}
    }
	fclose(tmpf);
	remove(TEMP_FILE);
	fclose(fout);
	fclose(fin);
    return 0;
}


// for debug
// int main()
// {
    // FILE * fin=fopen("input.txt","rb");
    // FILE * fout=fopen("output.txt","wb");
    // FILE * tmpf=fopen("temp.dat","wb+");
	// char pass[100]="123456";
	// Encrypt(fin,tmpf,pass);
	// rewind(tmpf);
	// Decrypt(tmpf,fout,pass);
	// fclose(tmpf);
	// fclose(fout);
	// fclose(fin);
	// return 0;
// }
