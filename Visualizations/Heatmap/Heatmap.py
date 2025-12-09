"""
Hourly Heatmap Visualizations
=============================

This module implements the ``htmp`` class, which generates two coordinated
heatmaps with Bokeh:

1. **Main Heatmap**  
   Displays hourly values (e.g., temperature, RH, CO₂) for all days in a year.  

2. **Thermal Comfort / Anomaly Map**  
   Highlights hours inside or outside an admissible comfort range.

The figure also includes:
- A colorbar with tick formatting
- A sidebar with occurrence percentages for each color range
- A second bar chart showing % of hours inside/outside the comfort range
- Linked brushing between heatmaps

The class is general and can be reused for any hourly environmental dataset
with columns: ``Date``, ``Hour``, ``Value``.

Designed for the BEPVis project.

Author: Ofelia Vera-Piazzini, Massimiliano Scarpa (Università Iuav di Venezia)
License: MIT
"""

import pandas as pd
import numpy as np
import math
from bokeh.plotting import figure, show, output_file, figure
from bokeh.transform import linear_cmap, factor_cmap
from bokeh.models import CustomJSTickFormatter, FixedTicker, Range1d, BoxSelectTool, PrintfTickFormatter, LinearColorMapper, CustomJSTickFormatter, HoverTool, ColorBar, FixedTicker, ColumnDataSource, LabelSet, SaveTool, ResetTool, WheelZoomTool, PanTool, BoxZoomTool, BoxSelectTool
from bokeh.layouts import column, gridplot
from bokeh.palettes import Turbo256

# ======================
# CLASS DEFINITION
# ======================
class htmp:
    """
    Generate an hourly environmental heatmap and anomaly map.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain the columns: ``['Date', 'Hour', 'Value']``  
        - ``Date`` : string or datetime  
        - ``Hour`` : 0–23  
        - ``Value``: environmental variable to visualize
    source_file_pathandname : str
        Name of the source dataset (optional label).
    zone_name : str
        Name of the room or zone.
    parameter_title : str
        Label of the environmental variable (e.g. "Temperature").
    parameter_unit : str
        Unit of the variable (e.g. "°C", "%").
    ns_color : int
        Number of colors in the palette (12 recommended).
    s_limit : list
        [min_value, max_value] for the main heatmap color scale.  
        If values are strings, limits are computed automatically.
    s_limit_best : list
        [min_value, max_value] of admissible or comfort range.
    filesave_name : str
        Output filename (HTML).

    Notes
    -----
    - Two heatmaps are generated:
        * full-range value heatmap
        * anomaly heatmap based on comfort limits
    - Colorbars and occurrence plots are automatically created.
    """

    def __init__(self, df = '?', source_file_pathandname = '?', zone_name = '?', parameter_title = '?', parameter_unit = '?', ns_color = '?', s_limit = ['?', '?'], s_limit_best = ['?', '?'], filesave_name = '?'):
        # --------------------------------------------------------------
        # 1. PREPARE AND VALIDATE INPUT DATA
        # --------------------------------------------------------------

        # Extract value list for limit auto-detection
        values = df['Value'].tolist()
        
        # Compute limits if user left "?"
        for n in range(2):
            if isinstance(s_limit[n], str):
                if n == 0:
                    s_limit[n] = np.nanmin(values)
                else:
                    s_limit[n] = np.nanmax(values)
            if isinstance(s_limit_best[n], str):
                if n == 0:
                    s_limit_best[n] = np.nanmin(values)
                else:
                    s_limit_best[n] = np.nanmax(values)

        # Create a grid: [hours x days], with values
        hours = df['Hour']
        dates = pd.to_datetime(df['Date'])
        values = df['Value']

        # Calculate the day number of the year for each date
        day_of_year = dates.dt.dayofyear

        # Create a list of unique hours, days, and months
        unique_hours = sorted(df['Hour'].unique())
        unique_days = sorted(day_of_year.unique())

        # --------------------------------------------------------------
        # 2. GRID CONSTRUCTION FOR HEATMAP
        # --------------------------------------------------------------

        # Create a grid of values for each hour and day
        values_grid = np.empty((len(unique_hours), len(unique_days)))

        # Loop over unique hours
        for i, hour in enumerate(unique_hours):
            # Loop over unique days
            for j, day in enumerate(unique_days):
                # Extract value for the current hour and day
                value = df[(df['Hour'] == hour) & (day_of_year == day)]['Value']
                
                # Check if value data exists
                if len(value) > 0:
                    # Assign the first value to the corresponding grid cell
                    values_grid[i, j] = value.values[0]

        # --------------------------------------------------------------
        # 3. COLOR PALETTE
        # --------------------------------------------------------------

        # Define the color palette
        colors = [Turbo256[n] for n in range(0,len(Turbo256),max(1,int(256/ns_color)))][:ns_color]
        custom_colors = ["#733B9E", "#18447C", "#4980B9", "#86B1E4", "#BED7EC", "#E0F3F8", "#FFEE12", "#FFB901", "#FF9643", "#ED6F08", "#EA0112", "#A50026"]

        if ns_color == 12:
            colors = custom_colors
        else:
            colors = colors
        
        # Define axis ranges
        x_range = Range1d(0, 365) # Adjust x_range to accommodate all 365 days
        y_range = Range1d(0, len(unique_hours) - 1) #23 hours

        # =====================================================================
        # MAIN HEATMAP
        # =====================================================================

        # Define month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Create HoverTool instance with tooltips
        hover_tool = HoverTool(
            tooltips=[("Day", "@x{0}"), ("Hour", "@y{0}"), (parameter_title, "@image{0.0}" + parameter_unit)])

        # Create the figure
        p = figure(title='Hourly ' + parameter_title + ' - ' + zone_name,
                x_range=x_range,  
                y_range=y_range,
                x_axis_location="below",
                x_axis_label="Days",
                y_axis_label="Hours",
                width=800,
                height=300,
                tools=["save", "pan", "box_zoom", "reset", "wheel_zoom"])

        # Add hover tool to the first figure
        p.add_tools(hover_tool)

        # Create the main ticks for the firat day of each month
        minor_tick = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] # Days in each month
        main_ticks = np.cumsum([1] + minor_tick[:-1])  # Start of each month (e.g., 1, 32, 60...)

        # Create intermediate ticks (3 weeks within each month)
        week_ticks = []
        for i, days in enumerate(minor_tick):
            start_of_month = main_ticks[i]
            weeks_in_month = np.linspace(start_of_month, start_of_month + days, num=4, endpoint=False)[1:]
            week_ticks.extend(weeks_in_month)


        # Configure the main ticker
        p.xaxis.ticker = FixedTicker(ticks=main_ticks)

        # Combine main and intermediate ticks
        all_ticks = sorted(list(main_ticks) + list(week_ticks))
        p.xaxis.ticker = FixedTicker(ticks=all_ticks)

        # Customize the tick format
        p.xaxis.formatter = CustomJSTickFormatter(code="""
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];
            
            for (let i = 0; i < month_starts.length; i++) {
                if (Math.abs(tick - month_starts[i]) < 1) {
                    return months[i];
                }
            }
            return '';
        """)

        
        p.grid.grid_line_color = None
        p.axis.axis_line_color = None
        
        # Configuration of minor ticks
        p.xaxis.minor_tick_line_color = 'Black'
        p.xaxis.minor_tick_line_width = 0.5
        p.xaxis.minor_tick_in = -3
        p.xaxis.minor_tick_out = 0
        
        # Configuration of major ticks
        p.grid.grid_line_color = None
        p.axis.axis_line_color = None
        p.axis.major_tick_line_color = 'Black'
        p.axis.major_label_text_font_size = "9px"
        p.axis.major_label_standoff = 0
        p.xaxis.major_label_orientation = "horizontal"

        # Create color mapper
        mapper = linear_cmap(field_name='image', palette = colors, low=s_limit[0], high=s_limit[1])

        # Create the heatmap
        p.rect(x="x", y="y", width=1, height=1, source={'x': day_of_year.astype(str), 'y': hours, 'image': values},
            fill_color=mapper, line_color=None)

        # Create the ticker locations
        ticker_locs = np.linspace(s_limit[0], s_limit[1], num=len(colors))

        # --------------------------------------------------------------
        # COLORBAR
        # --------------------------------------------------------------

        # Create color bar with fixed ticker locations
        ns_digit = 10
        ns_digit = int(math.floor(math.log10(abs((s_limit[1] - s_limit[0]) / ns_color)))) + 1
        ticker_locs = [round(value, ns_digit) for value in ticker_locs]
        color_bar = ColorBar(color_mapper=mapper['transform'],
                            location=(0, 0), 
                            title= parameter_title + '[' + parameter_unit + ']',
                            ticker=FixedTicker(ticks=ticker_locs),
                            formatter=PrintfTickFormatter(format="%f"),
                            major_tick_line_color = None,
                            label_standoff=6, 
                            border_line_color=None, 
                            padding=4,
                            title_standoff=10)

        # Set the font size of the tick labels
        color_bar.major_label_text_font_size = "7pt"

        p.add_layout(color_bar, 'right')

        # --------------------------------------------------------------
        # OCCURRENCE PERCENTAGE BAR (main heatmap)
        # --------------------------------------------------------------

        # Create occurrence percentages for each value range
        occurrences = {}
        for i in range(len(colors)):
            lower_bound = s_limit[0] + i * (s_limit[1] - s_limit[0]) / len(colors)
            upper_bound = s_limit[0] + (i + 1) * (s_limit[1] - s_limit[0]) / len(colors)
            occurrences[f"{lower_bound:.1f}-{upper_bound:.1f}"] = np.sum((values_grid >= lower_bound) & (values_grid < upper_bound)) / np.sum(~np.isnan(values_grid)) * 100

        # Create a horizontal bar plot next to the legend
        source = ColumnDataSource(data=dict(value_range=list(occurrences.keys()), occurrences=list(occurrences.values())))
        bar_plot = figure(y_range=list(occurrences.keys()),
                        x_range=(0,100),
                        title='Occurrences (%)',
                        width=150,
                        height=295,
                        tools='',
                        outline_line_color=None)

        # Add a horizontal bar renderer
        bar_plot.hbar(y= 'value_range', right='occurrences', height=1, line_color=None, source=source, 
                    fill_color=factor_cmap('value_range', palette=colors, factors=list(occurrences.keys())))

        # Round the percentage values to two decimals and add '%' symbol
        occurrences_formatted = [f"{value:.2f}%" for value in occurrences.values()]
        source.data['occurrences_formatted'] = occurrences_formatted

        # Add percentage values at the end of each bar
        labels = LabelSet(x='occurrences', y='value_range', text='occurrences_formatted',
                        x_offset=5, y_offset=-5, source=source, text_align='left',
                        text_font_size='7pt')

        bar_plot.add_layout(labels)

        # Remove grid lines and x-axis
        bar_plot.xgrid.visible = False
        bar_plot.ygrid.visible = False
        bar_plot.xaxis.visible = False
        bar_plot.yaxis.visible = False
        bar_plot.yaxis.major_tick_line_color = None
        bar_plot.yaxis.minor_tick_line_color = None

        # =====================================================================
        # SECOND HEATMAP — COMFORT RANGE / ANOMALY MAP
        # =====================================================================

        # Extract hour, date, and value columns
        hours_second_heatmap = df['Hour']
        dates_second_heatmap = pd.to_datetime(df['Date'])
        values_second_heatmap = df['Value']

        # Calculate the day number of the year for each date
        day_of_year_second_heatmap = dates.dt.dayofyear

        # Create a list of unique hours, days, and months
        unique_hours_second_heatmap = sorted(df['Hour'].unique())
        unique_days_second_heatmap = sorted(day_of_year_second_heatmap.unique())

        # Create a grid of values for each hour and day
        values_grid_second_heatmap = np.empty((len(unique_hours), len(unique_days_second_heatmap)))

        # Loop over unique hours
        for i, hour in enumerate(unique_hours_second_heatmap):
            # Loop over unique days
            for j, day in enumerate(unique_days_second_heatmap):
                # Extract value for the current hour and day
                value = df[(df['Hour'] == hour) & (day_of_year_second_heatmap == day)]['Value']
                
                # Check if value data exists
                if len(value) > 0:
                    # Assign the first value value to the corresponding grid cell
                    values_grid_second_heatmap[i, j] = value.values[0]

        # Define month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Create HoverTool instance with tooltips
        hover_tool_second = HoverTool(
            tooltips=[("Day", "@x{0}"), ("Hour", "@y{0}"), (parameter_title, "@image{0.0} °C")])

        p_second_row = figure(title='Hourly ' + parameter_title + ' - ' + zone_name + ' - Anomalies',
                x_range=x_range, 
                y_range=y_range,
                x_axis_location="below",
                x_axis_label="Days",
                y_axis_label="Hours",
                width=800,
                height=300,
                tools=["save", "pan", "box_zoom", "reset", "wheel_zoom"])

        # Add hover tool to the second figure
        p_second_row.add_tools(hover_tool_second)

        # Configure the main ticker
        p_second_row.xaxis.ticker = FixedTicker(ticks=main_ticks)

        # Combine main and intermediate ticks
        p_second_row.xaxis.ticker = FixedTicker(ticks=all_ticks)

        # Customize the tick format
        p_second_row.xaxis.formatter = CustomJSTickFormatter(code="""
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];
            
            for (let i = 0; i < month_starts.length; i++) {
                if (Math.abs(tick - month_starts[i]) < 1) {
                    return months[i];
                }
            }
            return '';
        """)

        p_second_row.grid.grid_line_color = None
        p_second_row.axis.axis_line_color = None
        p_second_row.xgrid.grid_line_color = '#FFFFFF'

        # Configuration of ticks
        p_second_row.axis.major_tick_line_color = 'Black'
        p_second_row.axis.major_label_text_font_size = "9px"
        p_second_row.axis.major_label_standoff = 0
        p_second_row.xaxis.major_label_orientation = "horizontal"

        p_second_row.xaxis.minor_tick_line_color = 'Black'
        p_second_row.xaxis.minor_tick_line_width = 0.5
        p_second_row.xaxis.minor_tick_in = -3
        p_second_row.xaxis.minor_tick_out = 0
        
        
        # Define custom green palette for "Thermal Comfort Range"
        green_palette = ["#F7F4ED"]

        # Create a color mapper for the "Thermal Comfort Range" category
        mapper_anomaly = LinearColorMapper(palette=green_palette, low=s_limit_best[0], high=s_limit_best[1],
                                low_color='#737373', high_color='#737373')

        # Use the custom color mapper in your plotting code
        p_second_row.rect(x="x", y="y", width=1, height=1, source={'x': day_of_year_second_heatmap.astype(str), 'y': hours_second_heatmap, 'image': values_second_heatmap},
                        fill_color={'field': 'image', 'transform': mapper_anomaly}, line_color=None)

        # Add color bar
        ticker_locs_second_sheet = np.linspace(np.nanmin(values_grid_second_heatmap), np.nanmax(values_grid_second_heatmap), num=len(colors))
        
        # Define the desired ticks for the color bar
        color_bar_ticks = np.linspace(s_limit_best[0], s_limit_best[1], num = len(colors))

        # Specify the desired tick locations
        custom_ticks = [s_limit_best[0], (s_limit_best[0] + s_limit_best[1]) / 2, s_limit_best[1]]

        # ----------------------
        # COLOR BAND LEGEND
        # ----------------------

        # Add color bar for the "Thermal Comfort Range"
        color_bar_thermal = ColorBar(color_mapper=mapper_anomaly, 
                                        location=(0, 0), 
                                        title='Admitted range',
                                        ticker=FixedTicker(ticks=custom_ticks),
                                        formatter=PrintfTickFormatter(format="%d"),
                                        label_standoff=6, 
                                        border_line_color=None, 
                                        padding=4,
                                        title_standoff=10)
                                        
        # Set the font size of the tick labels
        color_bar_thermal.major_label_text_font_size = "7pt"

        # Add the "Thermal Comfort Range" color bar to the plot
        p_second_row.add_layout(color_bar_thermal, 'right')

        # ------------------------------------------------------------------
        # OCCURRENCE SUMMARY BAR — COMFORT VS OUT-OF-RANGE
        # ------------------------------------------------------------------

        # Calculate percentage of hours in comfort range for each day
        total_occurrences = np.sum(~np.isnan(values_grid_second_heatmap))
        percentage_f7f4ed = np.sum((values_grid_second_heatmap >= s_limit_best[0]) & (values_grid_second_heatmap <= s_limit_best[1])) / total_occurrences * 100
        percentage_737373 = np.sum((values_grid_second_heatmap < s_limit_best[0]) | (values_grid_second_heatmap > s_limit_best[1])) / total_occurrences * 100

        # Create the vertical stacked bar chart figure
        stacked_bar_chart = figure(y_range=(0, 100),
                                height=300,
                                width=105,
                                title='Occurrences',
                                toolbar_location=None,
                                tools="hover",
                                tooltips=[("Category", "@category"), ("Percentage", "@percentage{0.2f}%")])

        # Adjust the width of the bars to make them more visible
        bar_width = 0.5  # Adjust the width as needed
        bar_offset = 0.1  # Offset to center the bars on the x-axis

        # Define category names
        categories = ['Thermal Comfort', 'Out of Range']

        # Define percentages
        percentages = [percentage_f7f4ed, percentage_737373]

        # Add the first stacked bar (color #F7F4ED)
        stacked_bar_chart.vbar(x=0, top=percentage_f7f4ed, width=bar_width, color='#F7F4ED', source=dict(category=[categories[0]], percentage=[percentages[0]]))

        # Add the second stacked bar (color #737373)
        stacked_bar_chart.vbar(x=0, bottom=percentage_f7f4ed, top=100, width=bar_width, color='#737373', source=dict(category=[categories[1]], percentage=[percentages[1]]))

        # Set the x-axis ticker
        stacked_bar_chart.xaxis.ticker = [0]
        stacked_bar_chart.xaxis.major_label_overrides = {0: '(%)'}

        # --------------------------------------------------------------
        # LINKED BRUSHING (ACROSS BOTH HEATMAPS)
        # --------------------------------------------------------------

        # Change the size of the y-axis text
        stacked_bar_chart.yaxis.major_label_text_font_size = "9px"

        # Add linked tools to both heatmaps
        p.tools = [hover_tool, SaveTool(), ResetTool(), WheelZoomTool(), PanTool(), BoxZoomTool()]
        p_second_row.tools = [hover_tool_second,SaveTool(), ResetTool(), WheelZoomTool(), PanTool(), BoxZoomTool()]

        # Add linked brushing to both heatmaps
        p_second_row.add_tools(BoxSelectTool(dimensions="width"))
        p.add_tools(BoxSelectTool(dimensions="width"))

        # --------------------------------------------------------------
        # FINAL LAYOUT AND OUTPUT
        # --------------------------------------------------------------

        layout = gridplot([[p, bar_plot], [p_second_row, stacked_bar_chart]])
        output_file(filesave_name + ".html")
        show(layout)