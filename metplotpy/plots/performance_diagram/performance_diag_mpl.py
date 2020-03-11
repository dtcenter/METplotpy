import matplotlib.pyplot as plt
import numpy as np


def performance_diagram(perf_data):
    '''
        A preliminary script that generates performance diagram of one fictitious model of data with POD and FAR
        values.  Hard-coding of labels for x-axis, y-axis, CSI lines and bias lines, contour colors for the CSI
        curves.  


        Args:
            perf_data: A list of performance data in the form of dictionary with keys of POD and SUCCESS_RATE

        Returns:
            Generates a performance diagram with eqaul lines of CSI (Critical Success Index) and equal lines
            of bias
    '''
    figsize = (9, 8)
    markers = ['.', '*']
    colors = ['r', 'k']
    xlabel = "Success Ratio (1-FAR)"
    ylabel = "Probability of Detection"
    ticks = np.arange(0.1, 1.1, 0.1)
    dpi = 300
    csi_cmap = "Blues"
    csi_label = "Critical Success Index"
    title = "Performance Diagram"
    # set the start value to a non-zero number to avoid the runtime divide-by-zero error
    grid_ticks = np.arange(0.000001, 1.01, 0.01)
    sr_g, pod_g = np.meshgrid(grid_ticks, grid_ticks)
    bias = pod_g / sr_g
    csi = 1.0 / (1.0 / sr_g + 1.0 / pod_g - 1.0)
    csi_contour = plt.contourf(sr_g, pod_g, csi, np.arange(0.1, 1.1, 0.1), extend="max", cmap=csi_cmap)
    # csi_contour = plt.contourf(sr_g, pod_g, csi, np.arange(0.1, 1.1, 0.1), extend="max")
    b_contour = plt.contour(sr_g, pod_g, bias, [0.5, 1, 1.5, 2, 4], colors="k", linestyles="dashed")
    plt.clabel(b_contour, fmt="%1.1f", manual=[(0.2, 0.9), (0.4, 0.9), (0.6, 0.9), (0.7, 0.7)])
    cbar = plt.colorbar(csi_contour)
    cbar.set_label(csi_label, fontsize=14)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.xticks(ticks)
    plt.yticks(ticks)
    plt.title(title, fontsize=14, fontweight="bold")
    plt.text(0.48, 0.6, "Frequency Bias", fontdict=dict(fontsize=14, rotation=45))
    # plt.legend(**legend_params)
    # plt.figure(figsize=figsize)
    for perf in perf_data:
        plt.plot(perf["SUCCESS_RATIO"], perf["POD"], marker=".", color='r',
                  label="label")
    plt.show()

def generate_random_data(n):
    ''' return a list of dictionaries containing the Performance data:
        perf_data[i] = {'SUCCESS_RATIO': .xyz, 'POD': .lmn}
        Where the success ratio=1- FAR

        Args:
            n:  The number of POD,Success ratio performance point "pairs"
        Returns:
            perf_data: A list of POD and FAR values represented as a dictionary
    '''

    perf_data = []
    # create n-sets of POD, FAR dataset
    far = np.random.randint(size=n, low=1, high=9)
    np.random.seed(seed=234)
    pod = np.random.randint(size=n, low=1, high=9)

    # Realistic values are between 0 and 1.0 let's multiply each value by 0.1
    pod_values = [x*.01 for x in pod]

    # success ratio, 1-FAR; multiply each FAR value by 0.1 then do arithmetic
    # to convert to the success ratio
    success_ratio = [1-x*0.1 for x in far]

    for i in range(n):
        cur_perf = {}
        cur_perf["POD"] = pod_values[i]
        cur_perf["SUCCESS_RATIO"] =success_ratio[i]
        perf_data.append(cur_perf)

    return perf_data

if __name__ == "__main__":

    # number of POD, 1-FAR
    num = 7
    perf_list = generate_random_data(num)
    for perf in perf_list:
        pod = perf["POD"]
        success = perf['SUCCESS_RATIO']
        # print(f'pod: {pod}| success ratio:{success}')

    performance_diagram(perf_list)
