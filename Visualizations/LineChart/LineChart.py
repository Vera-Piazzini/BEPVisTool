"""
Line Charts for PMV and PPD
===========================

This module implements the ``lnchrt`` class used in BEPVis to generate
monthly PMV or PPD trend line charts for each space (People Object).

Features
--------
- Supports PMV and PPD monthly aggregated data
- Displays average, minimum, and maximum per zone
- Adds comfort annotations and recommended ranges (ISO / ASHRAE 55)
- Generates interactive HTML outputs with Bokeh
- Creates a clean legend, hover tool, and color-coded comfort bands

Input Format
------------
The Excel sheet must contain the following columns:

For each `nominal_people_object_name`:
    * <Name>
    * <Name>max
    * <Name>min

Example:
    Month | Office1 | Office1max | Office1min | Office2 | ...

Authors: Ofelia Vera-Piazzini, Massimiliano Scarpa (Università Iuav di Venezia)  
License: MIT
"""

import pandas as pd
from bokeh.models import BoxAnnotation, HoverTool, Legend, LegendItem, Span, ColumnDataSource
from bokeh.plotting import figure, show, output_file, save
import colorcet as cc
import random

# ============================================================================
# Helper Function
# ============================================================================

def Replace_FromDict(string = '?', dict = {}):
    """
    Replace multiple characters in a string using a mapping dictionary.

    Parameters
    ----------
    string : str
        Input string.
    dict : dict
        Dictionary where key = old character, value = new character.

    Returns
    -------
    str
        Cleaned string.
    """
    result = string
    for key, value in dict.items():
        result = result.replace(str(key), str(value))
    return result

# ============================================================================
# Line Chart Class
# ============================================================================

class lnchrt:
    """
    Generate PMV/PPD monthly line charts for all zones.

    Parameters
    ----------
    source_file_pathandname : str
        Excel file containing PMV or PPD results.
    s_nominal_people_object_name : list[str]
        List of People-Object names (spaces).
    html_file_pathandname : str
        Optional output filename (deprecated, overwritten by filesave_name).
    target : str
        'PMV' or 'PPD'.
    filesave_name : str
        Output filename for the interactive HTML file.

    Notes
    -----
    - The plot includes mean/min/max lines for each zone.
    - Comfort ranges are displayed depending on PMV/PPD.
    - Each zone gets a unique Glasbey color from ``colorcet``.
    """

    def __init__(self, source_file_pathandname = '?',
                 s_nominal_people_object_name = '?',
                 html_file_pathandname = '?',
                 target = '?',
                 filesave_name = '?'):
        
        # Validate target
        target = target.upper()
        if not(target in ['PMV', 'PPD']):
            print('target is not among available ones')
        else:
            # Load data from Excel
            df = pd.read_excel(source_file_pathandname, sheet_name = target + ' Data')
            
            # Initialize variables
            s_color = cc.glasbey_bw[0:len(s_nominal_people_object_name)]
            
            # Convert data in sources for Bokeh
            source = []
            r = []
            n_people = -1
            import random
            s_nominal_people_object_name_alias = []
            
            # Prepare clean aliases forcolumn names
            replace_dict = {' ': '_', '-': '_', '.': '_', ',': '_', ':': '_', ';': '_','!': '_','?': '_','+': '_','*': '_','\\': '_','/': '_'}
            for nominal_people_object_name in s_nominal_people_object_name:
                nominal_people_object_name_alias = Replace_FromDict(string = nominal_people_object_name, dict = replace_dict)
                s_nominal_people_object_name_alias.append(nominal_people_object_name_alias)
                n_people += 1
                source.append(ColumnDataSource(data={'months': df['Month'], nominal_people_object_name_alias: df[nominal_people_object_name], nominal_people_object_name_alias + 'max': df[nominal_people_object_name + 'max'], nominal_people_object_name_alias + 'min': df[nominal_people_object_name + 'min']}))
                
                # Define Y range depending on PMV/PPD
                if target == 'PMV':
                    y_range = (-3, 3)
                else:
                    y_range = (0, 100)
                
                # Create figure
                p = figure(x_range=df['Month'], y_range = y_range, height=500, width=800, title="Monthly average " + target + " values by space", 
                        tools="pan,wheel_zoom,reset, box_select,box_zoom,lasso_select")

            # --------------------------------------------------------------
            # Draw lines (mean, max, min) for each zone
            # --------------------------------------------------------------

            r_people = []
            random.seed(23)
            n_people = -1
            for nominal_people_object_name in s_nominal_people_object_name:
                n_people += 1
                nominal_people_object_name_alias = s_nominal_people_object_name_alias[n_people]
                color = cc.glasbey_category10[n_people]
                
                color = 'rgb(' + str(int(color[0] * 255)) + ',' \
                                + str(int(color[1] * 255)) + ',' \
                                + str(int(color[2] * 255)) + ')'
                
                r_people.append(p.line(x = 'months', y = nominal_people_object_name_alias, source = source[n_people], color = color, line_width = 1.6))
                r_people.append(p.line(x = 'months', y = nominal_people_object_name_alias + 'max', source = source[n_people], color = color, line_width = 0.8))
                r_people.append(p.line(x = 'months', y = nominal_people_object_name_alias + 'min', source = source[n_people], color = color, line_width = 0.8))

            # --------------------------------------------------------------
            # Hover tools for each zone
            # --------------------------------------------------------------
            hover = []
            items = []
            n_people = -1
            for nominal_people_object_name in s_nominal_people_object_name:
                n_people += 1
                nominal_people_object_name_alias = s_nominal_people_object_name_alias[n_people]
                hover.append(HoverTool(renderers=[r_people[n_people * 3], r_people[n_people * 3 + 1], r_people[n_people * 3 + 2]], tooltips=[
                                                            ("Space", nominal_people_object_name),
                                                            ("Month", "@months"),
                                                            ("Min", "@*PEOPLENAME*min".replace('*PEOPLENAME*', nominal_people_object_name_alias)),                                          
                                                            ("Avg", "@*PEOPLENAME*".replace('*PEOPLENAME*', nominal_people_object_name_alias)),
                                                            ("Max", "@*PEOPLENAME*max".replace('*PEOPLENAME*', nominal_people_object_name_alias))]))
                p.add_tools(hover[-1])
                items.append(LegendItem(label=nominal_people_object_name_alias, renderers=[r_people[n_people * 3], r_people[n_people * 3 + 1], r_people[n_people * 3 + 2]]))

            # ============================================================================
            # Comfort Zones and Standard Limits
            # ============================================================================

            legend1 = Legend(items = items, orientation="horizontal", location="top_center")
            dummy_glyph_renderers = [p.square([0], [0], fill_color=color, line_color=None) for color in ["#E9C2C1", "#F2DADA", "#F7E7E6", "#F8FAF3", "#F3F6FA", "#DAE4F1", "#C2D3E9"]]

            if target == 'PMV': 
                # Add PMV color bands (ISO 7730)
                hot_box = BoxAnnotation(bottom=2.5, top=3, fill_alpha=0.7, fill_color="#E9C2C1", level="underlay")
                warm_box = BoxAnnotation(bottom=1.5, top=2.5, fill_alpha=0.7, fill_color="#F2DADA", level="underlay")
                slightlywarm_box = BoxAnnotation(bottom=0.5, top=1.5, fill_alpha=0.7, fill_color="#F7E7E6", level="underlay")
                neutral_box = BoxAnnotation(bottom=-0.5, top=0.5, fill_alpha=0.7, fill_color="#F8FAF3", level="underlay")
                slightlycool_box = BoxAnnotation(bottom=-1.5, top=-0.5, fill_alpha=0.7, fill_color="#F3F6FA", level="underlay")
                cool_box = BoxAnnotation(bottom=-2.5, top=-1.5, fill_alpha=0.7, fill_color="#DAE4F1", level="underlay")
                cold_box = BoxAnnotation(bottom=-3, top=-2.5, fill_alpha=0.7, fill_color="#C2D3E9", level="underlay")
                p.add_layout(hot_box)
                p.add_layout(warm_box)
                p.add_layout(slightlywarm_box)
                p.add_layout(neutral_box)
                p.add_layout(slightlycool_box)
                p.add_layout(cool_box)
                p.add_layout(cold_box)

                # ISO 7730 recommended range
                span1 = Span(location=0.7, dimension='width', line_color='black', line_dash='dashed', line_width=0.5)
                span2 = Span(location=-0.7, dimension='width', line_color='black', line_dash='dashed', line_width=0.5)
                p.add_layout(span1)
                p.add_layout(span2)

                legend = Legend(items=[LegendItem(label="- - - ISO 7730 (Existing buildings)", renderers=[p.line(x=[0, 0], y=[0, 0], line_color=None, line_alpha=0)])],
                                location="top_right")
                legend2 = Legend(title= "PMV index", items=[LegendItem(label="Hot", renderers=[dummy_glyph_renderers[0]]),
                                        LegendItem(label="Warm", renderers=[dummy_glyph_renderers[1]]),
                                        LegendItem(label="Slightly Warm", renderers=[dummy_glyph_renderers[2]]),
                                        LegendItem(label="Neutral", renderers=[dummy_glyph_renderers[3]]),
                                        LegendItem(label="Slightly Cool", renderers=[dummy_glyph_renderers[4]]),
                                        LegendItem(label="Cool", renderers=[dummy_glyph_renderers[5]]),
                                        LegendItem(label="Cold", renderers=[dummy_glyph_renderers[6]])],
                                        location="center_right")
            else:
                # Add PPD comfort range zones
                Outofrange_box = BoxAnnotation(bottom=0, top=15, fill_alpha=0.7, fill_color="#F8FAF3", level="underlay")
                Comfort_box = BoxAnnotation(bottom=15, top=100, fill_alpha=0.7, fill_color="#F2DADA", level="underlay")
                p.add_layout(Outofrange_box)
                p.add_layout(Comfort_box)
                
                # Spans
                span1 = Span(location=15, dimension='width', line_color='black', line_dash='dashed', line_width=0.5)

                p.add_layout(span1)

                legend = Legend(items=[LegendItem(label="- - - - - ASHRAE 55 recommended range", renderers=[p.line(x=[0, 0], y=[0, 0], line_color=None, line_alpha=0)])],
                                    location="top_right")
                legend2 = Legend(title="PPD ranges", items=[
                        LegendItem(label="Out of range", renderers=[dummy_glyph_renderers[1]]),
                        LegendItem(label="Comfort range", renderers=[dummy_glyph_renderers[3]])], 
                        location="center_right")
            
            # ----------------------------------------------------------------------
            # Final Legend and Layout
            # ----------------------------------------------------------------------

            # Format legends
            legend1.border_line_color = None
            legend2.border_line_color = None
            legend1.label_text_font_size = '7pt'
            legend2.label_text_font_size = '8pt'
            p.add_layout(legend2, 'right')
            p.add_layout(legend1, 'above')
            p.legend.click_policy="mute"
            legend.label_text_font_size = "7pt"
            legend.background_fill_color = None

            # Axis labels
            p.xaxis.axis_label = "Months"
            p.yaxis.axis_label = target + " values"
            p.yaxis.major_label_orientation = "horizontal"

            # Final layout
            p.add_layout(legend)
            html_file_pathandname = "Zones - " + target + " - Monthly" + '.html'
            
            # Output
            output_file(filename = html_file_pathandname, title = "Zones - " + target + " - Monthly")
            output_file(filesave_name + ".html")
            show(p)