# Créditos & Uso

## O padrão original

Este framework é um **fork e instanciação** do padrão **LLM Wiki**, criado por **Andrej Karpathy**:

- Gist original: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

O gist do Karpathy descreve a **ideia** de forma deliberadamente abstrata — uma wiki persistente mantida por LLM como alternativa ao RAG, com três camadas (fontes brutas / wiki / schema) e três operações (Ingest / Query / Lint). Ele encerra sugerindo que cada pessoa construa, junto com seu agente, uma versão que sirva ao seu contexto.

**Este repositório é essa versão construída** — uma instanciação madura, com os padrões de alimentadores (Ingest automatizado) e o ciclo de curadoria (Lint automatizado com gate humano) que não estão no gist abstrato.

> Os conceitos centrais (a ideia, as 3 camadas, as 3 operações, index/log) são do Karpathy. A instanciação, os padrões de alimentador, a régua de curadoria e o material deste repo são a contribuição deste fork.

## O padrão aberto de conformidade

A camada de conformidade descrita em [docs/05](docs/05-conformidade-okf.md) segue o **Open Knowledge Format (OKF)**, especificação aberta publicada em <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>. A especificação e seus termos são de seus autores; este repositório apenas documenta como uma wiki do framework nasce conformante com ela.

## Autoria do fork

Instanciação e documentação **by @caioxavier.ai**.

## Uso

Compartilhado livremente entre quem quiser usar. **Use à vontade, adapte ao seu contexto, crédito é apreciado.** Sem garantias — é um framework de referência, não um produto.
