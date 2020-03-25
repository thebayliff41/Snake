#! /usr/bin/env python3

import json
from scipy.stats import describe
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.optimize import curve_fit
import numpy as np
import sys
import argparse

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

def parseArgs():
    """
    Parses the command line arguments. 

    Returns them as a Namespace object
    """
    parser = argparse.ArgumentParser(description="Graph from train_file.txt.")
    parser.add_argument('count_to_find', metavar='C', type=int, nargs='?', help=
        "Number of data to find in train_file.txt", default=0)
    parser.add_argument('--with-variance', "-wv",  action="store_true")
    parser.add_argument('-describe', '-d', action="store_true")
    return parser.parse_args()

def main():
    args = parseArgs()

    l = find_training_data("train_file.txt", args.count_to_find)

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
        if args.describe:
            print(describe(d))

    model = LinearRegression()
    x = np.asarray(trials).reshape(-1, 1)
    y = np.asarray([d.mean for d in describes]).reshape(-1, 1)

    model.fit(x, y)

    y_new = model.predict(x)
    ax = plt.axes()

    yerr = np.array([[d.variance if d.mean - d.variance >= 0 else d.mean 
    for d in describes], [d.variance for d in describes]])
    plt.errorbar(x, y, yerr=yerr)
    plt.scatter(x, y)
    plt.plot(x, y_new, color='red', label="linear-fit")
    #plt.plot(trials, [d.mean for d in describes])
    if args.with_variance:
        plt.fill_between(trials, [d.mean - d.variance if d.mean - d.variance >=
        0 else 0 for d in describes], [d.mean + d.variance for d in describes], alpha=.2)
    plt.ylabel("Mean")
    plt.xlabel("Number of Trials")
    plt.figtext(.1, .9, f"Replications: {replications}")
    plt.title("Average Snake length vs trials")
    plt.show()

if __name__ == "__main__":
    main()
