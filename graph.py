#! /usr/bin/env python3

import json
from scipy import stats
from scipy.stats import describe, sem, t, linregress
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import normalize
from sklearn.metrics import r2_score
from scipy.optimize import curve_fit
import numpy as np
import math
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
    parser.add_argument('count_to_find', metavar='C', type=int, nargs='?', 
        help= "Number of data to find in train_file.txt", default=0)
    parser.add_argument('--with-variance', "-wv",  action="store_true")
    parser.add_argument('-describe', '-d', action="store_true")
    parser.add_argument('-suppress', '-s', action="store_true")
    parser.add_argument('-linear', '-l', action="store_true")
    parser.add_argument('-confidence-interval', '-ci', action="store_true")
    parser.add_argument('-cutoff', '-co', type=int, default=0)
    parser.add_argument('-complex', '-cp', action="store_true")
    parser.add_argument('-extrapolate', '-e', type=int, metavar='E')
    parser.add_argument('-raw', '-r', action="store_true")
    return parser.parse_args()

def mean_confidence_interval(data, confidence=0.95):
    """
    Returns the confidence interval for the given data.

    Argument list:
    :param data: The data to take the CI from
    :param confidence: the amount of confidence we want to have from the data
    """
    if type(data) != type(np.array([0])):
        raise ValueError(
        f"The given array has type {type(data)} but should be of type {type(np.array([0]))}")

    number_of_elements = len(data)
    average, standard_error = np.mean(data), sem(data)
    interval = standard_error * t.ppf((1 + confidence) / 2., number_of_elements-1)
    return average, average - interval, average + interval

def parseData(data_list, scores, confidence_interval = False, verbose = False):
    """
    Places the confidence interval data into the given list

    Keyword arguments:
    data_list - empty list
    """
    if not isinstance(data_list, list) or data_list: 
        raise ValueError(
        f"The given data has type {type(data_list)} but should be of type list")

    for index, data in enumerate(scores):
        _, low, high = mean_confidence_interval(np.array(data))

        if confidence_interval:
            #Don't modify iterable while iterating
            copy_data = data
            for num in copy_data:
                if num < low or num > high:
                    data.remove(num)

        data_list.append(describe(data))

        if verbose:
            print(index * 10 + 10, describe(data))

def main():
    """Driver"""

    args = parseArgs()
    if args.complex:
        file_name = "complex_train_file.txt"
    else:
        file_name = "train_file.txt"

    data = find_training_data(file_name, args.count_to_find)

    final_scores = []
    trials = []

    replications = data[0]['replications']
    for d in data:
        final_scores.append(d['final_scores'])
        trials.append(d['trials'])

    formatted_scores = []

    for t in final_scores:
        formatted_scores.append(undo(t))

    describes = []
    parseData(describes, formatted_scores, args.confidence_interval, args.describe)

    model = LinearRegression()

    x = np.asarray(trials).reshape(-1, 1)

    y = [d.mean for d in describes]
    y = np.asarray(y).reshape(-1, 1)

    model_y = y

    y_lin = np.exp(y) #Linearize y

    model.fit(x, y_lin)
    y_new = model.predict(x)

    plt.ylabel("Mean")
    plt.xlabel("Number of Trials")
    plt.figtext(.1, .9, f"Replications: {replications}")
    plt.title("Average Snake length vs trials")

    if args.linear:
        plt.scatter(x, y_lin)
        plt.plot(x, y_new, color='red', label="linear-fit")
        plt.show()
        exit()

    plt.scatter(x, y, label = "original-data")

    if args.raw:
        plt.show()
        exit()

    if args.extrapolate:
        if args.extrapolate < max(x)[0]:
            raise ValueError(f"The value passed to the -e option is less than the "
            "maximum value of the original data, {max(x)[0]}.")
        elif args.extrapolate % 10 != 0:
            raise ValueError("Extrapolation value must be a multiple of 10")

        extrapolate_x = np.array([i for i in range(max(x)[0], args.extrapolate + 10, 10)]).reshape(-1, 1)
        extrapolate_y = np.log(model.predict(extrapolate_x))
        plt.plot(extrapolate_x, extrapolate_y, ':', color='green', label="projected-fit")


    indexes = []
    for index, value in enumerate(y_new):
        if value < 0:
            indexes += [index]

    if indexes:
        fixed_x = [x[indexes[0]], x[indexes[-1] + 1]]
        x = x[indexes[-1] + 1:]
        y_new = np.log(y_new[indexes[-1] + 1:]) 
        y = y[indexes[-1] + 1:] 
        fixed_y = [1, y_new[0]]
        plt.plot(fixed_x, fixed_y, ':', color="red",  label="non-transformable")
    else:
        y_new = np.log(y_new) 

    plt.plot(x, y_new, color='red', label="linear-fit")

    plt.legend()
    #print(r2_score(y[indexes[-1] + 1:], y_new))
    print(r2_score(y, y_new))
    #print(f"y = ln({model.coef_}x + {model.intercept_})") #Equation of the line


    if not args.suppress:
        plt.show()

if __name__ == "__main__":
    main()
