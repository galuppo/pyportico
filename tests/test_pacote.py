from importlib.metadata import version

import pyportico


def test_versao_coincide_com_metadados():
	assert pyportico.__version__ == version("pyportico")


def test_all_exporta_nomes_existentes():
	for nome in pyportico.__all__:
		assert hasattr(pyportico, nome), nome
