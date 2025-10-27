n=int(input("Enter the number of strings: "))
y=n
Lstrings=[]
while(n>0): 
    x=input("Enter the strings")
    Lstrings.append(x)
    n-=1

dict={}
for word in Lstrings:
    for letter in word:
        if letter in dict:
            dict[letter]+=1
        else:
            dict[letter]=1

print(Lstrings)
print(dict)





























    
