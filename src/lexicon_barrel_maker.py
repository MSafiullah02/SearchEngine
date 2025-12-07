import os
os.makedirs("../lexicon", exist_ok=True) # ensures that the output directories exist
with open("lexicon.txt", "r", encoding="utf-8") as f:
    total = sum(1 for _ in f) # counts number of lines
with open("lexicon.txt", "r") as infile:
    outs = [open(f"../lexicon/lexicon{i + 1}.txt", "w") for i in range(100)] # opens all barrels for lexicon
    last_percent = -1
    i = 1
    for line in infile:
        percent = (i * 100) // total
        i+=1
        if percent != last_percent:
            print(f"{percent}% done", end='\r')  # shows progress in integer percentages so that showing progress doesn't take make the program inefficient
            last_percent = percent
        outs[int(line.strip().split('\t')[1]) % 100].write(line)
    for f in outs: # close all files
        f.close()
print("\nDone!")