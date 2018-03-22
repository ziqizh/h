# -*- coding: utf-8 -*-

import click


@click.group('organization')
def organization():
    """Manage organization."""


@organization.command('add-organization')
@click.option('--name', prompt=True, help="The name of the organization")
@click.option('--logo', default=None, help="The logo of the organization in the form of an svg")
@click.option('--authority', prompt=True, help="The authority which the organization is associated with")
@click.pass_context
def add_organization(ctx, name, authority, logo):
    """
    Create a new organization.

    Create a new organization that any group of the same authority can belong to.
    """
    request = ctx.obj['bootstrap']()

    organization_svc = request.find_service(name='organization')
    organization_svc.create_organization(
        name=name, logo=logo, authority=authority)

    request.tm.commit()
