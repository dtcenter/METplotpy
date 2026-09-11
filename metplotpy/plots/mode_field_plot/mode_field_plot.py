# ============================*
# ** Copyright UCAR (c) 2026
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

"""
Class Name: ModeFieldPlot
 """
__author__ = 'Minna Win'

import os
import sys
from datetime import datetime
import yaml

import numpy as np
import netCDF4 as nc
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects  # noqa: F401  (used inside add_object_labels)
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
from cartopy.feature import ShapelyFeature
from metplotpy.plots.mode_field_plot.mode_field_plot_config import ModeFieldPlotConfig
from metplotpy.plots import util
from metplotpy.plots.util import get_common_logger as logging


class ModeFieldPlot:
    """
        Python implementation of the deprecated MET application: plot_mode_field
       This code is a configurable version of the script created by Michelle Harrold.

       A default configuration file in the METplotpy/metplotpy/plots/config directory
       contains default values for plot settings.  The user provides a *required*
       configuration file to customize the plot based on their data.

    """


    def __init__(self, params: dict) -> None:
        default_conf_filename = "mode_field_plot_defaults.yaml"

        # Determine location of the default YAML config files and then
        # read defaults stored in YAML formatted file into the dictionary
        if 'METPLOTPY_BASE' in os.environ:
            location = os.path.join(os.environ['METPLOTPY_BASE'], 'metplotpy/plots/config')
        else:
            location = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))

        with open(os.path.join(location, default_conf_filename), 'r') as stream:
            try:
                defaults = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print(exc)

        # merge user defined parameters into defaults
        if params:
            self.settings = {**defaults, **params}
        else:
            self.settings = defaults

        # instantiate the config object
        self.config_obj = ModeFieldPlotConfig(self.settings)
        self.logger = self.config_obj.logger

        # Retrieve the Natural Earth shapefile either
        # online, or use the shapefile in the mode_field_plot
        # directory
        if self.config_obj.download_shapefile:
            shp_path = shpreader.natural_earth(
                resolution="50m", category="physical", name="coastline"
            )
            reader = shpreader.Reader(shp_path)
        else:
            # use existing shapefile
            srcdir = os.path.dirname(__file__)
            parent = os.path.join(srcdir, "shapefile")
            local_shapefile = os.path.join(parent, "ne_50m_coastline.shp")
            reader = shpreader.Reader(local_shapefile)

        geoms = list(reader.geometries())
        self.shapefile_geoms = geoms


    def plot_mode_objects(self) -> None:
        """
        Plot the raw forecast and observation fields (same layout/crop as
        plot_mode_objects), sharing one colorbar for direct visual comparison.

        Args:
            :param self: used to retrieve the necessary plot settings defined in the
                              YAML config file
         :return: None

        """

        nc_path = self.config_obj.input_file
        out_path = self.config_obj.output_filename
        pad = self.config_obj.padding
        dpi = int(self.config_obj.resolution_dpi)
        label_objects: bool = self.config_obj.labels_on
        fig_width = self.config_obj.plot_width
        hspace = self.config_obj.vert_spacing
        super_title_text = self.config_obj.super_title_text
        super_title_fontsize = self.config_obj.super_title_font_size

        subplot_top = self.config_obj.subplot_adjust_top
        subplot_bottom = self.config_obj.subplot_adjust_bottom
        subplot_right = self.config_obj.subplot_adjust_right
        subplot_left = self.config_obj.subplot_adjust_left

        d = self.load_mode_obj(nc_path)

        lon, (fcst_id, fcst_clus, obs_id, obs_clus, fcst_raw, obs_raw) = self.roll_to_pm180(
            d["lon"], d["fcst_obj_id"], d["fcst_clus_id"], d["obs_obj_id"],
            d["obs_clus_id"], d["fcst_raw"], d["obs_raw"],
        )

        lat = d["lat"]

        extent = self.get_extent(lat, lon, fcst_id, obs_id, pad=pad)

        ids, color_map = self.build_cluster_cmap([fcst_clus, obs_clus])
        fcst_rgba = self.build_rgba(fcst_id, fcst_clus, color_map)
        obs_rgba = self.build_rgba(obs_id, obs_clus, color_map)

        coast_geoms = self.shapefile_geoms
        proj = ccrs.PlateCarree()

        # Cartopy's PlateCarree axes enforce a 1:1 data aspect ratio, so we size
        # the figure to match the extent's aspect ratio ourselves -- otherwise
        # matplotlib pads out the leftover space as big gaps around each map.
        lon_range = extent[1] - extent[0]
        lat_range = extent[3] - extent[2]
        map_aspect = lon_range / lat_range  # width / height, per panel
        map_height = fig_width / map_aspect
        title_space = self.config_obj.title_space  # per-panel title
        top_bottom_margin = self.config_obj.top_bottom_margin  # suptitle allowance
        fig_height = 2 * (map_height + title_space) + top_bottom_margin

        fig, axes = plt.subplots(
            2, 1, figsize=(fig_width, fig_height), subplot_kw={"projection": proj},
        )

        fig.subplots_adjust(hspace=hspace, top=subplot_top, bottom=subplot_bottom, left=subplot_left,
                            right=subplot_right)
        fcst_init_str = util.parse_met_time(d["fcst_init_time"])
        fcst_valid_str = util.parse_met_time(d["fcst_valid_time"])
        obs_valid_str = util.parse_met_time(d["obs_valid_time"])

        fcst_time_line = ""
        if fcst_init_str or fcst_valid_str:
            parts = []
            if fcst_init_str:
                parts.append(f"Init: {fcst_init_str}")
            if fcst_valid_str:
                parts.append(f"Valid: {fcst_valid_str}")
            fcst_time_line = "  |  " + "   ".join(parts)

        obs_time_line = f"  |  Valid: {obs_valid_str}" if obs_valid_str else ""

        titles = [
            f"Forecast objects  |  {d['model']}  {d['fcst_var']} {d['fcst_level']}  "
            f"({d['fcst_thresh']}){fcst_time_line}",
            f"Observation objects  |  {d['obtype']}  {d['obs_var']} {d['obs_level']}  "
            f"({d['obs_thresh']}){obs_time_line}",
        ]
        rgba_fields = [fcst_rgba, obs_rgba]

        for ax, rgba, title in zip(axes, rgba_fields, titles):
            ax.set_extent(extent, crs=proj)
            coast_feat = ShapelyFeature(
                coast_geoms, proj, facecolor="0.92", edgecolor="0.35", linewidth=0.5
            )
            ax.add_feature(coast_feat, zorder=0)
            ax.imshow(
                rgba, origin="lower", extent=[lon.min(), lon.max(), lat.min(), lat.max()],
                transform=proj, interpolation="nearest", zorder=2,
            )
            gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="gray", alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False
            ax.set_title(title, fontsize=11, fontweight="bold")

        if label_objects:
            self.add_object_labels(axes[0], fcst_id, lat, lon, proj)
            self.add_object_labels(axes[1], obs_id, lat, lon, proj)

        fig.suptitle(
            super_title_text,
            fontsize=super_title_fontsize,
        )

        fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
        plt.tight_layout()
        self.logger.info(f"Wrote {out_path}")


    def plot_mode_raw(self):
        """Plot the raw forecast and observation fields (same layout/crop as
        plot_mode_objects), sharing one colorbar for direct visual comparison."""

        nc_path = self.config_obj.input_file
        out_path = self.config_obj.output_filename
        pad = self.config_obj.padding
        dpi = int(self.config_obj.resolution_dpi)
        label_objects: bool = self.config_obj.labels_on
        fig_width = self.config_obj.plot_width
        hspace = self.config_obj.vert_spacing
        super_title_text = self.config_obj.super_title_text
        super_title_fontsize = self.config_obj.super_title_font_size
        cmap_name = self.config_obj.cmap
        vmin = self.config_obj.vmin
        vmax = self.config_obj.vmax

        d = self.load_mode_obj(nc_path)

        lon, (fcst_id, obs_id, fcst_raw, obs_raw) = self.roll_to_pm180(
            d["lon"], d["fcst_obj_id"], d["obs_obj_id"], d["fcst_raw"], d["obs_raw"],
        )
        lat = d["lat"]

        # Reuse the same object-derived bounding box so the raw-field plot lines
        # up with the object plot at the same zoom level.
        extent = self.get_extent(lat, lon, fcst_id, obs_id, pad=pad)

        fcst_plot = np.ma.masked_less(np.ma.masked_invalid(fcst_raw), 0)
        obs_plot = np.ma.masked_less(np.ma.masked_invalid(obs_raw), 0)

        if vmax is None:
            combined = np.concatenate([fcst_plot.compressed(), obs_plot.compressed()])
            vmax = float(np.percentile(combined, self.config_obj.vmax_pctile)) if combined.size else 1.0

        coast_geoms = self.shapefile_geoms
        proj = ccrs.PlateCarree()

        lon_range = extent[1] - extent[0]
        lat_range = extent[3] - extent[2]
        map_aspect = lon_range / lat_range
        map_height = fig_width / map_aspect
        title_space = self.config_obj.title_space
        top_bottom_margin = self.config_obj.top_bottom_margin
        fig_height = 2 * (map_height + title_space) + top_bottom_margin

        fig, axes = plt.subplots(
            2, 1, figsize=(fig_width, fig_height), subplot_kw={"projection": proj},
        )
        # Leave extra room on the right for a shared colorbar.
        fig.subplots_adjust(hspace=hspace, top=0.90, bottom=0.04, left=0.05, right=0.88)

        fcst_init_str = util.parse_met_time(d["fcst_init_time"])
        fcst_valid_str = util.parse_met_time(d["fcst_valid_time"])
        obs_valid_str = util.parse_met_time(d["obs_valid_time"])

        fcst_time_line = ""
        if fcst_init_str or fcst_valid_str:
            parts = []
            if fcst_init_str:
                parts.append(f"Init: {fcst_init_str}")
            if fcst_valid_str:
                parts.append(f"Valid: {fcst_valid_str}")
            fcst_time_line = "  |  " + "   ".join(parts)
        obs_time_line = f"  |  Valid: {obs_valid_str}" if obs_valid_str else ""

        titles = [
            f"{d['model']}  {d['fcst_var']} {d['fcst_level']}  "
            #        f"({d['fcst_units']}){fcst_time_line}",
            f"(mm){fcst_time_line}",
            f"{d['obtype']}  {d['obs_var']} {d['obs_level']}  "
            #        f"({d['obs_units']}){obs_time_line}",
            f"(mm)",
        ]
        fields = [fcst_plot, obs_plot]

        im = None
        for ax, field, title in zip(axes, fields, titles):
            ax.set_extent(extent, crs=proj)
            im = ax.imshow(
                field, origin="lower", extent=[lon.min(), lon.max(), lat.min(), lat.max()],
                transform=proj, cmap=cmap_name, vmin=vmin, vmax=vmax,
                interpolation="nearest", zorder=2,
            )
            # Coastlines drawn as outline-only on top of the data (no fill),
            # since the data covers the whole domain here.
            coast_feat = ShapelyFeature(
                coast_geoms, proj, facecolor="none", edgecolor="black", linewidth=0.6
            )
            ax.add_feature(coast_feat, zorder=3)
            gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="gray", alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False
            ax.set_title(title, fontsize=11, fontweight="bold")

        cbar = fig.colorbar(im, ax=axes, shrink=0.75, pad=0.02, extend="max")
        if len(self.config_obj.colorbar_label) == 0:
            cbar.set_label(f"{d['fcst_var']} ({d['fcst_units']})", fontsize=self.config_obj.colorbar_label_fontsize)
        else:
            cbar.set_label(self.config_obj.colorbar_label, fontsize=self.config_obj.colorbar_label_fontsize)

        fig.suptitle(super_title_text,
                     fontsize=super_title_fontsize
                     )

        fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
        print(f"Wrote {out_path}")


    def build_cluster_cmap(self, clus_ids_list):
        """Build a consistent discrete colormap for cluster ids across panels."""
        all_ids = set()
        for arr in clus_ids_list:
            vals = arr.compressed() if np.ma.is_masked(arr) else arr.ravel()
            vals = vals[vals > 0]
            all_ids.update(np.unique(vals).tolist())
        ids = sorted(all_ids)

        base_colors = plt.get_cmap("tab20").colors + plt.get_cmap("tab20b").colors
        color_map = {cid: base_colors[i % len(base_colors)] for i, cid in enumerate(ids)}
        return ids, color_map


    def add_object_labels(self, ax, obj_id, lat, lon, proj, fontsize=7):
        """Label each individual object with its object id at its centroid."""
        data = obj_id.filled(-1) if np.ma.is_masked(obj_id) else obj_id
        ids = np.unique(data)
        ids = ids[ids > 0]
        lon2d, lat2d = np.meshgrid(lon, lat)
        for oid in ids:
            m = data == oid
            clat = lat2d[m].mean()
            clon = lon2d[m].mean()
            ax.text(
                clon, clat, str(int(oid)),
                transform=proj, fontsize=fontsize, fontweight="bold",
                ha="center", va="center", color="black",
                path_effects=[
                    matplotlib.patheffects.withStroke(linewidth=2, foreground="white"),
                ],
            )


    def load_mode_obj(self, path):
        ds = nc.Dataset(path)
        d = {
            "lat": ds.variables["lat"][:],
            "lon": ds.variables["lon"][:],
            "fcst_raw": ds.variables["fcst_raw"][:],
            "fcst_obj_id": ds.variables["fcst_obj_id"][:],
            "fcst_clus_id": ds.variables["fcst_clus_id"][:],
            "obs_raw": ds.variables["obs_raw"][:],
            "obs_obj_id": ds.variables["obs_obj_id"][:],
            "obs_clus_id": ds.variables["obs_clus_id"][:],
            "fcst_var": util.decode_char_var(ds.variables["fcst_variable"]),
            "obs_var": util.decode_char_var(ds.variables["obs_variable"]),
            "fcst_level": util.decode_char_var(ds.variables["fcst_level"]),
            "obs_level": util.decode_char_var(ds.variables["obs_level"]),
            "fcst_thresh": util.decode_char_var(ds.variables["fcst_conv_threshold"]),
            "obs_thresh": util.decode_char_var(ds.variables["obs_conv_threshold"]),
            "fcst_units": util.decode_char_var(ds.variables["fcst_units"]),
            "obs_units": util.decode_char_var(ds.variables["obs_units"]),
            "model": getattr(ds, "model", ""),
            "obtype": getattr(ds, "obtype", ""),
            "fcst_init_time": getattr(ds.variables["fcst_raw"], "init_time", None),
            "fcst_valid_time": getattr(ds.variables["fcst_raw"], "valid_time", None),
            "obs_valid_time": getattr(ds.variables["obs_raw"], "valid_time", None),
        }
        ds.close()
        return d


    def build_rgba(self, obj_id, clus_id, color_map, unmatched_color=(0.0, 0.0, 1.0)):
        """Build an RGBA image from object/cluster ids.

        Any pixel that belongs to an object (obj_id valid) is colored:
        - by its cluster's color, if that cluster matched across fcst/obs
          (clus_id > 0)
        - by `unmatched_color` (default blue), if the object had no match
          (clus_id == -1, MODE's code for "no cluster/pair")
        """
        obj_data = obj_id.filled(-1) if np.ma.is_masked(obj_id) else obj_id
        clus_data = clus_id.filled(-1) if np.ma.is_masked(clus_id) else clus_id

        h, w = obj_data.shape
        rgba = np.zeros((h, w, 4), dtype=float)

        has_obj = obj_data > 0
        matched = has_obj & (clus_data > 0)
        unmatched = has_obj & (clus_data <= 0)

        for cid, color in color_map.items():
            m = matched & (clus_data == cid)
            if not m.any():
                continue
            rgba[m, 0] = color[0]
            rgba[m, 1] = color[1]
            rgba[m, 2] = color[2]
            rgba[m, 3] = 0.75

        if unmatched.any():
            rgba[unmatched, 0] = unmatched_color[0]
            rgba[unmatched, 1] = unmatched_color[1]
            rgba[unmatched, 2] = unmatched_color[2]
            rgba[unmatched, 3] = 0.75

        return rgba


    def roll_to_pm180(self, lon, *fields):
        """Roll a 0-360 lon axis (and matching 2D fields) to -180..180."""
        lon = np.asarray(lon)
        lon_adj = np.where(lon > 180, lon - 360, lon)
        order = np.argsort(lon_adj)
        lon_out = lon_adj[order]
        fields_out = [f[:, order] for f in fields]
        return lon_out, fields_out


    def get_extent(self, lat, lon, *id_fields, pad=5.0):
        """Bounding box (lon-lat) covering all non-missing object pixels, padded."""
        mask = np.zeros(id_fields[0].shape, dtype=bool)
        for f in id_fields:
            mask |= ~np.ma.getmaskarray(f)
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        lat_min, lat_max = lat[rows.min()], lat[rows.max()]
        lon_min, lon_max = lon[cols.min()], lon[cols.max()]
        return [
            max(lon_min - pad, -180),
            min(lon_max + pad, 180),
            max(lat_min - pad, -90),
            min(lat_max + pad, 90),
        ]


def main(config_filename=None):
    # Read in the YAML configuration file.  Environment variables in
    # the configuration file are supported.
    settings = util.get_params(config_filename)

    mfp = ModeFieldPlot(settings)
    if mfp.config_obj.field_to_plot == "raw":
        mfp.plot_mode_raw()
    else:
        mfp.plot_mode_objects()


if __name__ == "__main__":
    main()
