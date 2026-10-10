import importlib.util
from pathlib import Path

import pytest

from portico_espacial import (
	ApoioRestricao,
	Concreto,
	ModeloPortico,
	Ponto,
	Restricao,
	SecaoRetangular,
	TipoAgregado,
)

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def modelo_simples() -> ModeloPortico:
	"""Dois pilares engastados (Terreo -> Pav1) e uma viga entre eles, já montado."""
	modelo = ModeloPortico()
	terreo = modelo.criar_pavimento("Terreo", elevacao=0.0)
	pav1 = modelo.criar_pavimento("Pav1", elevacao=3.0)

	c30 = Concreto(fck_MPa=30.0, agregado=TipoAgregado.BASALTO_DIABASIO, nome="C30")
	secao_pilar = SecaoRetangular(largura=0.30, altura=0.50)
	secao_viga = SecaoRetangular(largura=0.20, altura=0.50)

	for x in (0.0, 5.0):
		pilar = modelo.criar_pilar(
			pavimento_base=terreo, x_base=x, y_base=0.0,
			pavimento_topo=pav1, x_topo=x, y_topo=0.0,
			secao=secao_pilar, material=c30,
		)
		pilar.apoio_base = ApoioRestricao(Restricao.engastado(pilar.ponto_base))

	modelo.criar_viga(
		ponto_inicial=Ponto(0.0, 0.0, 3.0),
		ponto_final=Ponto(5.0, 0.0, 3.0),
		secao=secao_viga, material=c30,
		pavimentos=[pav1],
	)
	modelo.montar()
	return modelo


@pytest.fixture(scope="session")
def exemplos():
	"""Módulo examples/exemplo_portico_espacial.py, carregado pelo caminho."""
	caminho = RAIZ / "examples" / "exemplo_portico_espacial.py"
	spec = importlib.util.spec_from_file_location("exemplo_portico_espacial", caminho)
	modulo = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(modulo)
	return modulo
