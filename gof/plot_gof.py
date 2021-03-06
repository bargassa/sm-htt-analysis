#!/usr/bin/env python

import argparse
import os
import json
import yaml
import numpy as np

import matplotlib as mpl
mpl.use('Agg')
mpl.rcParams['font.size'] = 16
import matplotlib.pyplot as plt
from matplotlib import cm

import logging
logger = logging.getLogger("plot_gof")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Plot goodness of fit results")
    parser.add_argument(
        "variables", help="Considered variables in goodness of fit test")
    parser.add_argument(
        "path", help="Path to directory with goodness of fit results")
    parser.add_argument("channel", help="Select channel to be plotted")
    return parser.parse_args()


def make_cmap(colors, position):
    if len(position) != len(colors):
        raise Exception("position length must be the same as colors")
    elif position[0] != 0 or position[-1] != 1:
        raise Exception("position must start with 0 and end with 1")

    cdict = {'red': [], 'green': [], 'blue': []}
    for pos, color in zip(position, colors):
        cdict['red'].append((pos, color[0], color[0]))
        cdict['green'].append((pos, color[1], color[1]))
        cdict['blue'].append((pos, color[2], color[2]))

    cmap = mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 256)
    return cmap


def plot_2d(variables, results, filename):
    plt.figure(figsize=(1.5 * len(variables), 1.0 * len(variables)))
    a = plt.gca()
    for i1 in range(len(variables)):
        for i2 in range(len(variables)):
            if results[i1, i2] == -1.0:
                results[i1, i2] = np.nan
                continue
            if i1 >= i2:
                results[i1, i2] = np.nan
                continue
            a.text(
                i1 + 0.5,
                i2 + 0.5,
                '{0:.2f}'.format(results[i1, i2]),
                ha='center',
                va='center')
    cmap = make_cmap([(1, 0, 0), (1, 1, 0), (0, 1, 0)],
                     np.array([0.0, 0.05, 1.0]))
    cmap.set_bad(color='w')
    results = np.ma.masked_invalid(results)
    p = plt.pcolormesh(results.T, vmin=0.0, vmax=1.0, cmap=cmap)
    cbar = plt.colorbar(p)
    cbar.set_label(
        'Saturated goodness of fit p-value', rotation=270, labelpad=50)
    plt.xticks(
        np.array(range(len(variables))) + 0.5, variables, rotation='vertical')
    plt.yticks(
        np.array(range(len(variables))) + 0.5,
        variables,
        rotation='horizontal')
    plt.xlim(0, len(variables))
    plt.ylim(0, len(variables))
    plt.savefig(filename, bbox_inches='tight')


def plot_1d(variables, results, filename):
    plt.figure(figsize=(len(variables) * 0.5, 5.0))
    y = results
    x = range(len(y))
    plt.plot(x, y, '+', mew=4, ms=16)
    plt.ylim((-0.05, 1.05))
    plt.xlim((-0.5, len(x) - 0.5))
    plt.xticks(x, variables, rotation='vertical')
    plt.axhline(y=0.05, linewidth=3, color='r')
    plt.ylabel('Saturated goodness of fit p-value', labelpad=20)
    ax = plt.gca()
    ax.xaxis.grid()
    plt.savefig(filename, bbox_inches="tight")


def search_results_1d(path, channel, variables):
    results = []
    missing = []
    for variable in variables:
        filename = os.path.join(path, "{}_{}".format(channel, variable),
                                "gof.json")
        if not os.path.exists(filename):
            missing.append(variable)
            results.append(-1.0)
            continue
        logger.debug(
            "Found goodness of fit result for variable %s in channel %s.",
            variable, channel)

        p_value = json.load(open(filename))
        results.append(p_value["125.0"]["p"])

    return missing, results


def search_results_2d(path, channel, variables):
    missing = []
    results = np.ones((len(variables), len(variables))) * (-1.0)
    for i1, v1 in enumerate(variables):
        for i2, v2 in enumerate(variables):
            if i2 <= i1:
                continue
            filename = os.path.join(path, "{}_{}_{}".format(channel, v1, v2),
                                    "gof.json")
            if not os.path.exists(filename):
                missing.append("{}_{}".format(v1, v2))
                continue
            logger.debug(
                "Found goodness of fit result for variable pair (%s, %s) in channel %s.",
                v1, v2, channel)

            p_value = json.load(open(filename))
            results[i1, i2] = p_value["125.0"]["p"]

    return missing, results


def main(args):
    if not os.path.exists(args.variables):
        logger.fatal("File %s does not exist.")
        raise Exception
    if not os.path.exists(args.path):
        logger.fatal("Path %s does not exist.")
        raise Exception

    # Plot 1D gof results
    variables = yaml.load(open(args.variables))["variables"]
    missing_1d, results_1d = search_results_1d(args.path, args.channel,
                                               variables)
    logger.debug("Missing variables for 1D plot in channel %s:", args.channel)
    for variable in missing_1d:
        print("{} {}".format(args.channel, variable))

    plot_1d(variables, results_1d, "{}_gof_1d.png".format(args.channel))

    # Plot 2D gof results
    missing_2d, results_2d = search_results_2d(args.path, args.channel,
                                               variables)
    logger.debug("Missing variables for 2D plot in channel %s:", args.channel)
    for variable in missing_2d:
        print("{} {}".format(args.channel, variable))

    plot_2d(variables, results_2d, "{}_gof_2d.png".format(args.channel))

    # Apply selection criterica
    variables_selected = []
    logger.info("Find well described variables for channel %s:", args.channel)
    for i, v in enumerate(variables):
        if results_1d[i] > 0.05:
            variables_selected.append(v)
            print("- {}".format(v))

    # Plot 1D gof results for reduced variable set
    results_1d_selected = [
        results_1d[i] for i, v in enumerate(variables)
        if v in variables_selected
    ]

    plot_1d(variables_selected, results_1d_selected,
            "{}_gof_1d_selected.png".format(args.channel))

    # Plot 2D gof results for reduced variable set
    missing_2d_selected, results_2d_selected = search_results_2d(
        args.path, args.channel, variables_selected)
    plot_2d(variables_selected, results_2d_selected,
            "{}_gof_2d_selected.png".format(args.channel))


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
