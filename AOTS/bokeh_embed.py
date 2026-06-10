from bokeh.embed import components


def bokeh_embed_response(figure_or_dict):
    """
    Serialize one or more Bokeh figures for client-side embedding.
    """
    if isinstance(figure_or_dict, dict):
        result = {}
        for key, fig in figure_or_dict.items():
            script, div = components(fig)
            result[key] = {'script': script, 'div': div}
        return result
    script, div = components(figure_or_dict)
    return {'script': script, 'div': div}
