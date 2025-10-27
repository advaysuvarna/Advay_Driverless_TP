import csv
x=int(input("Hey there! how many names do you want to input?"))
with open("d://names.csv", "w", newline="") as myfile:
    writer=csv.writer(myfile, delimiter=",")
    for i in range(x):
        rollno=int(input("Enter the roll number: "))
        name=input("Enter the name: ")
        writer.writerow([rollno, name])
        print("Name added.")

print("Sorting The CSV file.......")

list1=[]
with open("d://names.csv", "r", newline="") as myfile:
    reader=csv.reader(myfile, delimiter =",")
    for i in reader:
        list1.append(i)
list1.sort()

with open("d://names.csv", "w", newline="") as myfile:
    writer=csv.writer(myfile, delimiter =",")
    writer.writerows(list1)

print("Sorted Successfully")

with open("d://names.csv", "r", newline="") as myfile:
    reader=csv.reader(myfile, delimiter =",")
    for i in reader:
        print(i)

print("Lets Delete all odd rollnumbers...")

for i in list1:
    if int(i[0])%2!=0:
        list1.remove(i)

with open("d://names.csv", "w", newline="") as myfile:
    writer=csv.writer(myfile, delimiter =",")
    writer.writerows(list1)
print("Deleted Successfully")

with open("d://names.csv", "r", newline="") as myfile:
    reader=csv.reader(myfile, delimiter =",")
    for i in reader:
        print(i)

string=""
for i in list1:
    string+=i[1]
string=string.replace(" ", "")
print("The concatenated string is: ", string)

leastdiff=abs(ord(string[0])-ord(string[1]))
for i in range(len(string)):
    for j in range(i+1, len(string)):
        diff=abs(ord(string[i])-ord(string[j]))
        if diff<leastdiff: 
            leastdiff=diff
print("The least difference between any two characters is: ", leastdiff)
   
        
