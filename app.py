import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask


# Mapeamento dos meses
mapping_meses = {
    'janeiro': 0,
    'fevereiro': 1,
    'março': 2,
    'abril': 3,
    'maio': 4,
    'junho': 5,
    'julho': 6,
    'agosto': 7,
    'setembro': 8,
    'outubro': 9,
    'novembro': 10,
    'dezembro': 11
}

# função para pegar a "sopa", dado um html
def obter_html(url):
    print("Obtendo HTML de:", url)
    req = requests.get(url)
    html = req.content
    soup = BeautifulSoup(html, 'html.parser')
    return soup


# Dado um html, raspa os dados de uma célula específica
def raspar_dados_bioma(soup, row, col):
    print("Raspando dados do bioma...")
    celulas_coluna = soup.findAll('td', {'class': f'data row{row} col{col}'})
    valores_coluna = [celula.text.strip() for celula in celulas_coluna]
    return valores_coluna[0] if valores_coluna else None


# Função para encontrar a média e o recorde mensal
def encontrar_media_e_recorde_mensal(soup, mes_solicitado):
    print("Encontrando média e recorde mensal...")
    quantidade_linhas = 27
    
    if mes_solicitado.lower() in mapping_meses:
        mes_index = mapping_meses[mes_solicitado.lower()]

        # Encontrar as células da coluna específica do mês solicitado para calcular a média
        celulas_mensal = soup.findAll('td', {'class': f'data row28 col{mes_index}'})
        valores_mensal = [int(celula.text.strip()) for celula in celulas_mensal if celula.text.strip().isdigit()]  # Convertendo e filtrando valores inteiros

        # Calcular a média
        if valores_mensal:
            media_mensal = sum(valores_mensal) / len(valores_mensal)
            resultado_media = f'Média do mês - {int(media_mensal)} focos\n'

        # Encontrar o recorde de focos para o mês solicitado
        lista_mensal = []
        for y in range(quantidade_linhas):
            # Procurando, em todas as linhas, quais células da coluna têm o valor do recorde
            celulas_mensal = soup.findAll('td', {'class': f'data row{y} col{mes_index}'})
            valores_mensal = [int(celula.text.strip()) for celula in celulas_mensal if celula.text.strip().isdigit()]  # Convertendo e filtrando valores inteiros
            lista_mensal.extend(valores_mensal)

        # Calcular o recorde
        if lista_mensal:
            maior_valor_mensal = max(lista_mensal)
            ano_do_recorde_mensal = 1999 + lista_mensal.index(maior_valor_mensal)
            if mes_index >= 5:  # Se o mês for junho ou posterior, subtrai 1 do ano do recorde
                ano_do_recorde_mensal = ano_do_recorde_mensal - 1
            resultado_recorde = f'Recorde do mês - {maior_valor_mensal} focos (no ano {ano_do_recorde_mensal})\n'

        # Retornar tanto a média quanto o recorde
        return resultado_media, resultado_recorde


def enviar_email(focos_24h, acumulado_mes_atual_bioma, total_mesmo_mes_ano_passado_bioma, media, recorde):
    smtp_server = "smtp-relay.brevo.com"
    port = 587
    email = "marcoscony@gmail.com"
    password = "asFUfzSr8EN9R2HD"
    remetente = "marcoscony@gmail.com"
    destinatarios = ["marcoscony@gmail.com", 'marcos.acony@g.globo']
    titulo = "Teste de email"

    texto = f"""
    AMAZÔNIA - FOCOS DE INCÊNDIO

    24h - {focos_24h} focos
    Acumulado do mês atual - {acumulado_mes_atual_bioma} focos (vs {total_mesmo_mes_ano_passado_bioma} focos totais no mesmo mês do ano passado)
    {media}
    {recorde}
    """

    html = f"""
    <html>
      <body>
        <ul>
          <h2 style="color: #8B0000;"><b>AMAZÔNIA - FOCOS DE INCÊNDIO</b></h2>
          <li><b style="color: #555555;">24h</b> - {focos_24h} focos<br></li>
          <li><b style="color: #555555;">Acumulado do mês atual</b> - {acumulado_mes_atual_bioma} focos (vs {total_mesmo_mes_ano_passado_bioma} focos totais no mesmo mês do ano passado)<br></li>
          <li><b style="color: orange;">{media}</b><br></li>
          <li><b style="color: red;">{recorde}</b><br></li>
        </ul>
      </body>
    </html>
    """

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(email, password)

    mensagem = MIMEMultipart("alternative")
    mensagem["From"] = remetente
    mensagem["To"] = ",".join(destinatarios)
    mensagem["Subject"] = '🔥 FOCOS EM FOCO 🔍'
    conteudo_texto = MIMEText(texto, "plain")
    conteudo_html = MIMEText(html, "html")
    mensagem.attach(conteudo_texto)
    mensagem.attach(conteudo_html)

    print('Enviando e-mail')
    server.sendmail(remetente, destinatarios, mensagem.as_string())
    server.quit()

    print("E-mail enviado com sucesso.")


# Código que roda tudo
def run():
    print("Obtendo HTML da primeira URL...")
    url = 'http://terrabrasilis.dpi.inpe.br/queimadas/situacao-atual/media/bioma/grafico_historico_mes_atual_estado_amazonia.html'
    soup = obter_html(url)
    data_atual = datetime.now()
    dia_do_mes = data_atual.day
    focos_24h = raspar_dados_bioma(soup, 1, dia_do_mes - 2)
    acumulado_mes_atual_bioma = raspar_dados_bioma(soup, 1, 31)
    total_mesmo_mes_ano_passado_bioma = raspar_dados_bioma(soup, 0, 31)
    mes_atual = data_atual.month

    # Encontrar o nome do mês correspondente ao número do mês atual
    nome_mes_atual = None
    for mes, numero in mapping_meses.items():
        if numero == mes_atual - 1:  # Subtraímos 1 porque os meses em Python vão de 1 a 12
            nome_mes_atual = mes

    print("Obtendo HTML da segunda URL...")
    url2 = 'http://terrabrasilis.dpi.inpe.br/queimadas/situacao-atual/media//bioma/grafico_historico_estado_amazonia.html'
    soup = obter_html(url2)

    print('Executando função de média e recorde mensal')
    media, recorde = encontrar_media_e_recorde_mensal(soup, nome_mes_atual)
    print("Enviando email...")
    enviar_email(focos_24h, acumulado_mes_atual_bioma, total_mesmo_mes_ano_passado_bioma, media, recorde)
    return "E-mail enviado com sucesso."


app = Flask(__name__)

@app.route('/amazonia')
def amazonia():
    # Chama a função run
    return run()


if __name__ == '__main__':
    app.run(debug=True)