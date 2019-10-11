"""
Class Name: line.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import os
import plotly.graph_objects as go
import yaml
import pandas as pd
import numpy as np
from plots.met_plot import MetPlot

class Line(MetPlot):
    def __init__(self, parameters, data1, data2):
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by the parameters.

        """
        # read defaults stored in YAML formatted file into the dictionary
        location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(location, 'line_defaults.yaml'), 'r') as stream:
            try:
                defaults = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print(exc)

        # init common layout
        super().__init__(parameters, defaults)
        # create figure
        self.figure = self._create_figure(data1, data2)

    def _create_figure(self, data1, data2):
        """ Create a line plot"""
        fig = go.Figure()

        # Data comprising the first line
        line1_x = data1['x']
        print(line1_x)
        line1_y = data1['y']
        fig.add_trace(go.Scatter(x=line1_x, y=line1_y, name='Line1', line=dict(color='firebrick', width=4)))

        # Data comprising the second line
        line2_x = data2['x']
        line2_y = data2['y']
        fig.add_trace(go.Scatter(x=line2_x, y=line2_y, name='Line2', connectgaps=True,line=dict(color='green', width=4, dash='dash')))


        # Edit the layout
        fig.update_layout(title='Sample data', xaxis_title="x-values", yaxis_title='y-values')

        fig.show()


def main():
    # read user's data from file and arrange it in the array
    input_data_file1 = "/Users/minnawin/feature_19_line/METplotpy/metplotpy/plots/line/line1_plot_data.txt"
    data1 = pd.read_csv(input_data_file1, delim_whitespace=True)

    # Dropping rows with NaN:
    data1 = data1.dropna()
    print(data1)

    input_data_file2 = "/Users/minnawin/feature_19_line/METplotpy/metplotpy/plots/line/line2_plot_data.txt"
    data2 = pd.read_csv(input_data_file2, delim_whitespace=True)
    data2_none = data2.where((pd.notnull(data2)), None)
    data2_dropna = data2.dropna()
    print(data2_none)

    lplot = Line(data1, data2_none)
    # lplot = Line(data1, data2_dropna)




if __name__ == "__main__":
    main()
