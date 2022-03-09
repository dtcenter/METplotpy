#!/usr/bin/env conda run -n diff_index_plot python
# -*- coding: utf-8 -*-
"""
Load fieldijn from npz file created with save_ensemble_data.py
helper function, compute ensemble mean and spread, compute
difficulty index for a set of thresholds, plot and save the results.
Created on Tue Mar 17 08:06:07 2020
Last modified Mon Apr 6 11:30:30 2020
@author: campbell

Taken from original test_difficulty_index.py but replacing with METcalcpy and METplotpy.

"""
import argparse
import yaml
import numpy as np
import matplotlib.pyplot as plt
from metcalcpy.calc_difficulty_index import forecast_difficulty as di
from metcalcpy.calc_difficulty_index import EPS
from metcalcpy.piecewise_linear import PiecewiseLinear as plin
import metplotpy.plots.difficulty_index.mycolormaps as mcmap
from metplotpy.plots.difficulty_index.plot_difficulty_index import plot_field


def load_data(filename):
    """Load ensemble data from file"""
    loaded = np.load(filename)
    lats, lons = (loaded['lats'], loaded['lons'])
    fieldijn = np.ma.masked_invalid(
        np.ma.masked_array(
            data=loaded['data'],
            mask=loaded['mask']))

    return lats, lons, fieldijn


def compute_stats(field):
    """Compute mean and std dev"""
    mu = np.mean(field, axis=-1)
    sigma = np.std(field, axis=-1, ddof=1)

    return mu, sigma


def compute_difficulty_index(field, mu, sigma, thresholds):
    """
    Compute difficulty index for an ensemble forecast given
    a set of thresholds, returning a dictionary of fields.
    """
    dij = {}
    for threshold in thresholds:
        dij[threshold] =\
            di(sigma, mu, threshold, field, Aplin=None, sigma_over_mu_ref=EPS)

    return dij


def plot_difficulty_index(dij, lats, lons, thresholds):
    """
    Plot the difficulty index for a set of thresholds,
    returning a dictionary of figures
    """
    plt.close('all')
    myparams = {'figure.figsize': (8, 5),
                'figure.max_open_warning': 40}
    plt.rcParams.update(myparams)
    figs = {}
    units = 'feet'
    cmap = mcmap.stoplight()
    for threshold in thresholds:
        if np.max(dij[threshold]) <= 1.0:
            vmax = 1.0
        else:
            vmax = 1.5
        figs[threshold] =\
            plot_field(dij[threshold],
                          lats, lons, vmin=0.0, vmax=vmax, cmap=cmap,
                          xlab='Longitude \u00b0E', ylab='Latitude',
                          clab='thresh={} {}'.format(threshold, units),
                          title='Forecast Decision Difficulty Index')

    return figs


def save_difficulty_figures(config, figs, save_thresh, units='feet'):
    """
    Save subset of difficulty index figures.
    """
    fig_fmt = 'png'
    fig_basename = config['diff_fig_basename']
    for thresh in save_thresh:
        thresh_str = '{:.2f}'.format(thresh).replace('.', '_')
        fig_name = (fig_basename + thresh_str +
                    '_' + units + '.' + fig_fmt)
        print('Saving {}...\n'.format(fig_name))
        figs[thresh].savefig(fig_name, format=fig_fmt)


def plot_statistics(mu, sigma, lats, lons, units='feet'):
    """Plot ensemble mean and spread, returning figure handles"""
    cmap = mcmap.spectral()
    mu_fig =\
        plot_field(mu, lats, lons, cmap=cmap, clab=units,
                      vmin=0.0, vmax=np.nanmax(mu),
                      xlab='Longitude \u00b0E',
                      ylab='Latitude',
                      title='Forecast Ensemble Mean')
    sigma_fig =\
        plot_field(sigma, lats, lons, cmap=cmap, clab=units,
                      vmin=0.0, vmax=np.nanmax(sigma),
                      xlab='Longitude \u00b0E',
                      ylab='Latitude',
                      title='Forecast Ensemble Std')

    return mu_fig, sigma_fig


def save_stats_figures(config, mu_fig, sigma_fig):
    """
    Save ensemble mean and spread figures.
    """
    fig_fmt = 'png'
    fig_basename = config['stat_fig_basename']
    mu_name = fig_basename + 'mean.' + fig_fmt
    print('Saving {}...\n'.format(mu_name))
    mu_fig.savefig(mu_name, format=fig_fmt)
    sigma_name = fig_basename + 'std.' + fig_fmt
    print('Saving {}...\n'.format(sigma_name))
    sigma_fig.savefig(sigma_name, format=fig_fmt)


def main(config):
    """
    Load fieldijn from npz file created with save_ensemble_data.py
    helper function, compute ensemble mean and spread, compute
    difficulty index for a set of thresholds, plot and save the results.
    """
    filename = config['input_filename']
    lats, lons, fieldijn = load_data(filename)
    muij, sigmaij = compute_stats(fieldijn)
    thresholds = np.arange(4.0, 16.0, 1.0)
    dij = compute_difficulty_index(fieldijn, muij, sigmaij, thresholds)
    figs = plot_difficulty_index(dij, lats, lons, thresholds)
    save_thresh = np.arange(9.0, 13.0, 1.0)
    save_difficulty_figures(config, figs, save_thresh)
    units = 'feet'
    mu_fig, sigma_fig =\
        plot_statistics(muij, sigmaij, lats, lons, units=units)
    save_stats_figures(config, mu_fig, sigma_fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Example Difficulty Index Plotting')

    parser.add_argument(
        '--config', type=str, dest='config',
        required=True)

    input_args = parser.parse_args()

    """
    Read YAML configuration file
    """
    config = yaml.load(
        open(input_args.config), Loader=yaml.FullLoader)

    main(config)
