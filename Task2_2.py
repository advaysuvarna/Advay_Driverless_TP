n=int(input("Input n: "))
hash_table=[[] for i in range(10)]
def hashfunc(x,y):
    z=x%10
    y[z].append(x)
for i in range(n):
    el=int(input("Enter the number: "))
    hashfunc(el,hash_table)
print(hash_table)