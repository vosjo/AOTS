import uuid

from bokeh.embed import json_item


def _embed_target_id():
    return f'bk-{uuid.uuid4().hex[:12]}'


def bokeh_embed_response(figure_or_dict):
    """
    Serialize one or more Bokeh figures for client-side embedding via
    ``Bokeh.embed.embed_item()`` (CSP-friendly; no inline script HTML).
    """
    if isinstance(figure_or_dict, dict):
        return {
            key: {'item': json_item(fig, _embed_target_id())}
            for key, fig in figure_or_dict.items()
        }
    return {'item': json_item(figure_or_dict, _embed_target_id())}
