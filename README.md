# Domínios .br

Código escrito em Python para encontrar domínios .br em textos. O arquivo `tld_br.py` implementa:

- A função `br_tlds`, que acessa [a página de categorias de domínios do
  registro.br](https://registro.br/dominio/categorias/) e devolve dados estruturados dos TLDs .br
- A função `br_domain_tld_regexp` gera um padrão de expressões regulares em Python (a partir dos TLDs obtidos pela
  função acima) que encontra domínios .br em um texto (de acordo com as [regras do domínio definidas pelo
  registro.br](https://registro.br/dominio/regras/), incluindo caracteres acentuados)
- A classe `BRDomainMatcher` extrai domínios .br de textos, devolvendo o domínio encontrado e o TLD correspondente
- Uma interface de linha de comando (CLI) que possui os seguintes subcomandos (use `python br_tlds.py subcomando
  --help` para mais detalhes):
  - `python br_tlds.py download <arquivo.csv>`: baixa, extrai e salva os TLDs disponíveis
  - `python br_tlds.py filter`: filtra o texto vindo da entrada padrão (stdin) e mostra na saída padrão (stdout) os
    domínios .br encontrados. Exemplo: `cat arquivo.html | python br_tlds.py filter --encoding=utf-8 > resultados.txt`

O script `domains-wikipedia-pt.sh` é um exemplo de utilzação onde o conteúdo da Wikipédia em Português é baixado e são
feitos filtros para determinar quais os domínios .br mais citados (no fim, um CSV é gerado com as contagens).

## Instalando

```shell
git clone https://github.com/turicas/dominios.br
cd dominios.br
pip install -r requirements.txt
```

## Links relevantes

- RDAP registro.br: <https://rdap.registro.br/domain/xxx>
- Domínios em processo de liberação: <https://registro.br/dominio/lista-processo-liberacao.txt>
