# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [0.1.0] - 2026-10-10

### Adicionado

- Modelagem de pórticos espaciais: Pilares, Vigas e Lajes por coordenadas, amarrados a Pavimentos.
- Detecção de interseções Viga × Pilar (pilar vertical), Viga × Viga e apoio de Laje em Vão.
- Derivação automática de Lances, Vãos, Apoios e Links em `ModeloPortico.montar()`.
- Laje como grelha, com coeficientes de carga por nó.
- Concreto conforme a NBR 6118.
- Exportadores DXF 3D (linhas e sólidos) e IFC4 (camadas analítica e física, GUIDs determinísticos).
- Empacotamento com `pyproject.toml` (layout `src/`), extras `[dxf]` e `[dev]`.
- Exemplo em `examples/`, testes com pytest e CI no GitHub Actions.
