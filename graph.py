#! /usr/bin/env python3

import json
from scipy.stats import describe, sem, t
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
    parser.add_argument('-linearize', '-l', action="store_true")
    parser.add_argument('-confidence-interval', '-ci', action="store_true")
    parser.add_argument('-cutoff', '-co', type=int, default=0)
    parser.add_argument('-complex', '-cp', action="store_true")
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

def makeAllGtZero(array):
    """
    Takes an array and modifies in place. Adds the lowest number to all members
    of the array. 

    :param array: numpy array containing data to edit
    """
    if not isinstance(array, np.ndarray):
        raise ValueError(
        f"The given array has type {type(data)} but should be of type {type(np.array([0]))}")

    lowest = array.min() 
    if lowest < 0:
        with np.nditer(array, op_flags=['readwrite']) as it:
            for value in it:
                value[...] = abs(lowest) + value

    else:
        return

def normalize(array):
    """
    Normalizes the data passeed into through the array. Array is changed in
    place.

    Keyword arguments:
    array - numpy array containing data
    """
    if not isinstance(array, np.ndarray):
        raise ValueError(
        f"The given array has type {type(data)} but should be of type {type(np.array([0]))}")

    array_max = np.max(array)
    with np.nditer(array, op_flags=['readwrite']) as it:
        for value in it:
            value[...] = value/array_max

def parseData(data_list, scores, confidence_interval = False, verbose = False):
    """
    Places the confidence interval data into the given list

    Keyword arguments:
    data_list - empty list
    """
    if not isinstance(data_list, list) or data_list: 
        raise ValueError(
        f"The given data has type {type(data_list)} but should be of type list")

    for data in scores:
        _, low, high = mean_confidence_interval(np.array(data))

        if confidence_interval:
            #Don't modify iterable while iterating
            copy_data = data
            for num in copy_data:
                if num < low or num > high:
                    data.remove(num)

        data_list.append(describe(data))
        if verbose:
            print(describe(data))

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
    y = np.asarray([d.mean for d in describes]).reshape(-1, 1)
    model_y = y

    ax = plt.axes()

    if args.linearize:
        y_lin = np.exp(y) #Linearize y
        y_norm = np.copy(y_lin)

        y_norm = np.log(y_norm)

        #y_lin 
        model_y = y_lin

        #Supa's way
        b = np.mean(x * y) / np.mean(x * x)
        z = b * x

    model.fit(x, model_y)
    plt.scatter(x, y)

    y_new = model.predict(x)

    #Note: changing the values from the model won't make the fit as perfect, we 
    #would have to apply the same transformation to the original data

    print(y_new)
    y_new = np.log(y_new) #was indented
    y_new = np.flip(y_new)

    for index, ele in enumerate(y_new):
        if np.isnan(ele): 
            y_new[index] = 0
            break

    y_new = np.flip(y_new)
    print("normal", y_new)

    plt.plot(x, y_new, color='red', label="linear-fit")
    #plt.plot(x, np.log(z), color='red', label="linear-fit")
    #print(r2_score(y_new, logy))
    print(f"y = {model.coef_}x + {model.intercept_}")

    plt.ylabel("Mean")
    plt.xlabel("Number of Trials")
    plt.figtext(.1, .9, f"Replications: {replications}")
    plt.title("Average Snake length vs trials")

    if not args.suppress:
        plt.show()

if __name__ == "__main__":
    main()
