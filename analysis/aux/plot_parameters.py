
from bokeh import plotting as bpl

def plot_parameters(data, xpar, ypar, **kwargs):
   """
   Makes a simple plot of the given parameters
   """
   
   TOOLS = "pan, box_zoom, wheel_zoom, reset"
   
   fig = bpl.figure(plot_width=800, plot_height=600, toolbar_location='right',
                    tools=TOOLS)
   
   fig.circle([1,2], [1,2])
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = ypar
   fig.xaxis.axis_label = xpar
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig