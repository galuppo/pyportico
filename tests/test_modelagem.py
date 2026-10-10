def test_portico_simples_gera_lances_e_vaos(modelo_simples):
	assert [p.nome for p in modelo_simples.pilares] == ["P1", "P2"]
	assert all(len(p.lances) == 1 for p in modelo_simples.pilares)
	assert len(modelo_simples.vigas) == 1
	assert len(modelo_simples.vigas[0].vaos) == 1
	assert modelo_simples.links == []


def test_ids_das_barras_sao_unicos(modelo_simples):
	ids = [barra.id for barra in modelo_simples.barras()]
	assert len(ids) == len(set(ids))


def test_viga_isolada_quebra_nos_apoios(exemplos):
	modelo = exemplos.exemplo_viga_isolada_com_4_apoios()
	assert len(modelo.pilares) == 0
	assert len(modelo.vigas[0].vaos) == 3


def test_exemplo_edificio_monta(exemplos):
	modelo = exemplos.exemplo_edificio()
	assert len(modelo.pilares) == 14
	assert len(modelo.vigas) == 26
	assert len(modelo.lajes) == 7
