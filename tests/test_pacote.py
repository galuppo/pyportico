from importlib.metadata import version

import portico_espacial


def test_versao_coincide_com_metadados():
	assert portico_espacial.__version__ == version("portico-espacial")


def test_all_exporta_nomes_existentes():
	for nome in portico_espacial.__all__:
		assert hasattr(portico_espacial, nome), nome
