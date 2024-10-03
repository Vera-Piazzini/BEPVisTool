"""

**Visualization of Hourly Temperature Data Across Two Different Sheets**

This script reads temperature data from two sheets in an Excel file, processes it, and visualizes it using Bokeh. 
The resulting grid plot consists of four plots: two heatmaps representing hourly temperature variations for each space, 
and two bar charts summarizing the occurrences of temperature ranges.

The first heatmap shows the hourly temperature for Space 1, while the second heatmap highlights thermal comfort anomalies.
Two accompanying bar charts display the occurrence percentages of temperature ranges and thermal comfort ranges, respectively.

Modules:
    - pandas: For data manipulation and analysis.
    - numpy: For numerical operations and array handling.
    - bokeh.plotting: For creating interactive plots with Bokeh.
    - bokeh.transform: For mapping data values to visual attributes.
    - bokeh.models: For various interactive Bokeh components like tools, color mappers, and axes formatting.
    - bokeh.layouts: For arranging plots in a grid layout.

Functions:
    - **load_data(file_path: str) -> tuple:** Loads data from the specified Excel file and returns two DataFrames for the two sheets.
    - **prepare_heatmap_data(df: pd.DataFrame) -> tuple:** Prepares the data for the heatmaps by organizing it into grid format.
    - **create_heatmap(p: figure, temperatures_grid: np.ndarray, colors: list) -> figure:** Creates a Bokeh heatmap plot with the provided temperature data.
    - **create_bar_chart(occurrences: dict, colors: list) -> figure:** Creates a Bokeh horizontal bar chart displaying the occurrence percentages of temperature ranges.
    - **prepare_thermal_comfort_data(df: pd.DataFrame) -> tuple:** Prepares the data for the thermal comfort heatmap and stacked bar chart.
    - **create_thermal_comfort_heatmap(p: figure, temperatures_grid: np.ndarray, colors: list) -> figure:** Creates a Bokeh heatmap plot for thermal comfort anomalies.
    - **create_stacked_bar_chart(percentages: list) -> figure:** Creates a Bokeh stacked bar chart displaying the occurrence percentages of thermal comfort ranges.
    - **show_plots(heatmap1: figure, bar_chart1: figure, heatmap2: figure, bar_chart2: figure) -> None:** Displays the final Bokeh plots in a grid layout.

"""

import pandas as pd
import numpy as np
from bokeh.plotting import figure, show
from bokeh.transform import linear_cmap, factor_cmap
from bokeh.models import (PrintfTickFormatter, ColorBar, FixedTicker, ColumnDataSource, HoverTool, LabelSet, BoxSelectTool,
                         BoxZoomTool, PanTool, ResetTool, SaveTool, WheelZoomTool, CustomJSTickFormatter, 
                         LinearColorMapper, Legend, LegendItem, Span, BoxAnnotation)
from bokeh.layouts import gridplot


def load_data(file_path: str) -> tuple:
    """Loads data from the specified Excel file.

    Args:
        file_path (str): Path to the Excel file containing the data.

    Returns:
        tuple: Two DataFrames, one for each sheet in the Excel file.
    """
    df1 = pd.read_excel(file_path, sheet_name='Sheet1')
    df2 = pd.read_excel(file_path, sheet_name='Sheet2')
    return df1, df2


def prepare_heatmap_data(df: pd.DataFrame) -> tuple:
    """Prepares the data for the heatmaps by organizing it into grid format.

    Args:
        df (pd.DataFrame): DataFrame containing the temperature data.

    Returns:
        tuple: Two arrays for temperatures and coordinates.
    """
    hours = df['Hour']
    dates = pd.to_datetime(df['Date'])
    temperatures = df['Temp']

    day_of_year = dates.dt.dayofyear
    unique_hours = sorted(df['Hour'].unique())
    unique_days = sorted(day_of_year.unique())
    
    temperatures_grid = np.empty((len(unique_hours), len(unique_days)))
    for i, hour in enumerate(unique_hours):
        for j, day in enumerate(unique_days):
            temperature = df[(df['Hour'] == hour) & (day_of_year == day)]['Temp']
            temperatures_grid[i, j] = temperature.values[0] if len(temperature) > 0 else np.nan
    
    return temperatures_grid, unique_hours, unique_days


def create_heatmap(p: figure, temperatures_grid: np.ndarray, colors: list) -> figure:
    """Creates a Bokeh heatmap plot with the provided temperature data.

    Args:
        p (figure): Bokeh figure to add the heatmap to.
        temperatures_grid (np.ndarray): 2D array of temperature values.
        colors (list): Color palette for the heatmap.

    Returns:
        figure: Bokeh figure with the heatmap.
    """
    mapper = linear_cmap(field_name='image', palette=colors, low=np.nanmin(temperatures_grid), high=np.nanmax(temperatures_grid))
    
    p.rect(x="x", y="y", width=1, height=1, source={'x': np.repeat(range(365), 24), 'y': np.tile(range(24), 365), 'image': temperatures_grid.flatten()},
           fill_color=mapper, line_color=None)
    
    color_bar = ColorBar(color_mapper=mapper['transform'], location=(0, 0), title='Temperature (°C)', 
                         ticker=FixedTicker(ticks=np.linspace(np.nanmin(temperatures_grid), np.nanmax(temperatures_grid), num=len(colors))),
                         formatter=PrintfTickFormatter(format="%d"))
    
    p.add_layout(color_bar, 'right')
    return p


def create_bar_chart(occurrences: dict, colors: list) -> figure:
    """Creates a Bokeh horizontal bar chart displaying the occurrence percentages of temperature ranges.

    Args:
        occurrences (dict): Dictionary of temperature ranges and their occurrence percentages.
        colors (list): Color palette for the bar chart.

    Returns:
        figure: Bokeh figure with the bar chart.
    """
    source = ColumnDataSource(data=dict(temperature_range=list(occurrences.keys()), occurrences=list(occurrences.values())))
    
    bar_plot = figure(y_range=list(occurrences.keys()), x_range=(0, 48), title='Occurrences (%)', width=150, height=295)
    bar_plot.hbar(y='temperature_range', right='occurrences', height=1, line_color=None,
                  fill_color=factor_cmap('temperature_range', palette=colors, factors=list(occurrences.keys())))
    
    occurrences_formatted = [f"{value:.2f}%" for value in occurrences.values()]
    source.data['occurrences_formatted'] = occurrences_formatted
    
    labels = LabelSet(x='occurrences', y='temperature_range', text='occurrences_formatted',
                      x_offset=5, y_offset=-5, source=source, text_align='left', text_font_size='7pt')
    
    bar_plot.add_layout(labels)
    bar_plot.xgrid.visible = False
    bar_plot.ygrid.visible = False
    bar_plot.xaxis.visible = False
    bar_plot.yaxis.visible = False
    return bar_plot


def prepare_thermal_comfort_data(df: pd.DataFrame) -> tuple:
    """Prepares the data for the thermal comfort heatmap and stacked bar chart.

    Args:
        df (pd.DataFrame): DataFrame containing the temperature data.

    Returns:
        tuple: Data arrays and occurrences for thermal comfort analysis.
    """
    hours = df['Hour']
    dates = pd.to_datetime(df['Date'])
    temperatures = df['Temp']

    day_of_year = dates.dt.dayofyear
    unique_hours = sorted(df['Hour'].unique())
    unique_days = sorted(day_of_year.unique())
    
    temperatures_grid = np.empty((len(unique_hours), len(unique_days)))
    for i, hour in enumerate(unique_hours):
        for j, day in enumerate(unique_days):
            temperature = df[(df['Hour'] == hour) & (day_of_year == day)]['Temp']
            temperatures_grid[i, j] = temperature.values[0] if len(temperature) > 0 else np.nan
    
    total_occurrences = np.sum(~np.isnan(temperatures_grid))
    percentage_comfort = np.sum((temperatures_grid >= 15.0) & (temperatures_grid <= 25.1)) / total_occurrences * 100
    percentage_out_of_range = np.sum((temperatures_grid < 15.0) | (temperatures_grid > 25.1)) / total_occurrences * 100
    
    return temperatures_grid, percentage_comfort, percentage_out_of_range


def create_thermal_comfort_heatmap(p: figure, temperatures_grid: np.ndarray, colors: list) -> figure:
    """Creates a Bokeh heatmap plot for thermal comfort anomalies.

    Args:
        p (figure): Bokeh figure to add the heatmap to.
        temperatures_grid (np.ndarray): 2D array of temperature values.
        colors (list): Color palette for the heatmap.

    Returns:
        figure: Bokeh figure with the thermal comfort heatmap.
    """
    mapper_anomaly = LinearColorMapper(palette=colors, low=15.0, high=25.0)
    
    p.rect(x="x", y="y", width=1, height=1, source={'x': np.repeat(range(365), 24), 'y': np.tile(range(24), 365), 'image': temperatures_grid.flatten()},
           fill_color={'field': 'image', 'transform': mapper_anomaly}, line_color=None)
    
    color_bar_thermal = ColorBar(color_mapper=mapper_anomaly, location=(0, 0), title='Thermal Comfort Range (15-25°C)', 
                                ticker=FixedTicker(ticks=[15, 20, 25]), formatter=PrintfTickFormatter(format="%d"))
    
    p.add_layout(color_bar_thermal, 'right')
    return p


def create_stacked_bar_chart(percentages: list) -> figure:
    """Creates a Bokeh stacked bar chart displaying the occurrence percentages of thermal comfort ranges.

    Args:
        percentages (list): List of percentages for thermal comfort ranges.

    Returns:
        figure: Bokeh figure with the stacked bar chart.
    """
    categories = ['Comfort (15-25°C)', 'Out of Comfort Range']
    source = ColumnDataSource(data=dict(category=categories, percentages=percentages))
    
    bar_chart = figure(x_range=categories, y_range=(0, 100), title='Thermal Comfort Occurrence (%)', width=300, height=250)
    bar_chart.vbar(x='category', top='percentages', width=0.5, source=source,
                   color=factor_cmap('category', palette=['#F2DADA', '#F8FAF3'], factors=categories))
    
    bar_chart.yaxis.axis_label = 'Percentage (%)'
    bar_chart.xgrid.grid_line_color = None
    bar_chart.axis.minor_tick_line_color = None
    bar_chart.outline_line_color = None
    return bar_chart


def show_plots(heatmap1: figure, bar_chart1: figure, heatmap2: figure, bar_chart2: figure) -> None:
    """Displays the final Bokeh plots in a grid layout.

    Args:
        heatmap1 (figure): Bokeh figure with the first heatmap.
        bar_chart1 (figure): Bokeh figure with the first bar chart.
        heatmap2 (figure): Bokeh figure with the second heatmap.
        bar_chart2 (figure): Bokeh figure with the second bar chart.
    """
    grid = gridplot([[heatmap1, bar_chart1], [heatmap2, bar_chart2]])
    show(grid)