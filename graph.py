#! /usr/bin/env python3
import json
from scipy.stats import describe
import matplotlib.pyplot as plt
import sys
def undo(array):
    """
    Convert string of numebrs in psudo list format
    to list of ints

    Arguments:
    array - the string to convert

    returns a list of integers
    """
    skip = False
    l = []
    for i, c in enumerate(array):
        if skip:
            skip = False
            continue
        if c != ' ':
            if i + 1 < len(array) - 1 and array[i+1] != ' ':
                l.append(int(c + array[i+1]))
                skip = True
            else:
               l.append(int(c)) 
    return l

def find_training_data(file_name, count=0):
    """
    Using the given file_name, will find specified training data.

    Arguments
    file_name - the file to read data from
    count - the number of the training data to pull

    returns the raw data from the file
    """
    with open(file_name, "r") as f:
        first_line = f.readline().strip()
        count_in_file = int(first_line[first_line.find('=') + 1:])
        count = count_in_file if count == 0 else count

        rest_of_file = f.readlines()
        start = -1
        end = -1
        out = ""
        for index, line in enumerate(rest_of_file):
            line = line.strip() #Remove newline character
            if line == "Training: " + str(count):
                start = index + 1

        for index, line in enumerate(rest_of_file[start:]):
            if line.strip() == "]":
                end = start + index + 1
                break

        if start >= 0 and end >= 0:
            for line in rest_of_file[start:end]:
                out += line
    return json.loads(out)


if len(sys.argv) > 1:
    count_to_find = int(sys.argv[1])
else:
    count_to_find = 0

l = find_training_data("train_file.txt", count_to_find)

final_scores = []
trials = []
replications = l[0]['replications']
for d in l:
    final_scores.append(d['final_scores'])
    trials.append(d['trials'])

formatted_scores = []

for t in final_scores:
    formatted_scores.append(undo(t))

describes = []
for d in formatted_scores:
    describes.append(describe(d))

plt.plot(trials, [d.mean for d in describes])
plt.ylabel("Mean")
plt.xlabel("Number of Trials")
plt.figtext(.1, .9, f"Replications: {replications}")
plt.title("Average Snake length vs trials")
plt.show()
