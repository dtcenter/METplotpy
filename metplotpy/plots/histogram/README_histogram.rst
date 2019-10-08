
***Description of Histogram Plotting***


***Description of data***

***Default configuration file for histogram plots***


**[config]**

height:      The height of the final plot in pixels

width:       The width of the final plot in pixels


title:    The title of the plot

bargap:  The spacing between each bar in the plot


showlegend:  Set to True if an item corresponding to this plot is shown in the legend, False otherwise.
legend_titles:  The title to the legend, if set

legend_orientation:  Set to 'h' for horizontal, 'v' for vertical orientation for the legend

plot_bgcolor:  The color of plotting area in-between the x and y axes. Indicate by the hexadecimal code for the
color, eg. #fff.

histnorm: The type of normalization used, one of the following: " ", percent, probability, density, or probability density

image_name:  A descriptive name describing this plot.

scale:  An integer value depicting **????**

opacity:  Number between or equal to 0 and 1 to set the level of opacity level.

orientation: The orientation of the plot, set to 'v' for vertical, 'h' for horizontal

border_width = Any number greater than or equal to 0 to indicate the width of the border, in pixels.

xanchor = The position of the x anchor, indicate one of the following: center, bottom, top

yanchor = The position of the y anchor, indicate one of the following: center, bottom, top

marker_color = The name of the color to assign to the marker in the plot



**[legend]**

x: The x-position of the legend.  **UNITS???**

y:  The y-position of the legend.  **UNITS???**

font_family: The name of the font family to be used in the legend


font_size:  The size of the font in the legend, given in pixels.

font_color:  The color of the font in the legend, the name of the color is sufficient, e.g. Black, Blue, etc.

bgcolor:  The background color of the legend, leave empty if no background is desired, otherwise, indicate a
color name

border_color:  The border color for this plot.  Can be a color or array of colors.

border_width:

xanchor:

yanchor:

**[xaxis]**

x:  The x-position of the title for this axis, in **UNITS???**

y:  The y-position of the title for this axis, in **UNITS???**


linecolor:  The color of the x-axis of the plot.  Indicate the name of the color, e.g. Black, Red, etc.

showline:  Set to True to show the x-axis, False otherwise.

linewidth:  The width of the x-axis line, in pixels

**[xaxis_title]**


text: String or an array of strings, that sets text elements associated with each (x,y) pair.  This
can be undefined by leaving its value blank (undefined).

text_font_family: The name of the font family to be applied to any text in the plot

text_font_size:  The size of the text, a number that is greater than or equal to 1.  **UNITS??**

text_font_color: The color of the text comprising the title of the x-axis.  The name of the co

**[yaxis]**

x:  The position of the title for this axis, in **UNITS??**

y:  The position of the title for this axis, in **UNITS??**

linecolor:  Set the axis line color, indicated by its hexadecimal value, e.g. #444

linewidth:  The width in pixels, of the axis line.  A number greater than or equal to 0.

showline:  A boolean value, set to True to draw a line bounding this axis, False otherwise.

showgrid:  A boolean value, set to True to draw grid lines at every tick mark, False otherwise.

ticks:Determine whether or not ticks are drawn.  If not defined, ie value is left empty, then the axis ticks are
not drawn.  If set to 'outside', the axis' are drawn outside the axis line.  If set to 'inside', the axis' are drawn
inside the axis lines.

tickwidth: A number greater than or equal to 0 indicating the tick width in pixels.

tickcolor: The tick color, indicated by its hexadecimal value, e.g. #444.

gridwidth:  A number greater than or equal to 0.  The width, in pixels of the axis line.

gridcolor:  The axis line color, indicated by its hexadecimal value, eg #f000

**[yaxis_title]**

text: String or an array of strings, that sets text elements associated with each (x,y) pair.  This
can be undefined by leaving its value blank (undefined).

text_font_family:  The font family to be applied to this axis.  Plotly supports the following font families:
*Arial, Balto, Courier New, Droid Sans, Droid Serif, Droid Sans Mono, Gravitas One, Old Standart TT, Open Sans,
Overpass, Pt Sans Narrow, Raleway, Times New Roman*

text_font_size: A single number greater than or equal to 1

text_font_color:  The color of the text of the y-axis of the plot.  The name of the color is acceptable, e.g. Black, Red, etc.


**[xbins]**
start:  The starting value of the first bin
end:  The end value of the last bin
size: The size of the bins in pixels
