# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import organization as organization_cli
from h.services.organization import OrganizationService


class TestAddCommand(object):

    def test_it_creates_a_third_party_organization(self, cli, cliconfig, organization_service):
        logo = """
               <svg>
                 <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow"/>
               </svg>
               """
        result = cli.invoke(organization_cli.add_organization,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org',
                             u'--logo', logo,
                             ],
                            obj=cliconfig)

        assert result.exit_code == 0

        organization_service.create_organization.assert_called_once_with(
            name=u'Publisher',
            logo=logo,
            authority='publisher.org',
        )

    def test_it_creates_a_third_party_organization_default_logo(self, cli, cliconfig, organization_service):
        result = cli.invoke(organization_cli.add_organization,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org',
                             ],
                            obj=cliconfig)

        assert result.exit_code == 0

        organization_service.create_organization.assert_called_once_with(
            name=u'Publisher',
            logo=None,
            authority='publisher.org',
        )


@pytest.fixture
def organization_service():
    return mock.create_autospec(OrganizationService, spec_set=True, instance=True)


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request, organization_service):
    pyramid_config.register_service(organization_service, name='organization')
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
