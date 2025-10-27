def sortcor(lst):
    x=int(input("Enter the x cordinate of the reference point: "))
    y=int(input("Enter the y cordinate of the reference point: "))
    def dist(a):
        return ((a[0]-x)**2+(a[1]-y)**2)**0.5
    n=len(lst)
    for i in range(n):
        min_idx=i
        for j in range(i+1, n):
            if dist(lst[j])<dist(lst[min_idx]):
                min_idx=j
        lst[i], lst[min_idx]=lst[min_idx], lst[i]
    print("The list is sorted according to the given refrence point: ")
    print(lst)

arr=[]
num= int(input("Enter the number of coordinates to input to the list: "))
for i in range(num):
    temp=[]
    print(f"x{i+1},y{i+1}")
    x=int(input("Enter the x coordinate: "))
    y=int(input("Enter the y coordinate: "))
    temp.append(x)
    temp.append(y)
    tup=tuple(temp)
    arr.append(tup)

sortcor(arr)