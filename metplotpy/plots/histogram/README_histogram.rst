***Default configuration file for histogram plots***


**[config]**

height:      The height of the final plot in pixels

width:        The width of the final plot in pixels


title:    The title of the plot

bargap:  The spacing between each bar in the plot


showlegend:  Set to True if the plot legend is to be included in the plot, False otherwise

legend_titles:  The title to the legend, if set

legend_orientation:  Set to 'h' for horizontal, 'v' for vertical orientation for the legend

plot_bgcolor:  The colors to use in the plot's background 

histnorm:  ?????

image_name:  A descriptive name describing this plot.

scale:  An integer value depicting XXXXXX????

opacity:  An integer value (1-???) to set the level of opacity of the plot.  Do higher values indicate higher levels of opacity???

orientation: The orientation of the plot, set to 'v' for vertical, 'h' for horizontal

border_width = width of the border, in pixels

xanchor = The position of the x anchor: center, bottom, top

yanchor = The position of the y anchor: center, bottom, top

marker_color = The name of the color to assign to the marker in the plot



**[legend]**

x:

y:

font_family: The name of the font family to be used in the legend


font_size:  The size of the font in the legend, given in pixels.

font_color:  The color of the font in the legend, the name of the color is sufficient, e.g. Black, Blue, etc.

bgcolor:  The background color of the legend, leave empty if no background is desired, otherwise, indicate a
color name

border_color:

border_width:

xanchor:

yanchor:

**[xaxis]**

x:

y:


linecolor:      The color of the x-axis of the plot.  Indicate the name of the color, e.g. Black, Red, etc.

showline:  Set to True to show the x-axis, False otherwise.

linewidth:  The width of the x-axis line, in pixels

**[xaxis_title]**


text:

text_font_family: The name of the font family to be applied to any text in the plot

text_font_size:

text_font_color: The color of the text comprising the title of the x-axis.  The name of the co

**[yaxis]**

x:

y:

linecolor:

linewidth:

showline:

showgrid:

ticks:

tickwidth:

tickcolor:

gridwidth:

gridcolor:

**[yaxis_title]**

text:

text_font_family:

text_font_size:

text_font_color:  The color of the text of the y-axis of the plot.  The name of the color is acceptable, e.g. Black, Red, etc.


**[xbins]**

size: The size of the bins in pixels
