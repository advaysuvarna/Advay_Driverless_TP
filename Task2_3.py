#Task3.3
n=int(input("Input n: "))
hash_table=[[] for i in range(10)]
def hashfunc(x,y):
    z=x%10
    if len(y[z]) == 0:
        y[z].append(x)
        return
    high=len(y[z])-1
    low=0
    while high>=low:
        mid=(high+low)//2
        if x<=y[z][low]:
            y[z].insert(low,x)
            return
        elif x>=y[z][high]:
            y[z].insert(high+1,x)
            return
        elif x==y[z][mid]:
            y[z].insert(mid,x)
            return
        else:
            if x>y[z][mid]:
                low=mid+1
            else:
                high=mid-1
                

for i in range(n):
    el=int(input("Enter the number: "))
    hashfunc(el,hash_table)
print(hash_table)