from __future__ import annotations

from app.services.source_display_name import SourceDisplayNameService


def test_tablon_demanda_inmobiliaria_nacional_with_params_and_trailing_slash():
    url = "https://www.tablondeanuncios.com/inmobiliaria/?demanda=1"

    assert SourceDisplayNameService.from_url(url) == "🏠 Demanda inmobiliaria (España)"


def test_tablon_demanda_inmobiliaria_nacional_with_params_without_trailing_slash():
    url = "https://www.tablondeanuncios.com/inmobiliaria?demanda=1"

    assert SourceDisplayNameService.from_url(url) == "🏠 Demanda inmobiliaria (España)"


def test_tablon_demanda_inmobiliaria_provincia_with_params_and_trailing_slash():
    url = "https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1"

    assert SourceDisplayNameService.from_url(url) == "🏠 Demanda inmobiliaria · Murcia"


def test_tablon_demanda_inmobiliaria_provincia_with_params_without_trailing_slash():
    url = "https://www.tablondeanuncios.com/inmobiliaria-en-valencia?demanda=1"

    assert SourceDisplayNameService.from_url(url) == "🏠 Demanda inmobiliaria · Valencia"


def test_tablon_no_demanda_without_params_and_trailing_slash():
    url = "https://www.tablondeanuncios.com/pisos-en-alquiler-en-malaga/"

    assert SourceDisplayNameService.from_url(url) == "🏠 Pisos en alquiler · Málaga"


def test_tablon_no_demanda_without_params_without_trailing_slash():
    url = "https://www.tablondeanuncios.com/pisos-en-alquiler-en-malaga"

    assert SourceDisplayNameService.from_url(url) == "🏠 Pisos en alquiler · Málaga"
