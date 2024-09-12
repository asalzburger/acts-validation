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
        self.color = color
        self.marker = marker
        self.markersize = markersize
        self.linestyle = linestyle
        self.linewidth = linewidth
        self.alpha = alpha

    def set_color(self, color: str) -> None:
        self.color = color

    def set_marker(self, marker: str) -> None:
        self.marker = marker

    def set_markersize(self, markersize: float) -> None:
        self.markersize = markersize

    def set_linestyle(self, linestyle: str) -> None:
        self.linestyle = linestyle

    def set_linewidth(self, linewidth: float) -> None:
        self.linewidth = linewidth

    def set_alpha(self, alpha: float) -> None:
        self.alpha = alpha

    def get_style(self) -> dict:
        return {'color': self.color, 'marker': self.marker, 'linestyle': self.linestyle, 'linewidth': self.linewidth, 'alpha': self.alpha}

    def get_color(self) :
        return self.color

    def get_marker(self) :
        return self.marker

    def get_markersize(self) :
        return self.markersize

    def get_linestyle(self) :
        return self.linestyle

    def get_linewidth(self) :
        return self.linewidth

    def get_alpha(self) :
        return self.alpha

