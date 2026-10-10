"""
Exemplos de uso do Pórtico Espacial.

Constroem o modelo via os métodos criar_* do ModeloPortico, chamam
ModeloPortico.montar() e exportam o edifício para DXF e IFC em
examples/saida/.

id é sempre gerado internamente pelo ModeloPortico -- nunca informado
aqui. nome é informado explicitamente só quando queremos um valor
específico; nos outros casos, deixamos o próprio modelo gerar.

Execução (com o pacote instalado: pip install -e ".[dxf]"):
	python examples/exemplo_portico_espacial.py
"""

from pathlib import Path

from portico_espacial.concreto import Concreto, TipoAgregado
from portico_espacial.elementos import ApoioRestricao
from portico_espacial.estrutura import ModeloPortico
from portico_espacial.geometria import Ponto
from portico_espacial.secoes import SecaoRetangular
from portico_espacial.vinculos import Restricao
from portico_espacial.exportadores.dxf import ExportadorDxf
from portico_espacial.exportadores.ifc import ExportadorIfc, EscritorIfcManual


def exemplo_portico_simples() -> ModeloPortico:
	"""
	Pórtico simples: dois pilares (Térreo -> Pav1) sustentando uma
	viga no nível do Pav1, com fundação (engaste, não modelada em
	detalhe) na base de cada pilar.

		P1 (0,0)         P2 (5,0)
		 |                 |
		 |----- V1 --------|   <- nível Pav1 (z = 3.0)
		 |                 |
		(engaste)         (engaste)   <- nível Terreo (z = 0.0)
	"""
	modelo = ModeloPortico()

	# 1) Pavimentos -- sempre ANTES de qualquer elemento, criados pelo próprio modelo
	terreo = modelo.criar_pavimento(nome="Terreo", elevacao=0.0)
	pav1 = modelo.criar_pavimento(nome="Pav1", elevacao=3.0)

	# 2) Seção e material -- reaproveitados pelos dois pilares e pela viga
	sec_pilar = SecaoRetangular(largura=0.3, altura=0.5)
	sec_viga = SecaoRetangular(largura=0.2, altura=0.5)
	concreto = Concreto(fck_MPa=30.0, agregado=TipoAgregado.BASALTO_DIABASIO, nome="C30")

	# 3) Pilares P1 (0,0) e P2 (5,0), os dois do Terreo ao Pav1 -- id e nome
	#    ("P1", "P2") gerados automaticamente pelo modelo
	p1 = modelo.criar_pilar(
		pavimento_base=terreo, x_base=0.0, y_base=0.0,
		pavimento_topo=pav1, x_topo=0.0, y_topo=0.0,
		secao=sec_pilar, material=concreto,
	)
	p2 = modelo.criar_pilar(
		pavimento_base=terreo, x_base=5.0, y_base=0.0,
		pavimento_topo=pav1, x_topo=5.0, y_topo=0.0,
		secao=sec_pilar, material=concreto,
	)
	# Fundação não modelada em detalhe -- engaste direto na base de cada pilar
	p1.apoio_base = ApoioRestricao(restricao=Restricao.engastado(p1.ponto_base))
	p2.apoio_base = ApoioRestricao(restricao=Restricao.engastado(p2.ponto_base))

	# 4) Viga ligando P1 a P2, com o topo da seção no nível do Pav1 (z = 3.0)
	#    -- nome gerado a partir do Pav1 (numeração por pavimento)
	v1 = modelo.criar_viga(
		ponto_inicial=Ponto(0.0, 0.0, 3.0),
		ponto_final=Ponto(5.0, 0.0, 3.0),
		secao=sec_viga, material=concreto,
		pavimentos=[pav1],
	)

	modelo.montar()
	return modelo

def exemplo_viga_isolada_com_4_apoios() -> ModeloPortico:
	"""
	Viga isolada (nenhum Pilar no modelo), contínua sobre 4 apoios
	simples -- útil pra validar o comportamento de uma viga sem
	modelar o resto do pórtico em volta.

		|---- 3,0 m ----|---- 3,0 m ----|---- 3,0 m ----|
		^                ^               ^                ^
	  apoio 1          apoio 2         apoio 3          apoio 4
	 (dist. 0,0)      (dist. 3,0)     (dist. 6,0)      (dist. 9,0)
	"""
	modelo = ModeloPortico()

	# Mesmo isolada, precisa de ao menos 1 Pavimento registrado (pode ser fictício)
	pav = modelo.criar_pavimento(nome="Ficticio", elevacao=0.0)

	sec = SecaoRetangular(largura=0.2, altura=0.5)
	concreto = Concreto(fck_MPa=30.0, agregado=TipoAgregado.BASALTO_DIABASIO, nome="C30")

	viga = modelo.criar_viga(
		ponto_inicial=Ponto(0.0, 0.0, 0.0),
		ponto_final=Ponto(9.0, 0.0, 0.0),
		secao=sec, material=concreto,
		pavimentos=[pav],
		restricoes=[
			(0.0, Restricao.apoio_simples(Ponto(0.0, 0.0, 0.0))),
			(3.0, Restricao.apoio_simples(Ponto(3.0, 0.0, 0.0))),
			(6.0, Restricao.apoio_simples(Ponto(6.0, 0.0, 0.0))),
			(9.0, Restricao.apoio_simples(Ponto(9.0, 0.0, 0.0))),
		],
	)

	modelo.montar()
	return modelo

def exemplo_edificio() -> ModeloPortico:
	"""
		Um edificio multipavimentos, considerando pilares prosseguindo 
		pela platibanda e com torre de caixa d'água
		----- Pavimentos -----
		Cobertura (14.5)
		Reservatório (10.5)
		Terraço (7.5)
		Mezanino (3.0)
		Térreo (0.0)
		Fundação (-1.0)

		----- Eixos e pilares

				A(X=0)		B(X=5)		C(X=10)		D(X=14)
				  |			  |			   |		   |
		1(Y=0)--- P1----------P2-----------P3----------P4---
				  |			  |			   |		   |
		2(Y=-5)---P5----------|------------P6----------P7---
				  |			  |			   |		   |
		3(Y=-10)--P8----------|------------P9----------P10--
				  |			  |			   |		   |
		4(Y=-14)--P11---------P12----------P13---------P14--
				  |			  |			   |		   |

		----- Pilares
		P1 	(A,1) - Fundação -> Terraço (+1,20m)
		P2 	(B,1) - Fundação -> Terraço (+1,20m)
		P3 	(C,1) - Fundação -> Cobertura
		P4 	(D,1) - Fundação -> Cobertura
		P5 	(A,2) - Fundação -> Terraço (+1,20m)
		P6 	(C,2) - Fundação -> Cobertura
		P7	(D,2) - Fundação -> Cobertura
		P8 	(A,3) - Fundação -> Terraço (+1,20m)
		P9 	(C,3) - Fundação -> Mezanino
		P10 (D,3) - Fundação -> Terraço (+1,20m)
		P11 (A,4) - Fundação -> Terraço (+1,20m)
		P12 (B,4) - Fundação -> Terraço (+1,20m)
		P13 (C,4) - Fundação -> Terraço (+1,20m)
		P14 (D,4) - Fundação -> Terraço (+1,20m)

		----- Térreo
		
				A(X=0)		B(X=5)		C(X=10)		D(X=14)
				  |			  |			   |		   |
		1(Y=0)--- P1---(V1)---P2---(V1)----P3---(V1)---P4---
				  |			  |			   |		   |
				 (V4)		  |			  (V5)		  (V6)
				  |			  |			   |		   |
		2(Y=-5)---P5----------|------------P6---(V2)---P7---
				  |			  |			   |		   |
				 (V4)		  |			  (V5)		  (V6)
				  |			  |			   |		   |
		3(Y=-10)--P8----------|------------P9----------P10--
				  |			  |			   |		   |
				 (V4)		  |			  (V5)		  (V6)
				  |			  |			   |		   |
		4(Y=-14)--P11--(V3)--P12---(V3)---P13---(V3)---P14--
				  |			  |			   |		   |

		----- Mezanino (L3 é uma marquise interna com 1,20m de balanço)
		
				A(X=0)		B(X=5)		C(X=10)		D(X=14)
				  |			  |			   |		   |
		1(Y=0)--- P1---(V1)---P2---(V1)----P3---(V1)---P4---
				  |			  |			   |		   |
				 (V4)		  |			  (V5)	 L1	  (V6)
				  |			  |			   |		   |
		2(Y=-5)---P5----------|---(1,2m)---P6---(V2)---P7---
				  |			  |	  |		   |		   |
				 (V4)		  |	  |	L3	  (V5)		  (V6)
				  |			  |	  |		   |		   |
		3(Y=-10)--P8----------|---|--------P9	L2	   P10--
				  |			  |			   |		   |
				 (V4)		  |			  (V5)		  (V6)
				  |			  |			   |		   |
		4(Y=-14)--P11--(V3)--P12---(V3)---P13---(V3)---P14--
				  |			  |			   |		   |

		----- Terraço
		
				A(X=0)		B(X=5)		C(X=10)		D(X=14)
				  |			  |			   |		   |
		1(Y=0)--- P1---(V1)---P2---(V1)----P3---(V1)---P4---
				  |			  			   |		   |
				 (V4)		  			  (V5)	 L1	  (V6)
				  |			  			   |		   |
		2(Y=-5)---P5					   P6---(V2)---P7---
				  |			  	  		   |		   |
				 (V4)		  L3  		  (V5)	L2	  (V6)
				  |			  	  		   |		   |
		3(Y=-10)--P8					   P9----------P10--
				  |			  			   |		   |
				 (V4)		  			  (V5)	L2	  (V6)
				  |			  			   |		   |
		4(Y=-14)--P11--(V3)--P12---(V3)---P13---(V3)---P14--
				  |			  |			   |		   |
			
		----- Reservatório
		
				A(X=0)		B(X=5)		C(X=10)		D(X=14)
				  |			  |			   |		   |
		1(Y=0)----|-----------|------------P3---(V1)---P4---
				  |			  |			   |		   |
				  |			  |			  (V3)		  (V4)
				  |			  |			   |		   |
		2(Y=-5)---|-----------|------------P6---(V2)---P7---
				  |			  |			   |		   |
				  |			  |			   |		   |
				  |			  |			   |		   |
		3(Y=-10)--|-----------|------------| ----------|----
				  |			  |			   |		   |
				  |			  |			   |		   |
				  |			  |			   |		   |
		4(Y=-14)--|-----------|------------|----------------
				  |			  |			   |		   |


		"""
	modelo = ModeloPortico()

	concreto = Concreto(30, TipoAgregado.BASALTO_DIABASIO, "C30")
	modelo.material_link = Concreto(9999.0, TipoAgregado.BASALTO_DIABASIO, "Link")

	pav_fundacao = modelo.criar_pavimento("Fundação", -1.0)
	pav_terreo = modelo.criar_pavimento("Térreo", 0.0)
	pav_mezanino = modelo.criar_pavimento("Mezanino", 3.0)
	pav_terraco = modelo.criar_pavimento("Terraço", 7.5)
	pav_reservatorio = modelo.criar_pavimento("Reservatório", 10.5)
	pav_cobertura = modelo.criar_pavimento("Cobertura", 14.5)

	# Eixos
	eA = 0.0
	eB = 5.0
	eC = 10.0
	eD = 14.0
	e1 = 0.0
	e2 = -5.0
	e3 = -10.0
	e4 = -14.0

	# Seções
	secao_p_20x40 = SecaoRetangular(0.2, 0.4)
	secao_p_40x20 = SecaoRetangular(0.4, 0.2)
	secao_p_20x60 = SecaoRetangular(0.2, 0.6)
	secao_p_60x20 = SecaoRetangular(0.6, 0.2)
	secao_v_20x50 = SecaoRetangular(0.2, 0.5)
	secao_v_20x30 = SecaoRetangular(0.2, 0.3)
	secao_g_10 = SecaoRetangular(0.25, 0.1)
	modelo.secao_link = SecaoRetangular(9999.0,9999.0)

	
	# Pilares
	# P1 	(A,1) - Fundação -> Terraço (+1,20m)
	p1 = modelo.criar_pilar(
		pav_fundacao, eA, e1,
		pav_terraco, eA, e1,
		secao_p_20x40,
		concreto,
		desnivel_topo=1.2,
		nome="P1")
	# P2 	(B,1) - Fundação -> Terraço (+1,20m)
	p2 = modelo.criar_pilar(
		pav_fundacao, eB, e1,
		pav_terraco, eB, e1,
		secao_p_20x40,
		concreto,
		desnivel_topo=1.2,
		nome="P2")
	# P3 	(C,1) - Fundação -> Cobertura
	p3 = modelo.criar_pilar(
		pav_fundacao, eC, e1-.1,
		pav_cobertura, eC, e1-.1,
		secao_p_20x60,
		concreto,
		nome="P3")
	# P4 	(D,1) - Fundação -> Cobertura
	p4 = modelo.criar_pilar(
		pav_fundacao, eD, e1-.1,
		pav_cobertura, eD, e1-.1,
		secao_p_20x60,
		concreto,
		nome="P4")
	# P5 	(A,2) - Fundação -> Terraço (+1,20m)
	p5 = modelo.criar_pilar(
		pav_fundacao, eA+.1, e2,
		pav_terraco, eA+.1, e2,
		secao_p_40x20,
		concreto,
		nome="P5",
		desnivel_topo=1.20)
	# P6 	(C,2) - Fundação -> Cobertura
	p6 = modelo.criar_pilar(
		pav_fundacao, eC, e2+.2,
		pav_cobertura, eC, e2+.2,
		secao_p_20x60,
		concreto,
		nome="P6")
	# P7	(D,2) - Fundação -> Cobertura
	p7 = modelo.criar_pilar(
		pav_fundacao, eD-.2, e2,
		pav_cobertura, eD-.2, e2,
		secao_p_20x60,
		concreto,
		nome="P7",
		rotacao=90)
	# P8 	(A,3) - Fundação -> Terraço (+1,20m)
	p8 = modelo.criar_pilar(
		pav_fundacao, eA, e3,
		pav_terraco, eA, e3,
		secao_p_20x40,
		concreto,
		nome="P8",
		desnivel_topo=1.2)
	# P9 	(C,3) - Fundação -> Mezanino
	p9 = modelo.criar_pilar(
		pav_fundacao, eC+.1, e3,
		pav_mezanino, eC+.1, e3,
		secao_p_40x20,
		concreto,
		nome="P9")
	# P10 (D,3) - Fundação -> Terraço (+1,20m)
	p10 = modelo.criar_pilar(
		pav_fundacao, eD-.1, e3,
		pav_terraco, eD-.1, e3,
		secao_p_40x20,
		concreto,
		nome="P10",
		desnivel_topo=1.2)
	# P11 (A,4) - Fundação -> Terraço (+1,20m)
	p11 = modelo.criar_pilar(
			pav_fundacao, eA, e4,
			pav_terraco, eA, e4,
			secao_p_20x40,
			concreto,
			nome="P11",
			desnivel_topo=1.2)
	# P12 (B,4) - Fundação -> Terraço (+1,20m)
	p12 = modelo.criar_pilar(
				pav_fundacao, eB, e4,
				pav_terraco, eB, e4,
				secao_p_20x40,
				concreto,
				nome="P12",
				desnivel_topo=1.2)
	# P13 (C,4) - Fundação -> Terraço (+1,20m)
	p13 = modelo.criar_pilar(
					pav_fundacao, eC, e4,
					pav_terraco, eC, e4,
					secao_p_20x40,
					concreto,
					nome="P13",
					desnivel_topo=1.2)
	# P14 (D,4) - Fundação -> Terraço (+1,20m)
	p14 = modelo.criar_pilar(
					pav_fundacao, eD, e4,
					pav_terraco, eD, e4,
					secao_p_20x40,
					concreto,
					nome="P14",
					desnivel_topo=1.2)	

	# Vigas Térreo
	v1_terreo = modelo.criar_viga(
		Ponto(p1.ponto_base.x, p1.ponto_base.y+.1, pav_terreo.elevacao),
		Ponto(p4.ponto_base.x, p4.ponto_base.y+.2, pav_terreo.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terreo],	
		nome="V1")
	v2_terreo = modelo.criar_viga(
		Ponto(p6.ponto_base.x, p6.ponto_base.y-.2, pav_terreo.elevacao),
		Ponto(p7.ponto_base.x, p7.ponto_base.y, pav_terreo.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terreo],	
		nome="V2")
	v3_terreo = modelo.criar_viga(
		Ponto(p11.ponto_base.x, p11.ponto_base.y-.1, pav_terreo.elevacao),
		Ponto(p14.ponto_base.x, p14.ponto_base.y-.1, pav_terreo.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terreo],	
		nome="V3")
	v4_terreo = modelo.criar_viga(
		Ponto(p1.ponto_base.x, p1.ponto_base.y, pav_terreo.elevacao),
		Ponto(p11.ponto_base.x, p11.ponto_base.y, pav_terreo.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terreo],	
		nome="V4")
	v5_terreo = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y, pav_terreo.elevacao),
		Ponto(p13.ponto_base.x, p13.ponto_base.y, pav_terreo.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terreo],	
		nome="V5")
	v6_terreo = modelo.criar_viga(
		Ponto(p4.ponto_base.x, p4.ponto_base.y, pav_terreo.elevacao),
		Ponto(p14.ponto_base.x, p14.ponto_base.y, pav_terreo.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terreo],	
		nome="V6")

	# Vigas Mezanino
	v1_mezanino = modelo.criar_viga(
		Ponto(p1.ponto_base.x, p1.ponto_base.y+.1, pav_mezanino.elevacao),
		Ponto(p4.ponto_base.x, p4.ponto_base.y+.2, pav_mezanino.elevacao),
		secao_v_20x50,
		concreto,
		[pav_mezanino],	
		nome="V1")
	v2_mezanino = modelo.criar_viga(
		Ponto(p6.ponto_base.x-1.2, p6.ponto_base.y-.2, pav_mezanino.elevacao),
		Ponto(p7.ponto_base.x, p7.ponto_base.y, pav_mezanino.elevacao),
		secao_v_20x50,
		concreto,
		[pav_mezanino],	
		nome="V2")
	v3_mezanino = modelo.criar_viga(
		Ponto(p11.ponto_base.x, p11.ponto_base.y-.1, pav_mezanino.elevacao),
		Ponto(p14.ponto_base.x, p14.ponto_base.y-.1, pav_mezanino.elevacao),
		secao_v_20x50,
		concreto,
		[pav_mezanino],	
		nome="V3")
	v4_mezanino = modelo.criar_viga(
		Ponto(p1.ponto_base.x, p1.ponto_base.y, pav_mezanino.elevacao),
		Ponto(p11.ponto_base.x, p11.ponto_base.y, pav_mezanino.elevacao),
		secao_v_20x50,
		concreto,
		[pav_mezanino],	
		nome="V4")
	v5_mezanino = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y, pav_mezanino.elevacao),
		Ponto(p13.ponto_base.x, p13.ponto_base.y, pav_mezanino.elevacao),
		secao_v_20x50,
		concreto,
		[pav_mezanino],	
		nome="V5")
	v6_mezanino = modelo.criar_viga(
		Ponto(p4.ponto_base.x, p4.ponto_base.y, pav_mezanino.elevacao),
		Ponto(p14.ponto_base.x, p14.ponto_base.y, pav_mezanino.elevacao),
		secao_v_20x50,
		concreto,
		[pav_mezanino],	
		nome="V6")

	# Vigas Terraço
	v1_terraco = modelo.criar_viga(
		Ponto(p1.ponto_base.x, p1.ponto_base.y+.1, pav_terraco.elevacao),
		Ponto(p4.ponto_base.x, p4.ponto_base.y+.2, pav_terraco.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terraco],	
		nome="V1")
	v2_terraco = modelo.criar_viga(
		Ponto(p6.ponto_base.x, p6.ponto_base.y-.2, pav_terraco.elevacao),
		Ponto(p7.ponto_base.x, p7.ponto_base.y, pav_terraco.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terraco],	
		nome="V2")
	v3_terraco = modelo.criar_viga(
		Ponto(p11.ponto_base.x, p11.ponto_base.y-.1, pav_terraco.elevacao),
		Ponto(p14.ponto_base.x, p14.ponto_base.y-.1, pav_terraco.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terraco],	
		nome="V3")
	v4_terraco = modelo.criar_viga(
		Ponto(p1.ponto_base.x, p1.ponto_base.y, pav_terraco.elevacao),
		Ponto(p11.ponto_base.x, p11.ponto_base.y, pav_terraco.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terraco],	
		nome="V4")
	v5_terraco = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y, pav_terraco.elevacao),
		Ponto(p13.ponto_base.x, p13.ponto_base.y, pav_terraco.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terraco],	
		nome="V5")
	v6_terraco = modelo.criar_viga(
		Ponto(p4.ponto_base.x, p4.ponto_base.y, pav_terraco.elevacao),
		Ponto(p14.ponto_base.x, p14.ponto_base.y, pav_terraco.elevacao),
		secao_v_20x50,
		concreto,
		[pav_terraco],	
		nome="V6")

	# Vigas Reservatório
	v1_reservatorio = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y+.2, pav_reservatorio.elevacao),
		Ponto(p4.ponto_base.x, p4.ponto_base.y+.2, pav_reservatorio.elevacao),
		secao_v_20x50,
		concreto,
		[pav_reservatorio],
		nome="V1")
	v2_reservatorio = modelo.criar_viga(
		Ponto(p6.ponto_base.x, p6.ponto_base.y-.2, pav_reservatorio.elevacao),
		Ponto(p7.ponto_base.x, p7.ponto_base.y, pav_reservatorio.elevacao),
		secao_v_20x50,
		concreto,
		[pav_reservatorio],
		nome="V2")
	v3_reservatorio = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y, pav_reservatorio.elevacao),
		Ponto(p6.ponto_base.x, p6.ponto_base.y, pav_reservatorio.elevacao),
		secao_v_20x50,
		concreto,
		[pav_reservatorio],
		nome="V3")
	v4_reservatorio = modelo.criar_viga(
		Ponto(p4.ponto_base.x, p4.ponto_base.y, pav_reservatorio.elevacao),
		Ponto(p7.ponto_base.x+.2, p7.ponto_base.y, pav_reservatorio.elevacao),
		secao_v_20x50,
		concreto,
		[pav_reservatorio],
		nome="V4")

	# Vigas Cobertura
	v1_cobertura = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y+.2, pav_cobertura.elevacao),
		Ponto(p4.ponto_base.x, p4.ponto_base.y+.2, pav_cobertura.elevacao),
		secao_v_20x30,
		concreto,
		[pav_cobertura],
		nome="V1")
	v2_cobertura = modelo.criar_viga(
		Ponto(p6.ponto_base.x, p6.ponto_base.y-.2, pav_cobertura.elevacao),
		Ponto(p7.ponto_base.x, p7.ponto_base.y, pav_cobertura.elevacao),
		secao_v_20x30,
		concreto,
		[pav_cobertura],
		nome="V2")
	v3_cobertura = modelo.criar_viga(
		Ponto(p3.ponto_base.x, p3.ponto_base.y, pav_cobertura.elevacao),
		Ponto(p6.ponto_base.x, p6.ponto_base.y, pav_cobertura.elevacao),
		secao_v_20x30,
		concreto,
		[pav_cobertura],
		nome="V3")
	v4_cobertura = modelo.criar_viga(
		Ponto(p4.ponto_base.x, p4.ponto_base.y, pav_cobertura.elevacao),
		Ponto(p7.ponto_base.x+.2, p7.ponto_base.y, pav_cobertura.elevacao),
		secao_v_20x30,
		concreto,
		[pav_cobertura],
		nome="V4")

	modelo.origem_grelha_no_primeiro_vertice = True

	# Lajes Mezanino
	l1_mezanino = modelo.criar_laje(
		pav_mezanino,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v5_mezanino.ponto_inicial.x, v1_mezanino.ponto_inicial.y, pav_mezanino.elevacao),
		 Ponto(v6_mezanino.ponto_inicial.x, v1_mezanino.ponto_final.y, pav_mezanino.elevacao),
		 Ponto(v6_mezanino.ponto_inicial.x, v2_mezanino.ponto_final.y, pav_mezanino.elevacao),
		 Ponto(v5_mezanino.ponto_inicial.x, v2_mezanino.ponto_inicial.y, pav_mezanino.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L1")
	l2_mezanino = modelo.criar_laje(
		pav_mezanino,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v5_mezanino.ponto_inicial.x, v2_mezanino.ponto_inicial.y, pav_mezanino.elevacao),
		 Ponto(v6_mezanino.ponto_inicial.x, v2_mezanino.ponto_final.y, pav_mezanino.elevacao),
		 Ponto(v6_mezanino.ponto_inicial.x, v3_mezanino.ponto_final.y, pav_mezanino.elevacao),
		 Ponto(v5_mezanino.ponto_inicial.x, v3_mezanino.ponto_final.y, pav_mezanino.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L2")
	l3_mezanino = modelo.criar_laje(
		pav_mezanino,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v2_mezanino.ponto_inicial.x, v2_mezanino.ponto_inicial.y, pav_mezanino.elevacao),
		 Ponto(v5_mezanino.ponto_inicial.x, v2_mezanino.ponto_final.y, pav_mezanino.elevacao),
		 Ponto(v5_mezanino.ponto_inicial.x, p9.ponto_base.y, pav_mezanino.elevacao),
		 Ponto(v2_mezanino.ponto_inicial.x, p9.ponto_base.y, pav_mezanino.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L3")

	# Lajes Terraço
	l1_terraco = modelo.criar_laje(
		pav_terraco,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v5_terraco.ponto_inicial.x, v1_terraco.ponto_inicial.y, pav_terraco.elevacao),
		 Ponto(v6_terraco.ponto_inicial.x, v1_terraco.ponto_final.y, pav_terraco.elevacao),
		 Ponto(v6_terraco.ponto_inicial.x, v2_terraco.ponto_final.y, pav_terraco.elevacao),
		 Ponto(v5_terraco.ponto_inicial.x, v2_terraco.ponto_inicial.y, pav_terraco.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L1")
	l2_terraco = modelo.criar_laje(
		pav_terraco,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v5_terraco.ponto_inicial.x, v2_terraco.ponto_inicial.y, pav_terraco.elevacao),
		 Ponto(v6_terraco.ponto_inicial.x, v2_terraco.ponto_final.y, pav_terraco.elevacao),
		 Ponto(v6_terraco.ponto_inicial.x, v3_terraco.ponto_final.y, pav_terraco.elevacao),
		 Ponto(v5_terraco.ponto_inicial.x, v3_terraco.ponto_final.y, pav_terraco.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L2")
	l3_terraco = modelo.criar_laje(
		pav_terraco,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v4_terraco.ponto_inicial.x, v1_terraco.ponto_inicial.y, pav_terraco.elevacao),
		 Ponto(v5_terraco.ponto_inicial.x, v1_terraco.ponto_final.y, pav_terraco.elevacao),
		 Ponto(v5_terraco.ponto_inicial.x, v3_terraco.ponto_final.y, pav_terraco.elevacao),
		 Ponto(v4_terraco.ponto_inicial.x, v3_terraco.ponto_final.y, pav_terraco.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L3")

	# Lajes Reservatório
	l1_reservatorio = modelo.criar_laje(
		pav_reservatorio,
		secao_g_10,
		concreto,
		(1.0,0.0,0.0),
		[Ponto(v3_reservatorio.ponto_inicial.x, v1_reservatorio.ponto_inicial.y, pav_reservatorio.elevacao),
		 Ponto(v4_reservatorio.ponto_inicial.x, v1_reservatorio.ponto_final.y, pav_reservatorio.elevacao),
		 Ponto(v4_reservatorio.ponto_inicial.x, v2_reservatorio.ponto_final.y, pav_reservatorio.elevacao),
		 Ponto(v3_reservatorio.ponto_inicial.x, v2_reservatorio.ponto_inicial.y, pav_reservatorio.elevacao)],
		secao_g_10.largura,
		secao_g_10.largura,
		"L1")

	modelo.montar()
	return modelo

if __name__ == "__main__":
	m1 = exemplo_portico_simples()
	print(f"Pórtico simples: {len(m1.pilares)} pilares, {len(m1.vigas)} vigas, {len(m1.pavimentos)} pavimentos")
	print(f"  ids: {[p.id for p in m1.pilares]}, nomes: {[p.nome for p in m1.pilares]}")
	print(f"  viga id/nome: {m1.vigas[0].id} / {m1.vigas[0].nome}")

	m2 = exemplo_viga_isolada_com_4_apoios()
	print(f"Viga isolada: {len(m2.vigas)} viga(s), {len(m2.vigas[0].restricoes)} restrições")
	print(f"  viga id/nome: {m2.vigas[0].id} / {m2.vigas[0].nome}")
	
	m3 = exemplo_edificio()
	print(f"Edifício: {len(m3.pilares)} pilares, {len(m3.vigas)} vigas, {len(m3.lajes)} laje(s)")
	for pilar in m3.pilares:
		print(f'Pilar: {pilar.nome}')
		print(f'\tNasce: {pilar.pavimento_base.nome} ({pilar.ponto_base.x},{pilar.ponto_base.y}) Desnível={pilar.desnivel_base}')
		print(f'\tMorre: {pilar.pavimento_topo.nome} ({pilar.ponto_topo.x},{pilar.ponto_topo.y}) Desnível={pilar.desnivel_topo}')
		print('\t\tLances:')
		for lance in pilar.lances:
			print(f'\t\t\t{lance.nome}: pavimento={lance.pavimento}')
	for viga in m3.vigas:
		print(f'Viga: {viga.nome}-{viga.pavimentos[0].nome}')
		print(f'\tVãos:')
		for vao in viga.vaos:
			print(f'\t\t{vao.nome} - i=({vao.no_inicial}) j=({vao.no_final})')
	for laje in m3.lajes:
		print(f'Laje: {laje.nome}-{laje.pavimento.nome}')
		print(f'\tContorno com {len(laje.apoios)} apoios')
		for apoio in laje.apoios:		
			print(f'\t\t{apoio.aresta} - Viga:{apoio.vao.viga.nome} Vão:{apoio.vao.nome}')

	saida = Path(__file__).parent / 'saida'
	saida.mkdir(exist_ok=True)

	exportador_dxf = ExportadorDxf()
	exportador_dxf.exportar(m3, str(saida / 'portico_barras.dxf'))
	exportador_dxf.exportar_solido(m3, str(saida / 'portico_solido.dxf'))
	for pav in m3.pavimentos:
		exportador_dxf.exportar_solido(m3, str(saida / f'{pav.nome}.dxf'), pav)

	ifc_writer = EscritorIfcManual()
	exportador_ifc = ExportadorIfc(m3, ifc_writer)
	exportador_ifc.exportar(str(saida / 'portico.ifc'))
	print(f'Arquivos gerados em: {saida}')
