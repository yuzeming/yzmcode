#include <cstdlib>
#include <cstdio>
#include <cstring>

const int MAXN=100;
const int MAXM=1000;

const int Fx[]={0,1, 0,-1,1, 1,-1,-1};
const int Fy[]={1,0,-1, 0,1,-1, 1,-1};

char M[MAXN][MAXN+1];
char W[MAXM][MAXN+1];
int Ans[MAXM],LW[MAXM];
int N,Mi;

void Check(char tmp[],bool first)
{
    for (int i=0;i<Mi;++i)
        if (strncmp(tmp,W[i],LW[i])==0&&(LW[i]!=1||first)) //注意长度为1的单词在8个方向会被记录8次，在这里排除这种情况。
            ++Ans[i];  //find word[i] at matrix[x][y] in f direction
}

void Work(int X,int Y)
{
    for (int f=0;f<8;++f)
    {
        int x=X,y=Y,len=0;
        char tmp[MAXN];
        while (0<=x&&x<N&&0<=y&&y<N)
        {
            tmp[len++]=M[x][y];
            x+=Fx[f];y+=Fy[f];
        }
        tmp[len]='\0';
        Check(tmp,f==0);
    }
}

int main()
{
    scanf("%d%d",&N,&Mi);
    for (int i=0;i<N;++i)
        scanf("%s",M[i]);
    for (int i=0;i<Mi;++i)
    {
        scanf("%s",W[i]);
        LW[i]=strlen(W[i]);
    }
    for (int i=0;i<N;++i)
        for (int j=0;j<N;++j)
            Work(i,j);
    for (int i=0;i<Mi;++i)
        printf("%d:%s\n",Ans[i],W[i]);
}
