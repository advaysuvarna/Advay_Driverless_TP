print("Lets multiply two matrixes")
def matmult():
    m=int(input("Enter the number of rows in the first matrix:" ))
    n=int(input("Enter the number of coloumns in the first matrix: "))
    p=int(input("Enter the number of rows in the second matrix:" ))
    q=int(input("Enter the number of coloumns in the second matrix: "))
    if n!=p:
        print("m is not equal to n!!")
        return
    hash1=[[] for i in range(m)]
    hash2=[[] for j in range(p)]
    hash3 = [[0 for j in range(q)] for i in range(m)]
    for a in range(m):
        for b in range(n):
            print(f"Enter the number in position ({a+1},{b+1})")
            num=int(input(""))
            hash1[a].append(num)
    for c in range(p):
        for d in range(q):
            print(f"Enter the number in position ({c+1},{d+1})")
            num=int(input(""))
            hash2[c].append(num)
    for i in range(m):
        for j in range(q):
            hash3[i][j]=0
            for k in range(n):
                hash3[i][j]+=hash1[i][k]*hash2[k][j]
    for i in range(m):
        print(hash3[i])
matmult()