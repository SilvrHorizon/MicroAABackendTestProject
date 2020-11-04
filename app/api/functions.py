from flask import jsonify, request, url_for
from werkzeug.http import HTTP_STATUS_CODES


def api_paginate_query(query, endpoint, page, per_page=1, **kwargs):
    paginated = query.paginate(page, per_page, False)

    return {
        "items": [item.to_dict() for item in paginated.items],
        "_meta": {
            "page": page,
            "per_page": per_page,
            "total_items": paginated.total
        },
        "_links": {
            "self": url_for(endpoint, page=page, **kwargs),
            "next_page": (url_for(endpoint, page=page + 1, **kwargs)) if paginated.has_next else None,
            "prev_page": (url_for(endpoint, page=page - 1, **kwargs)) if paginated.has_prev else None
        }
    }

def get_pagination_page():
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        try:
            page = int(page)
        except (ValueError):
            page = 1
    return page

def make_error_response(status_code, message=None):
    data = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')
    }

    if message:
        data["message"] = message

    response = jsonify(data)
    response.status_code = status_code
    return response

def make_bad_request(message=None):
    return make_error_response(status_code=400, message=message)
