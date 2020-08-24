import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator


def plotGraph(data, labels, ylabel=None, title=None, saveLoc=None):
    years = mdates.YearLocator(1)  # major tick every 2 years
    months = mdates.MonthLocator(interval=6)  # minor tick every 3 months

    styles = ['b-', 'r--', 'y-.', 'g:']
    styles = styles[0:len(data.columns)]

    fig, ax = plt.subplots()
    data.plot(style=styles, lw=1, ax=ax, markersize=3)

    ax.xaxis.set_minor_locator(years)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))

    plt.legend(loc=9, bbox_to_anchor=(0.5, -0.2), labels=labels)
    plt.xlabel('Date')
    plt.ylabel(ylabel)
    plt.grid()

    if title is not None:
        plt.title(title)
    if saveLoc is not None:
        plt.savefig(saveLoc, bbox_inches='tight', dpi = 300, ncols=2)
    plt.show()
