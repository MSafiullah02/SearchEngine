import os
os.makedirs("../inverted_index", exist_ok=True)
outs = [open(f"../inverted_index/inverted_index{i}.txt", "w", encoding="utf-8") for i in range(100)]
with open("inverted_index.txt", "r", encoding="utf-8") as f:
    total = sum(1 for _ in f)
with open("inverted_index.txt", "r", encoding="utf-8") as infile:
    last_percent = -1
    for i, line in enumerate(infile, start=1):
        percent = (i * 100) // total
        if percent != last_percent:
            print(f"{percent}% done", end='\r')
            last_percent = percent
        number = int(line.strip().split('\t')[0])
        outs[number%100].write(line)
for f in outs:
    f.close()
print("\nDone!")