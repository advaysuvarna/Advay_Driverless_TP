class selsort:
    def sort(self, lst):
        n=len(lst)
        for i in range(n):
            min_idx=i
            for j in range(i+1, n):
                if lst[j]<lst[min_idx]:
                    min_idx=j
            lst[i], lst[min_idx]=lst[min_idx], lst[i]
        return lst
sortedlist=selsort()
n = int(input("\nEnter number of strings to sort: "))
s = []
for i in range(n):
    l = input(f"Enter string {i+1}: ")
    s.append(l)
print("Sorted strings:", sortedlist.sort(s))