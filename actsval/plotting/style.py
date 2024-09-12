#!/usr/bin/env python3

# The style class is a collection of matplotlib styles
class style :
    """ A collection of matplotlib styles """
    def __init__(self, color = None,
                       marker = "o",
                       markersize = None,
                       linestyle = None,
                       linewidth = 1.,
                       alpha = None) -> None:
        """ constructor with default arguments """        
        self.color = color
        self.marker = marker
        self.markersize = markersize
        self.linestyle = linestyle
        self.linewidth = linewidth
        self.alpha = alpha

    def set_color(self, color: str) -> None:
        """ Set the color """
        self.color = color

    def set_marker(self, marker: str) -> None:
        """ Set the marker """
        self.marker = marker

    def set_markersize(self, markersize: float) -> None:
        """ Set the marker size """
        self.markersize = markersize

    def set_linestyle(self, linestyle: str) -> None:
        """ Set the line style """
        self.linestyle = linestyle

    def set_linewidth(self, linewidth: float) -> None:
        """ Set the line width """
        self.linewidth = linewidth

    def set_alpha(self, alpha: float) -> None:
        """ Set the alpha """
        self.alpha = alpha

    def get_style(self) -> dict:
        """ Get the style as a decitionary"""
        return {'color': self.color, 
                'marker': self.marker, 
                'linestyle': self.linestyle, 
                'linewidth': self.linewidth, 
                'alpha': self.alpha}

    def get_color(self) :
        """ single access to the color """
        return self.color

    def get_marker(self) :
        """ single access to the marker """
        return self.marker

    def get_markersize(self) :
        """ single access to the marker size """
        return self.markersize

    def get_linestyle(self) :
        """" single access to the line style """
        return self.linestyle

    def get_linewidth(self) :
        """ single access to the line width """
        return self.linewidth

    def get_alpha(self) :
        """ single access to the alpha """
        return self.alpha