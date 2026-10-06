"""TAREFA DO ALUNO -- os cinco testes que faltam para os >= 8 do entregavel. 
 
Cada teste abaixo tem nome, docstring e um pytest.skip. Apague o skip, escreva o 
corpo, e o teste passa a valer. Nenhum deles precisa de banco: os tres primeiros 
rodam so contra o motor. 
""" 
 
from __future__ import annotations 
 
from decimal import Decimal 
 
import pytest 
 
 
def test_regressao_numerica_contra_a_planilha(fluxos_golden): 
    """Compara os seis indices com a aba SSB da Planilha_base.xlsx. 
 
    Criterio do entregavel: abs(delta) <= 1E-6 por indice. Comece pelo inventario 
    de referencia (Y = 200, F = 50, renovaveis = 115, nao renovaveis = 85) e 
    escreva os seis valores esperados a mao antes de rodar -- se o teste passar 
    de primeira sem voce saber o valor esperado, ele nao esta provando nada. 
    """ 
    from app.dominio.motor_emergia import calcular_indices

    resultado = calcular_indices(fluxos_golden, Decimal("1000"))

    esperado = {
        "y": Decimal("200.000000"),
        "eyr": Decimal("4.000000"),
        "elr": Decimal("0.739130"),
        "esi": Decimal("5.411765"),
        "eii": Decimal("0.184783"),
        "percentual_r": Decimal("57.500000"),
    }

    assert abs(resultado.y - esperado["y"]) <= Decimal("1E-6")
    assert abs(resultado.eyr - esperado["eyr"]) <= Decimal("1E-6")
    assert abs(resultado.elr - esperado["elr"]) <= Decimal("1E-6")
    assert abs(resultado.esi - esperado["esi"]) <= Decimal("1E-6")
    assert abs(resultado.eii - esperado["eii"]) <= Decimal("1E-6")
    assert abs(resultado.percentual_r - esperado["percentual_r"]) <= Decimal("1E-6")


def test_quantizacao_unica_no_final(): 
    """Mostra o erro duplo de arredondar no meio do calculo. 
 
    Calcule ESI = EYR / ELR de duas formas: (a) quantizando EYR e ELR para seis 
    casas antes de dividir; (b) dividindo em 28 digitos e quantizando so o ESI. 
    Os dois resultados diferem -- e o motor usa (b). Prove a diferenca. 
    """ 
    eyr = Decimal("4.0000004")
    elr = Decimal("0.7391304")

    esi_intermediario = (
        eyr.quantize(Decimal("1E-6"))
        / elr.quantize(Decimal("1E-6"))
    ).quantize(Decimal("1E-6"))

    esi_final = (eyr / elr).quantize(Decimal("1E-6"))

    assert esi_intermediario != esi_final


def test_ordem_da_soma_com_magnitudes_divergentes(): 
    """A associatividade quebra quando as magnitudes divergem. 
 
    Monte um inventario com um fluxo de 1E20 sej e outro de 1E-5 sej e some nas 
    duas ordens possiveis. Explique, no corpo do teste, por que a precisao de 28 
    digitos e o limite -- e por que ordenar o inventario e uma decisao de dominio. 
    """ 
    grande = Decimal("1E20")
    pequeno = Decimal("1E-5")

    soma_1 = grande + pequeno
    soma_2 = pequeno + grande

    assert soma_1 == soma_2
    assert soma_1 == Decimal("100000000000000000000.00001")


def test_erro_de_dominio_responde_problem_json(cliente, corpo_golden): 
    """Inventario sem fluxo renovavel deve sair 422 em application/problem+json. 
 
    Hoje sai 500, porque o handler de FluxosInsuficientes nao existe -- note que 
    o 404 e o 422 do framework JA saem no formato certo, pelos handlers do 
    esqueleto: o que falta e so o erro de dominio. Feche o TODO PASSO 3 em 
    app/main.py e depois assegure aqui: status 422, header content-type 
    application/problem+json e os cinco campos da RFC 9457. 
    """ 
    corpo = {
        **corpo_golden,
        "fluxos": [
            fluxo for fluxo in corpo_golden["fluxos"]
            if fluxo["categoria"] in {"N", "MN", "SN"}
        ],
    }

    resposta = cliente.post("/v1/safras/1/calculos", json=corpo)

    assert resposta.status_code == 422
    assert resposta.headers["content-type"] == "application/problem+json"

    dados = resposta.json()

    assert dados["type"] == "https://agroemergia.sc/erros/fluxos-insuficientes"
    assert dados["title"] == "Fluxos insuficientes"
    assert dados["status"] == 422
    assert "detail" in dados
    assert dados["instance"] == "/v1/safras/1/calculos"


def test_campo_extra_no_corpo_da_requisicao_e_rejeitado(cliente, corpo_golden): 
    """"energia_produto_jj" tem de morrer com 422, nao virar calculo incompleto. 
 
    Hoje o CalculoRequestDTO nao declara extra="forbid": o campo desconhecido e 
    ignorado e o typo passa silencioso, exatamente como na planilha. Feche o 
    TODO PASSO 3 em app/api/v1/dto.py e prove aqui. 
    """ 
    corpo = {
        **corpo_golden,
        "energia_produto_jj": "1000",
    }

    resposta = cliente.post("/v1/safras/1/calculos", json=corpo)

    assert resposta.status_code == 422
    assert resposta.headers["content-type"] == "application/problem+json"