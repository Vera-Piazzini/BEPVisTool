"""
Scatter Plot Visualization (Heating & Cooling vs Outdoor Temperature)
====================================================================

This module implements the ``scttr_plt`` class for generating two scatter
plots: one for heating loads, one for cooling loads, both plotted against
outdoor temperature.

Each plot shows:
    - hourly values of Heating or Cooling Rate (W/m²)
    - points grouped by time-of-day ranges (0–8, 8–19, 19–24)
    - a global regression line
    - individual regression lines per time range
    - hover information
    - legends with interactive visibility

The two plots are displayed side by side using Bokeh's ``gridplot``.

Dataset Requirements
--------------------
The Excel file must contain the following columns:

    - Outdoor_Temperature
    - Zone_ILAS_HeatingRate
    - Zone_ILAS_CoolingRate
    - Date/Time (string "YYYY/MM/DD HH:MM")

Authors: Ofelia Vera-Piazzini, Massimiliano Scarpa (Università Iuav di Venezia)  
License: MIT
"""
import os
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.io import output_file
import numpy as np
from scipy.stats import linregress
from bokeh.palettes import viridis
import itertools
from bokeh.layouts import gridplot
from bokeh.models import HoverTool, Legend, Range1d
import math

# ============================================================================
# SCATTER PLOT CLASS
# ============================================================================
class scttr_plt:
    """
    Create scatter plots of Heating/Cooling vs Outdoor Temperature.

    Parameters
    ----------
    source_file_pathandname : str
        Path to the Excel file containing the required columns.
    zone_name : str
        Name of the zone for use in the plot title.
    value_max_heating : float
        Maximum expected heating rate, used to scale the Y axis.
    value_max_cooling : float
        Maximum expected cooling rate, used to scale the Y axis.
    filesave_name : str
        Base name of the output HTML file.

    Generates
    ---------
    An HTML file with two Bokeh scatter plots:
        - Heating vs Outdoor Temperature
        - Cooling vs Outdoor Temperature
    """
    def __init__(self, source_file_pathandname = '?', zone_name = '?', value_max_heating = '?', value_max_cooling = '?', filesave_name = '?'):
        
        # --------------------------------------------------------------
        # LOAD DATA
        # --------------------------------------------------------------
        df = pd.read_excel(source_file_pathandname)

        # Determine the maximum value among heating and cooling rates for y-axis scaling
        s_y = df['Zone_ILAS_HeatingRate'].tolist()
        s_y.extend(df['Zone_ILAS_CoolingRate'].tolist())
        y_max = math.ceil(max(value_max_heating, value_max_cooling)/50)*50

        # Extract outdoor temperature and heating rate columns
        x = df['Outdoor_Temperature']
        y = df['Zone_ILAS_HeatingRate']

        # Extract the hour from the 'Date/Time' column for time-of-day filtering
        df['Hour'] = df['Date/Time'].str.split().str[-1].str.split(':').str[0].astype(int)

        # --------------------------------------------------------------
        # HEATING RATE PLOT
        # --------------------------------------------------------------
        
        # Create the heating rate scatter plot
        p_h = figure(title="Total Heating Rate (W/m2) vs Outdoor Temperature (°C) - " + zone_name, tools="crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,examine,help")

        # Define colors palette for different time-of-day ranges
        num_ranges = 3
        colors = itertools.cycle(viridis(num_ranges))

        # Containers for storing glyphs (optional for extensions)
        scatter_items = []
        trend_lines = []

        # Add the overall (general) trend line for heating
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        general_trend_x = np.array([min(x), max(x)])
        general_trend_y = intercept + slope * general_trend_x
        general_trend_line = p_h.line(general_trend_x, general_trend_y, line_width=2, line_color="black", legend_label="General Trend Line")

        # Plot scatter points and trend lines by time-of-day intervals (0–8, 8–19, 19–24)
        for i, hour_range in enumerate([(0, 8), (8, 19), (19, 24)]):
            # Filter data by hour range
            x_range = x[(df['Hour'] >= hour_range[0]) & (df['Hour'] < hour_range[1])]
            y_range = y[(df['Hour'] >= hour_range[0]) & (df['Hour'] < hour_range[1])]
            
            # Scatter plot for the current time range
            color = next(colors)
            scatter_item = p_h.scatter(x_range, y_range, radius=0.2, fill_color=color, fill_alpha=0.6, line_color=None, legend_label=f"Time: {hour_range[0]}-{hour_range[1]}")
            scatter_items.append(scatter_item)
            
            # Add linear regression trend line if enough data points
            if len(x_range) > 1:
                slope, intercept, r_value, p_value, std_err = linregress(x_range, y_range)
                trend_x = np.array([min(x_range), max(x_range)])
                trend_y = intercept + slope * trend_x
                
                trend_line = p_h.line(trend_x, trend_y, line_width=2, line_color=color, legend_label=f"Time: {hour_range[0]}-{hour_range[1]} - Trend Line", visible=False)
                trend_lines.append(trend_line)

        # Axis labeling for heating plot
        p_h.xaxis.axis_label = 'Hourly Outdoor Temperature [°C]'
        p_h.yaxis.axis_label = 'Hourly Total Heating Rate [W/m2]'
        p_h.y_range.start = 0
        p_h.y_range.end =  y_max

        # Customize legend behavior for heating plot
        legend = p_h.legend
        p_h.legend.title = "Hour Range"
        p_h.legend.location = "top_right"
        p_h.legend.click_policy = "hide"
        legend.label_text_font_size = "9pt"
        legend.spacing = 1

        # Add hover tool for heating plot
        hover = HoverTool(tooltips=[("Outdoor Temperature", "@x{0.0} °C"), ("Heating Rate", "@y{0} W/m2")])
        p_h.add_tools(hover)

        # --------------------------------------------------------------
        # COOLING RATE PLOT (same logic)
        # --------------------------------------------------------------
        
        # Repeat the process for the cooling rate plot
        x = df['Outdoor_Temperature']
        y = df['Zone_ILAS_CoolingRate']
        
        # Create the cooling rate scatter plot
        p_c = figure(title="Total Cooling Rate (W/m2) vs Outdoor Temperature (°C) - " + zone_name, tools="crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,examine,help")

        # Define color palette for different time-of-day ranges
        num_ranges = 3
        colors = itertools.cycle(viridis(num_ranges))

        # Containers for storing glyphs (optional for extensions)
        scatter_items = []
        trend_lines = []

        # Add the overall (general) trend line for cooling
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        general_trend_x = np.array([min(x), max(x)])
        general_trend_y = intercept + slope * general_trend_x
        general_trend_line = p_c.line(general_trend_x, general_trend_y, line_width=2, line_color="black", legend_label="General Trend Line")

        # Plot scatter points and trend lines by time-of-day intervals (0–8, 8–19, 19–24)
        for i, hour_range in enumerate([(0, 8), (8, 19), (19, 24)]):
            # Filter data by hour range
            x_range = x[(df['Hour'] >= hour_range[0]) & (df['Hour'] < hour_range[1])]
            y_range = y[(df['Hour'] >= hour_range[0]) & (df['Hour'] < hour_range[1])]
            
            # Scatter plot for the current time range
            color = next(colors)
            scatter_item = p_c.scatter(x_range, y_range, radius=0.2, fill_color=color, fill_alpha=0.6, line_color=None, legend_label=f"Time: {hour_range[0]}-{hour_range[1]}")
            scatter_items.append(scatter_item)
            
            # Add linear regression trend line if enough data points
            if len(x_range) > 1:
                slope, intercept, r_value, p_value, std_err = linregress(x_range, y_range)
                trend_x = np.array([min(x_range), max(x_range)])
                trend_y = intercept + slope * trend_x
                
                trend_line = p_c.line(trend_x, trend_y, line_width=2, line_color=color, legend_label=f"Time: {hour_range[0]}-{hour_range[1]} - Trend Line", visible=False)
                trend_lines.append(trend_line)

        # Axis labeling for cooling plot
        p_c.xaxis.axis_label = 'Hourly Outdoor Temperature [°C]'
        p_c.yaxis.axis_label = 'Hourly Total Cooling Rate [W/m2]'
        p_c.y_range.start = 0
        p_c.y_range.end =  y_max

        # Customize legend behavior for cooling plot
        legend = p_c.legend
        p_c.legend.title = "Hour Range"
        p_c.legend.location = "top_right"
        p_c.legend.click_policy = "hide"
        legend.label_text_font_size = "9pt"
        legend.spacing = 1

        # Add hover tool for cooling plot
        hover = HoverTool(tooltips=[("Outdoor Temperature", "@x{0.0} °C"), ("Cooling Rate", "@y{0} W/m2")])
        p_c.add_tools(hover)

        # --------------------------------------------------------------
        # LAYOUT & OUTPUT
        # --------------------------------------------------------------

        layout = gridplot([[p_h, p_c]])
        output_file(filesave_name + ".html")
        show(layout)


