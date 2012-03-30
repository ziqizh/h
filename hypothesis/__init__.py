#!/usr/bin/env python

routes = [
    ('home', '/'),

    ('api', '/api/*subpath'),
    ('token', '/token'),

    ('bookmarklet', '/bookmarklet.js')
]

def includeme(config):
    config.include('.assets')
    config.include('.models')
    config.include('.views')

def create_app(config):
    config.include('.')

    for view, path in routes:
        config.add_route(view, path)

    return config.make_wsgi_app()
