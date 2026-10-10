import pytest

from pyportico.exportadores.ifc import EscritorIfcManual, ExportadorIfc

ezdxf = pytest.importorskip("ezdxf")
from pyportico.exportadores.dxf import ExportadorDxf  # noqa: E402


@pytest.mark.parametrize("metodo", ["exportar", "exportar_solido"])
def test_dxf_gera_arquivo_legivel(modelo_simples, tmp_path, metodo):
	arquivo = tmp_path / "portico.dxf"
	getattr(ExportadorDxf(), metodo)(modelo_simples, str(arquivo))
	documento = ezdxf.readfile(arquivo)
	assert len(documento.modelspace()) > 0


def test_ifc_gera_arquivo_step(modelo_simples, tmp_path):
	arquivo = tmp_path / "portico.ifc"
	ExportadorIfc(modelo_simples, EscritorIfcManual()).exportar(str(arquivo))
	conteudo = arquivo.read_text(encoding="utf-8")
	assert conteudo.startswith("ISO-10303-21;")
	assert "FILE_SCHEMA(('IFC4'));" in conteudo
	assert "IFCCOLUMN(" in conteudo
	assert "IFCBEAM(" in conteudo


def test_ifc_e_deterministico(modelo_simples, tmp_path):
	arquivos = [tmp_path / "a.ifc", tmp_path / "b.ifc"]
	for arquivo in arquivos:
		ExportadorIfc(modelo_simples, EscritorIfcManual()).exportar(str(arquivo))
	assert arquivos[0].read_bytes() == arquivos[1].read_bytes()
