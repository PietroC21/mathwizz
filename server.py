myStr = input("Enter a string: ")
input_bytes = myStr.encode('utf-8')  # Convert string to bytes
num_chuncks = len(input_bytes) // 32  # Number of 1024 byte chunks

chunks = []
if num_chuncks != 0:
    for i in range(num_chuncks):
        # Each chunk is 32 bytes
        try:
            chunk = input_bytes[i*32:(i+1)*32]
        except:
            chunk = 0
        chunks.append(chunk)
else:
    chunks.append(0)


myStr = ""

for i in range(1,len(chunks)):
    int_list1 = chr(chunk[i-1]) 
    int_list2 = chr(chunk[i]) 
    new_list = []
    print(int_list1)
    for a,b in zip(int_list1, int_list2):
        print(ord(chr(a)))
        new_list.append(ord(a)^ ord(b))
        print(new_list)



print("Str:")
mystr = bytes(chunks[0]).decode('utf-8')
print(mystr )
print(myStr )