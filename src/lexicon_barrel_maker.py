import os
os.makedirs("../lexicon", exist_ok=True) # ensures that the output directories exist
with open("lexicon.txt", "r", encoding="utf-8") as f:
    total = sum(1 for _ in f) # counts number of lines
with open("lexicon.txt", "r") as infile:
    outs = [open(f"../lexicon/lexicon{i + 1}.txt", "w", encoding="utf-8") for i in range(27)] # opens all barrels for lexicon
    last_percent = -1
    i = 1
    for line in infile:
        percent = (i * 100) // total
        i+=1
        if percent != last_percent:
            print(f"{percent}% done", end='\r')  # shows progress in integer percentages so that showing progress doesn't take make the program inefficient
            last_percent = percent
        ch = line.strip('\t')[0][0].lower()
        if 'a' <= ch <= 'z': # if the first character is a letter, write it in the corresponding barrel
            outs[ord(ch) - ord('a')].write(line)
        else: # otherwise, write it in the last (extra) barrel
            outs[26].write(line)
    for f in outs: # close all files
        f.close()
print("\nDone!")