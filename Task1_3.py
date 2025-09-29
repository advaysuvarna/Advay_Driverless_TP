class task:
    def sort(self, lst):
        n=len(lst)
        for i in range(n):
            min_idx=i
            for j in range(i+1, n):
                if lst[j]<lst[min_idx]:
                    min_idx=j
            lst[i], lst[min_idx]=lst[min_idx], lst[i]
        return lst
    def binary_search(self, lst, value):
        left, right = 0, len(lst) - 1
        while left <= right:
            mid = (left + right) // 2
            if lst[mid] == value:
                return mid
            elif lst[mid] < value:
                left = mid + 1
            else:
                right = mid - 1
        return -1

sortedlist=task()
n = int(input("\nEnter number of elements in the list: "))
s = []
for i in range(n):
    l = input(f"Enter string {i+1}: ")
    s.append(l)
print("Sorted strings:", sortedlist.sort(s))
value = input("Enter the string to search: ")
result = sortedlist.binary_search(s, value)
if result != -1:
    print(f"String '{value}' found at index {result}.")
else:
    print(f"String '{value}' not found in the list.")