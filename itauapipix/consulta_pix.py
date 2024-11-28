import env_itauapipix as env
from itauapipix.itau_api_pix import ItauClient


def pega_lista_pix(credentials, dthr_ini, dthr_fim):

    client = ItauClient.from_credentials(
        **credentials
    )

    resp = client.received_pixs(dthr_ini, dthr_fim)

    return resp.json()


def trata_resp_pix(json_resp):
    dados_pix = []
    for pix in json_resp['pix']:
        dados = {
            'valor': pix['valor'],
            'horario': pix['horario'],
            'id': pix['endToEndId'],
            'msg': pix.get('infoPagador', ''),
        }
        #pagador = pix['chave']
        #dados['cpf/cnpj'] = pagador.get('cnpj', pagador.get('cpf'))
        #dados['nome'] = pagador.get('nome')

        dados_pix.append(dados)

    return dados_pix


def consuta_pix(credentials, dthr_ini, dthr_fim):
    resp_json = pega_lista_pix(credentials, dthr_ini, dthr_fim)
    dados = trata_resp_pix(resp_json)
    return dados


if __name__ == '__main__':
    from pprint import pprint


    def teste01():
        dthr_ini = '2024-11-20T00:00:01Z'
        dthr_fim = '2024-11-27T23:59:59Z'
        key_credentials = 'coralli'

        credentials = env.credenciais[key_credentials]

        dados = consuta_pix(credentials, dthr_ini, dthr_fim)

        pprint(dados)

    teste01()