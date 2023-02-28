import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

import metcalcpy.util.tost_paired as tp
import metcalcpy.util.utils as calc_util


def get_case_data(series_data, series_vals, indy_vals, rp_diff, total):
    """
        Build a table with summary information for each case.

    :param series_data:
    :param series_vals:
    :param indy_vals:
    :param rp_diff:
    :param total:
    :return:
    """

    # Build a set of unique cases
    case_data = pd.DataFrame()
    case_data['CASE'] = series_data['CASE']
    case_data['LEAD'] = series_data['LEAD']
    case_data['LEAD_HR'] = series_data['LEAD_HR']
    case_data['MIN'] = [None] * len(series_data)
    case_data['MAX'] = [None] * len(series_data)
    case_data['WIN'] = [None] * len(series_data)
    case_data['DIFF'] = [None] * len(series_data)
    case_data['RP_THRESH'] = [None] * len(series_data)
    case_data['DIFF_TEST'] = [None] * len(series_data)
    case_data['RESULT'] = [None] * len(series_data)
    case_data['PLOT'] = [None] * len(series_data)
    case_data['RANK_RANDOM'] = [None] * len(series_data)
    case_data['RANK_MIN'] = [None] * len(series_data)
    case_data = case_data.drop_duplicates()
    case_data.reset_index(inplace=True, drop=True)

    # Check for equal numbers of entries for each case
    list_of_counts = series_data['CASE'].value_counts().tolist()
    count = sum(map(lambda x: x != total, list_of_counts))
    if count != 0:
        raise SystemExit('ERROR: Must have the same number of entries for each case.')
    # Compute summary info for each case
    series_vals_sorted = series_vals[0].copy()
    series_vals_sorted.sort()
    case_data['MIN'] = series_data.groupby('CASE')['PLOT'].min().tolist()
    case_data['MAX'] = series_data.groupby('CASE')['PLOT'].max().tolist()
    case_data['WIN'] = series_data.groupby('CASE')['PLOT'].apply(find_winner, s_v=series_vals_sorted).tolist()
    case_data['DIFF'] = case_data['MAX'] - case_data['MIN']
    case_data['RP_THRESH'] = case_data['LEAD_HR'].apply(find_thresh, args=(indy_vals, rp_diff))
    case_data['DIFF_TEST'] = case_data.apply(lambda x: f'{x["DIFF"]:.5f}' + str(x['RP_THRESH']), axis=1)
    case_data['RESULT'] = case_data.apply(lambda x: eval(x['DIFF_TEST']), axis=1)
    case_data['PLOT'] = case_data.apply(lambda x: x['WIN'] if x['RESULT'] is True else 'TIE', axis=1)
    case_data['RANK_RANDOM'] = series_data.groupby('CASE')['PLOT'].apply(rank_random).tolist()
    case_data['RANK_MIN'] = series_data.groupby('CASE')['PLOT'].apply(rank_min).tolist()
    return case_data


def find_winner(x, s_v):
    """
        functions for case data
        :param x:
        :param s_v:
        :return:
    """
    values = x.tolist()
    if sum(1 for _ in filter(None.__ne__, values)) != len(values):
        return None
    return s_v[values.index(min(values))]


def find_thresh(x, indy_vals, rp_diff):
    """
        # Aggregation functions for case data.
        :param rp_diff:
        :param indy_vals:
        :param x:
        :return:
        """
    thresh_ind = [i for i in range(len(indy_vals)) if indy_vals[i] == x][0]
    return rp_diff[thresh_ind]


def rank_random(x):
    values = x.tolist()
    values_cleaned = [i for i in values if i is not None]
    a = np.random.uniform(low=0, high=1, size=len(values_cleaned))
    zipped_lists = zip(values_cleaned, a)
    sorted_zipped_lists = sorted(zipped_lists)
    sorted_list1 = [element for _, element in sorted_zipped_lists]
    return a.tolist().index(sorted_list1[0]) + 1


def rank_min(x):
    return x.rank(method="min").tolist()[0]


def init_hfip_baseline(config, baseline_file, input_df):
    # Read the HFIP baseline information from a data file.
    baseline = pd.read_csv(os.path.join(sys.path[0], baseline_file),
                           sep=r'\s+', header='infer',
                           quotechar='"', skipinitialspace=True, encoding='utf-8')

    baseline['LEAD_HR'] = baseline['LEAD'] / 10000
    baseline['LEAD_HR'] = baseline['LEAD_HR'].astype('int')

    cur_baseline_data = None
    cur_baseline = "no"
    for stat in config.list_stat_1:
        if config.hfip_bsln == "no" or len(config.get_config_value('derived_series_1')) > 0:
            cur_baseline = "no"
            cur_baseline_data = None
        elif stat in baseline['VARIABLE'].tolist():
            if cur_baseline_data is None:
                all_filters = [baseline['BASIN'].isin(input_df['BASIN']), baseline['VARIABLE'].isin([stat]),
                               baseline['LEAD_HR'].isin(input_df['LEAD_HR'])]
                mask = np.array(all_filters).all(axis=0)
                cur_baseline_data = baseline.loc[mask]
                if config.hfip_bsln == "0":
                    cur_baseline = "HFIP Baseline"
                elif config.hfip_bsln == "5":
                    cur_baseline = 'Error Target for 20% HFIP Goal'
                    cur_baseline_data['VALUE'] = cur_baseline_data['VALUE'].apply(
                        lambda x: calc_util.round_half_up(x * 0.8, 1))
                else:  # config.hfip_bsln == "10":
                    cur_baseline = 'Error Target for 50% HFIP Goal'
                    cur_baseline_data['VALUE'] = cur_baseline_data['VALUE'].apply(
                        lambda x: calc_util.round_half_up(x * 0.5, 1))

    return {'cur_baseline': cur_baseline,
            'cur_baseline_data': cur_baseline_data}


def get_column_val(dep, input_df):
    """
        Get the column values, handling wind data.
        :param dep:
        :param input_df:
        :return:
    """
    # Compute the average of the wind radii, if requested
    if 'AVG_WIND' in dep:
        # Parse the first character and the last 2 characters
        typ = dep[0]
        rad = dep[-2:]

        # Pull wind radii for the 4 quadrants
        ne_wind = input_df[typ + "NE_WIND_" + rad].tolist()
        se_wind = input_df[typ + "SE_WIND_" + rad].tolist()
        sw_wind = input_df[typ + "SW_WIND_" + rad].tolist()
        nw_wind = input_df[typ + "NW_WIND_" + rad].tolist()

        # Replace any instances of 0 with NA
        ne_wind = [None if i == 0 else i for i in ne_wind]
        se_wind = [None if i == 0 else i for i in se_wind]
        sw_wind = [None if i == 0 else i for i in sw_wind]
        nw_wind = [None if i == 0 else i for i in nw_wind]

        # Compute the average
        val = [(ne + se + sw + nw) / 4 for ne, se, sw, nw in zip(ne_wind, se_wind, sw_wind, nw_wind)]

    else:
        # Otherwise, just get the column value
        val = input_df[dep].tolist()
    # For _WIND_ columns, replace any instances of 0 with NA
    if '_WIND_' in dep:
        val = [None if i == 0 else i for i in val]

    return val


def get_prop_ci(x, n, n_min, alpha):
    """
    Compute a confidence interval for a proportion.
    :param alpha:
    :param n_min:
    :param x:
    :param n:
    :return:
    """

    # Compute the standard proportion error
    zval = abs(norm.ppf(alpha / 2))
    phat = x / n
    bound = (zval * ((phat * (1 - phat) + (zval ** 2) / (4 * n)) / n) ** (1 / 2)) / (1 + (zval ** 2) / n)
    midpnt = (phat + (zval ** 2) / (2 * n)) / (1 + (zval ** 2) / n)

    # Compute the statistic and confidence interval
    stat = {'val': 100 * phat}
    if n < n_min:
        stat['ncl'] = None
        stat['ncu'] = None
    else:
        stat['ncl'] = 100 * (midpnt - bound)
        stat['ncu'] = 100 * (midpnt + bound)
    return stat


def get_mean_ci(d, alpha, n_min):
    """
        Compute a confidence interval about the mean.
    :param n_min:
    :param alpha:
    :param d:
    :return:
    """
    len_valid = len([x for x in d if x is not None and ~np.isnan(x)])
    # Degrees of freedom for t-distribution
    df = len_valid - 1

    # replace Nan to None if needed
    if len_valid != len(d):
        d_cleaned = [x for x in d if ~np.isnan(x)]
    else:
        d_cleaned = d
    # Compute the standard error
    s = calc_util.compute_std_err_from_mean(d_cleaned)
    if s[1] == 0:
        tval = abs(tp.qt(alpha / 2, df))
        stderr = tval * s[0]
    else:
        stderr = None

    # Compute the statistic and confidence interval
    stat = {'val': np.nanmean(d)}
    if len_valid < n_min or stderr is None:
        stat['ncl'] = None
        stat['ncu'] = None
    else:
        stat['ncl'] = stat['val'] - stderr
        stat['ncu'] = stat['val'] + stderr

    # Compute the p-value
    if s[0] != 0:
        ss_pval = 0.0 - abs(stat['val'] / s[0])
        cum_t_distrib = tp.pt(ss_pval, df)
    else:
        # in this case in Rscript ss_pval = -Inf and pt(ss_pval, df) = 0
        cum_t_distrib = 0
    stat['pval'] = 1 - 2 * cum_t_distrib

    return stat


def get_median_ci(d, alpha, n_min):
    """
        Compute a confidence interval about the median.
    :param d:
    :param alpha:
    :param n_min:
    :return:
    """
    len_valid = len([x for x in d if x is not None and ~np.isnan(x)])
    # Degrees of freedom for t-distribution
    df = len_valid - 1

    # replace Nan to None if needed
    if len_valid != len(d):
        d_cleaned = [x for x in d if ~np.isnan(x)]
    else:
        d_cleaned = d

    # Compute the standard error
    s = calc_util.compute_std_err_from_median_no_variance_inflation_factor(d_cleaned)
    if s[1] == 0:
        tval = abs(tp.qt(alpha / 2, df))
        stderr = tval * s[0]
    else:
        stderr = None

    # Compute the statistic and confidence interval
    stat = {'val': np.nanmedian(d)}
    if len_valid < n_min or stderr is None:
        stat['ncl'] = None
        stat['ncu'] = None
    else:
        stat['ncl'] = stat['val'] - stderr
        stat['ncu'] = stat['val'] + stderr

    # Compute the p-value
    if s[0] != 0:
        ss_pval = 0.0 - abs(stat['val'] / s[0])
        cum_t_distrib = tp.pt(ss_pval, df)
    else:
        # in this case in Rscript ss_pval = -Inf and pt(ss_pval, df) = 0
        cum_t_distrib = 0

    stat['pval'] = 1 - 2 * cum_t_distrib

    return stat


def common_member(a, b):
    """
        method to check if two lists have at-least one element common
    :param a:
    :param b:
    :return:
    """
    a_set = set(a)
    b_set = set(b)
    if len(a_set.intersection(b_set)) > 0:
        return True
    return False


def get_dep_column(stat, column_info, input_df):
    """
        Get a column of data to be plotted, handling absolute values and differences.
    :param stat:
    :param column_info:
    :param input_df:
    :return:
    """
    # Check for absolute value
    abs_flag = stat[0: 3] == 'ABS'

    # Split based on differences
    if abs_flag is True:
        dep = re.split(r'[()]', stat)[1]
    else:
        dep = stat
    diff_list = re.split(r'-', dep)

    # Initialize output
    col_to_plot = {'val': get_column_val(diff_list[0], input_df)}
    list_desc = column_info[column_info['COLUMN'] == diff_list[0]]['DESCRIPTION'].tolist()
    if len(list_desc) > 0:
        col_to_plot['desc'] = list_desc[0]
        col_to_plot['units'] = column_info[column_info['COLUMN'] == diff_list[0]]['UNITS'].tolist()[0]
    else:
        col_to_plot['desc'] = ''
        col_to_plot['units'] = ''
    # Loop over any remaining entries
    for i in range(1, len(diff_list), 1):
        val = get_column_val(diff_list[i], input_df)
        col_to_plot['val'] = [x - y for x, y in zip(col_to_plot['val'], val)]

        col_to_plot['desc'] = f"{col_to_plot['desc']}-{column_info[column_info['COLUMN'] == diff_list[i]]['DESCRIPTION'].tolist()[0]}"
        # Only append units that differ
        if col_to_plot['units'] != column_info[column_info['COLUMN'] == diff_list[i]]['UNITS'].tolist()[0]:
            col_to_plot['units'] = f"{col_to_plot['units']}{column_info[column_info['COLUMN'] == diff_list[i]]['UNITS'].tolist()[0]}"
    # Apply absolute value
    if abs_flag is True:
        col_to_plot['val'] = [abs(ele) for ele in col_to_plot['val']]
        col_to_plot['desc'] = f"Absolute Value of {col_to_plot['desc']}"

    return col_to_plot
