"""
GainsAndLosses Visualizations
=============================

This module contains two visualization classes used in the BEPVis project:

- ``GainsAndLosses_Spaces``:
    Creates stacked bar charts (annual + monthly) showing heat gains and losses
    for a single zone or for the entire building.

- ``GainsAndLosses_Parameters``:
    Aggregates gains/losses by parameter (solar, lights, equipment, infiltration…)
    and generates compact bar charts comparing all building zones.

These modules are automatically called by ``BEPVis_Manager``, but they can also
be used independently if the input DataFrame format is respected.

Output
------
Each visualization produces:
- An interactive HTML file (Bokeh)
- Optionally PNG export (if configured)

Author: Ofelia Vera-Piazzini, Massimiliano Scarpa (Università Iuav di Venezia)
License: MIT
"""

import pandas as pd
from bokeh.models import ColumnDataSource, Title, Legend, NumeralTickFormatter, Span
from bokeh.palettes import RdYlBu11, Turbo256
from bokeh.plotting import figure, show
from bokeh.layouts import row, column
from bokeh.io import output_file
import math

# ======================================================================
# CLASS 1 — GAINS AND LOSSES PER SPACE (Annual + Monthly Stacked Charts)
# ======================================================================

class GainsAndLosses_Spaces:
    """
    Generate bar charts showing monthly and annual heat gains and losses
    for a given space (or aggregated building level).

    Parameters
    ----------
    df_gains : pandas.DataFrame
        Monthly gains for each type. Columns follow:
        ['Month', '*Zone* - Solar', '*Zone* - Lights', ...].
    df_losses : pandas.DataFrame
        Monthly losses (same format as gains, but values negative).
    gains_max_month : float
        Max monthly total gains found across all zones (for plotting scale).
    gains_max_year : float
        Max annual gains found across all zones (for plotting scale).
    losses_min_month : float
        Min monthly total losses (negative values).
    losses_min_year : float
        Min annual losses (negative values).
    filesave_name : str
        Output filename (without extension).

    Notes
    -----
    - Values are assumed already normalized per floor area (kWh/m²).
    - This visualization produces an HTML file with two stacked charts:
        * Annual energy balance
        * Monthly energy balance
    """

    def __init__(self, df_gains = '?', df_losses = '?', gains_max_month =  '?', 
                 gains_max_year = '?', losses_min_month = '?', losses_min_year = '?', 
                 filesave_name = '?'):
        
        # Remove unwanted excel columns (e.g. "Unnamed:…")
        df_gains = df_gains.drop(df_gains.columns[df_gains.columns.str.contains('Unnamed')], axis = 1)
        df_losses = df_losses.drop(df_losses.columns[df_losses.columns.str.contains('Unnamed')], axis = 1)

        # Extract axes labels and energy component names
        months = df_gains['Month'].tolist()
        types_gains = df_gains.columns[1:].tolist() 
        types_losses = df_losses.columns[1:].tolist()

        # Total annual values for the stacked annual chart
        annual_gains = [sum(df_gains[type]) for type in types_gains]
        annual_losses = [sum(df_losses[type]) for type in types_losses]

        # Axis scaling (rounded to nice values)
        y_limit_max_annual = math.ceil(gains_max_year/50)*50
        y_limit_min_annual = math.floor(losses_min_year/50)*50
        
        y_limit_max_monthly = math.ceil(gains_max_month/10)*10
        y_limit_min_monthly = math.floor(losses_min_month/10)*10

        # Prepare ColumnDataSource for annual chart
        source_data_annual_gains = {
            'x': ['Annual'],
            **{type: [sum(df_gains[type])] for type in types_gains}
        }
        source_data_annual_losses = {
            'x': ['Annual'],
            **{type: [sum(df_losses[type])] for type in types_losses}
        }

        # Prepare ColumnDataSource for monthly chart
        source_data_monthly_gains = {
            'x': months,
            **{type: df_gains[type].tolist() for type in types_gains}
        }
        source_data_monthly_losses = {
            'x': months,
            **{type: df_losses[type].tolist() for type in types_losses}
        }

        # Color palettes (subsample Turbo256 for visual consistency)
        reverse_palette = [Turbo256[n] for n in range(0,len(Turbo256),10)]
        original_palette = reverse_palette[::-1]

        tooltips = [("Type", "$name"), ("Value", "@$name{0.00} kWh/m2")]

        # ----------------------
        # Annual Energy Balance
        # ----------------------
        
        p_annual_gains = figure(x_range=['Annual'], height=600, width=380, 
            title="Total Annual Energy Balance by Type",
            toolbar_location="left", tools="hover", tooltips=tooltips, 
            min_border=0,y_range=(y_limit_min_annual, y_limit_max_annual))

        hatch_patterns = [" ", ".", "o", "-", "|", "+", '"', ":", "@", "/", "\\", "x", ",", "`", "v", ">"]
        
        # Plot stacked bars for gains and losses on the same chart
        p_annual_gains.vbar_stack(types_gains,
                                  x='x',
                                  width=0.9,
                                  color=original_palette[:len(types_gains)][::-1],
                                  source=ColumnDataSource(data=source_data_annual_gains))

        p_annual_gains.vbar_stack(types_losses,
                                   x='x',
                                   width=0.9,
                                   color=reverse_palette[:len(types_losses)][::-1],
                                   source=ColumnDataSource(data=source_data_annual_losses))
        
        # Customize annual chart appearance
        p_annual_gains.xgrid.grid_line_color = None
        p_annual_gains.xaxis.visible = True
        p_annual_gains.axis.minor_tick_line_color = None
        p_annual_gains.outline_line_color = None
        p_annual_gains.xaxis.axis_label = None
        p_annual_gains.yaxis.axis_label = "Energy Balance (kWh/m2)"
        p_annual_gains.yaxis.major_label_orientation = "horizontal"
        p_annual_gains.yaxis.formatter = NumeralTickFormatter(format="0,0")
        
        #Adjust y-axis range for visual consistency between charts
        ratio_y_annual = y_limit_max_annual / (-y_limit_min_annual)
        ratio_y_monthly = y_limit_max_monthly / (-y_limit_min_monthly)
        y_limit_min_monthly = y_limit_min_monthly * ratio_y_monthly / ratio_y_annual
        
        # ----------------------
        # Monthly Energy Balance
        # ----------------------
       
        p_monthly_gains = figure(x_range=months, height = 600, width=700, y_range=(y_limit_min_monthly, y_limit_max_monthly), title="Building Energy Balance by Month and Type",
                toolbar_location="above", tools="hover", tooltips=tooltips)
        p_monthly_gains.vbar_stack(types_gains, x='x', width=0.9, color=original_palette[:len(types_gains)][::-1], source=ColumnDataSource(data=source_data_monthly_gains))
        p_monthly_gains.vbar_stack(types_losses, x='x', width=0.9, color=reverse_palette[:len(types_losses)][::-1], source=ColumnDataSource(data=source_data_monthly_losses))

        # Customize monthly chart appearance
        p_monthly_gains.x_range.range_padding = 0.1
        p_monthly_gains.xgrid.grid_line_color = None
        p_monthly_gains.axis.minor_tick_line_color = None
        p_monthly_gains.outline_line_color = None
        p_monthly_gains.xaxis.axis_label = "Months"
        p_monthly_gains.yaxis.axis_label = "Energy Balance (kWh/m2)"
        p_monthly_gains.yaxis.major_label_orientation = "horizontal"

        # ----------------------
        # Legend Configuration
        # ----------------------

        # Reorder gains (reversed) for consistent legend display
        ordered_types_gains = types_gains[::-1]
        ordered_types_losses = types_losses

        # Create the legend items with the adjusted order
        legend_items = []
        for t in ordered_types_gains:
            index = types_gains.index(t) 
            legend_items.append((t, [p_monthly_gains.renderers[index]]))  # Gains

        offset = len(types_gains)
        for t in ordered_types_losses:
            index = types_losses.index(t) 
            legend_items.append((t, [p_monthly_gains.renderers[offset + index]]))  # Losses

        legend = Legend(items=legend_items, location="center", glyph_height=20, glyph_width=20)
        legend.border_line_color = None

        # Add the legend
        p_monthly_gains.add_layout(legend, 'right')
        p_monthly_gains.legend.click_policy = "hide"

        # ----------------------
        # Span for Zero Line
        # ----------------------

        span1 = Span(location=0, dimension='width', line_color='black', line_width=2)
        p_annual_gains.add_layout(span1)
        p_monthly_gains.add_layout(span1)
        
        # ----------------------
        # Final Layout
        # ----------------------

        layout = row(p_annual_gains, p_monthly_gains)
        output_file(filesave_name + ".html")
        # Display the layout
        show(layout)

# =======================================================================
# CLASS 2 — GAINS AND LOSSES BY PARAMETER (Compact Zone Comparison Plots)
# =======================================================================
class GainsAndLosses_Parameters:
    """
    Create compact bar charts showing gains and losses by type and by zone.

    These charts aggregate annual gains/losses for each parameter
    (solar, equipment, conduction…) across all zones.

    Parameters
    ----------
    s_zone_name : list[str]
        List of zone names in display order.
    data_gains : pandas.DataFrame
        Annual gains per zone and per parameter.
    data_losses : pandas.DataFrame
        Annual losses per zone and per parameter.
    filesave_name : str
        Output HTML file name (without extension).
    """

    def __init__(self, s_zone_name = '?', data_gains = '?', data_losses = '?', filesave_name = '?'):
        self.s_zone_name = s_zone_name

        # -------------------------------------------------------
        # Extract gain and loss types from DataFrame column names
        # -------------------------------------------------------

        # Gain types appear as "*Zone* - Type"
        types_gains = data_gains.columns.tolist()[1:]
        for n in range(len(types_gains)):
            types_gains[n] = types_gains[n].split('* - ')[1]
        types_gains = list(dict.fromkeys(types_gains))
        ordered_types_gains = types_gains[::-1]

        # Build aggregated gain table per zone
        dict_gains = {'Space': self.s_zone_name}
        for type_gain in types_gains:
            dict_gains[type_gain] = [0] * len(self.s_zone_name)
        
        s_column = data_gains.columns.tolist()[1:]
        for column_name in s_column:
            zone_name = column_name.split('* - ')[0][1:]
            gain_name = column_name.split('* - ')[1]
            dict_gains[gain_name][self.s_zone_name.index(zone_name)] = abs(sum(data_gains[column_name]))

        # Losses
        types_losses = data_losses.columns.tolist()[1:]
        for n in range(len(types_losses)):
            types_losses[n] = types_losses[n].split('* - ')[1]
        types_losses = list(dict.fromkeys(types_losses))
        ordered_types_losses = types_losses
        
        # Initialize a dictionary to accumulate losses per zone
        dict_losses = {'Space': self.s_zone_name}
        for type_loss in types_losses:
            dict_losses[type_loss] = [0] * len(self.s_zone_name)
        
        s_column = data_losses.columns.tolist()[1:]
        for column_name in s_column:
            zone_name = column_name.split('* - ')[0][1:]
            loss_name = column_name.split('* - ')[1]
            dict_losses[loss_name][self.s_zone_name.index(zone_name)] = abs(sum(data_losses[column_name]))

        # Colors and tooltips
        palette_losses = [Turbo256[n] for n in range(0, len(Turbo256), 10)]
        palette_gains = palette_losses[::-1]

        tooltips = [("Type", "$name"), ("Value", "@$name{0.0} kWh/m2")]
        
        # -------------------------
        # Rendering gain bar charts
        # -------------------------

        gains_plots = []
        for i, gain_type in enumerate(ordered_types_gains):
            source_data_gains = {
                'x': self.s_zone_name,
                gain_type: list(dict_gains[gain_type])
            }
            source_gains = ColumnDataSource(data=source_data_gains)
                    
            p = figure(x_range = self.s_zone_name, height=150, width=600,
                        title=f"{gain_type}", title_location="left",
                        toolbar_location=None, tools="hover", tooltips=tooltips)
            p.vbar(x='x', top=gain_type, width=0.9,
                    color=palette_gains[i % len(palette_gains)],
                    source=source_gains, name=gain_type)
            
            # Customize appearance
            p.xgrid.grid_line_color = None
            p.ygrid.grid_line_color = None
            p.axis.minor_tick_line_color = None
            p.xaxis.major_tick_line_color = None
            p.y_range.start = 0
            p.outline_line_color = None
            p.title.text_font_size = "10px"
            p.title.align = "center"
            p.xaxis.axis_label = None
            p.xaxis.major_label_text_font_size = "0pt"
            p.yaxis.axis_label_text_font_size = "5pt"
            gains_plots.append(p)

            # Display title only on the first chart to avoid repetition
            if i == 0:
                p.add_layout(Title(text="Energy Gains and Losses (kWh/m2)", align="center"), "above")
            else:
                p.xaxis.axis_label = None

        # -------------------------
        # Rendering loss bar charts
        # -------------------------
        
        losses_plots = []
        for i, loss_type in enumerate(ordered_types_losses):
            source_data_losses = {
                'x': self.s_zone_name,
                loss_type: list(dict_losses[loss_type])
            }
            source_losses = ColumnDataSource(data=source_data_losses)
                    
            p = figure(x_range = self.s_zone_name, height=150, width=600,
                        title=f"{loss_type}", title_location="left",
                        toolbar_location=None, tools="hover", tooltips=tooltips)
            p.vbar(x='x', top=loss_type, width=0.9,
                    color=palette_losses[i % len(palette_losses)],
                    source=source_losses, name=loss_type)
            
            # Customize appearance
            p.xgrid.grid_line_color = None
            p.ygrid.grid_line_color = None 
            p.y_range.start = 0
            p.axis.minor_tick_line_color = None
            p.xaxis.major_tick_line_color = None
            p.outline_line_color = None
            p.title.text_font_size = "10px"
            p.yaxis.axis_label_text_font_size = "5pt"
            p.title.align = "center"

            losses_plots.append(p)

            # Only show X-axis labels on the last losses chart for clarity
            if i < len(types_losses) - 1:
                p.xaxis.major_label_text_font_size = "0pt"
                p.xaxis.axis_label = None
            else:
                p.xaxis.major_label_text_font_size = "8pt"

        # ----------------------
        # Final Layout
        # ----------------------
        
        layout = column(*gains_plots, *losses_plots)
        output_file(filesave_name + ".html")
        show(layout)