from colorama import Fore, init
from iqoptionapi.stable_api import IQ_Option
import time
import concurrent.futures
import sys
import getpass
import collections
from datetime import datetime


init(autoreset=True)



def entrada_inicial(args):
    par, valor, direcao, duracao, entrada, delay  = args
    global binary
    global digital

    if par not in binary and par not in digital:
        print(Fore.YELLOW + horario() + ' Par ' + par + ' fechado em binário e digital')
    elif par in binary: # preferencia pra operacao binaria pq tem menos delay no gale
        operacao_binaria(par, valor, direcao, duracao, entrada, delay)
    else:
        operacao_digital(par, valor, direcao, duracao, entrada, delay)

    return


def operacao_binaria(par, valor, direcao, duracao, entrada, delay):
    lucro_local = 0
    global lucro_global
    global balance
    global api

    time.sleep(delay)  # espera o delay até a hora de fazer a entrada

    for i in range(gale + 1):
        status, id = api.buy(valor, par, direcao, duracao)  # timeframe em minutos, direcao em minusculo

        if not status:
            print(Fore.YELLOW + 'Falha na entrada | ' + str(entrada) + ' : ' + par + ' : ' + str(
                valor) + ' : ' + direcao + ' : M' + str(duracao))
            print(id)
            return
        else:
            if i == 0:
                print(yellow(horario()) + ' Entrada binária | ' + par + ' | ' + str(valor) + ' | ' + direcao + ' | M' + str(
                    duracao))
            elif i == 1:
                print(yellow(horario()) + red(' Gale 1') + ' | ' + par + ' | ' + str(valor) + ' | ' + direcao + ' | M' + str(
                    duracao))
            elif i == 2:
                print(yellow(horario()) + red(' Gale 2') + ' | ' + par + ' | ' + str(valor) + ' | ' + direcao + ' | M' + str(
                    duracao))

            resultado, lucro = api.check_win_v4(id)
            if lucro > 0:
                print(yellow(horario()) + green(' Win') + ' | ' + par + ' | Lucro: ' + green(
                    str(round(lucro, 2))) + ' | M' + str(duracao))
                lucro_local += valor
                check_stop(lucro_local)
                return
            elif lucro < 0:
                print(yellow(horario()) + red(' Lose') + ' | ' + par + ' | Perda: ' + red(
                    str(round(lucro, 2))) + ' | M' + str(duracao))
                valor = round(valor * 2, 2)
                lucro_local += lucro
            else:
                print(yellow(horario()) + ' Doji' + ' | ' + par + ' | Perda: ' + red(
                    str(round(lucro, 2))) + ' | M' + str(duracao))
                lucro_local += lucro
                check_stop(lucro_local)
                return

    check_stop(lucro_local)


def operacao_digital(par, valor, direcao, duracao, entrada, delay):
    lucro_local = 0
    global lucro_global
    global balance
    global api

    time.sleep(delay)  # espera o delay até a hora de fazer a entrada

    for i in range(gale + 1):
        check, id = api.buy_digital_spot(par, valor, direcao, duracao)  # timeframe em minutos, direcao em minusculo

        if not check:
            print(Fore.YELLOW + 'Falha na entrada | ' + str(entrada) + ' : ' + par + ' : ' + str(
                valor) + ' : ' + direcao + ' : M' + str(duracao))
            print(id)
            return
        else:
            if i == 0:
                print(yellow(horario()) + ' Entrada digital | ' + par + ' | ' + str(valor) + ' | ' + direcao + ' | M' + str(
                    duracao))
            elif i == 1:
                print(yellow(horario()) + red(' Gale 1') + ' | ' + par + ' | ' + str(valor) + ' | ' + direcao + ' | M' + str(
                    duracao))
            elif i == 2:
                print(yellow(horario()) + red(' Gale 2') + ' | ' + par + ' | ' + str(valor) + ' | ' + direcao + ' | M' + str(
                    duracao))

            while True:
                status, lucro = api.check_win_digital_v2(id)

                if status:
                    if lucro > 0:
                        print(yellow(horario()) + green(' Win') + ' | ' + par + ' | Lucro: ' + green(
                            str(round(lucro, 2))) + ' | M' + str(duracao))
                        lucro_local += valor
                        check_stop(lucro_local)
                        return
                    else:
                        print(yellow(horario()) + red(' Lose') + ' | ' + par + ' | Perda: ' + red(
                            str(round(lucro, 2))) + ' | M' + str(duracao))
                        valor = round(valor * 2, 2)
                        lucro_local += valor
                        break

    check_stop(lucro_local)


def ler_lista() -> object:
    with open('sinais.txt', 'r') as f:
        linhas = f.readlines() # lê todas as linhas do arquivo

    lista = {}
    for i in range(len(linhas)):
        lista[i] = linhas[i].split(";") # separa cada linha pelo ';'
        lista[i][0] = lista[i][0].replace('M', '') # retira o M dos indicadores de duracao ('M15' -> '15')
        if lista[i][3] == 'CALL\n' or lista[i][3] == 'CALL \n': # retira quebras de linha e espaços vazios
            lista[i][3] = 'CALL'
        elif lista[i][3] == 'PUT\n' or lista[i][3] == 'PUT \n':
            lista[i][3] = 'PUT'

    lista_ordenada = collections.OrderedDict(sorted(lista.items(), key=lambda kv: kv[1][2])) # ordena a lista de acordo com o horario (ex: lista[0][2] = 01:00 < lista[1][2] = 01:30)

    return lista_ordenada


def run_at(hora) -> object: # calcula o delay entre a hora de entrada e o horário atual, menos o delay do usuário
    agora = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              '%Y-%m-%d %H:%M:%S')  # formata o horario atual para y:m:d h:m:s (string) e depois volta para datetime
    entrada = str(datetime.now())[:10] + ' ' + hora + ':00'  # ano, mes e dia + espaço + horario da lista de sinais (hora e minuto) + segundos (que é sempre 00)
    return entrada, (datetime.strptime(entrada, '%Y-%m-%d %H:%M:%S') - agora).total_seconds() - float(
        delay_usuario) / 1000


def next_3_min(entrada) -> bool:  # verifica se o horário de entrada está dentro dos próximos 3 minutos
    hora_entrada = datetime.strptime(entrada, '%Y-%m-%d %H:%M:%S')
    hora_agora = datetime.strptime(str(datetime.now())[:-7], '%Y-%m-%d %H:%M:%S')

    if 0 < (hora_entrada - hora_agora).total_seconds() <= 180:
        return True
    else:
        return False


def horario() -> str:
    return str(datetime.now())[10:-7] # retorna o horário formatado em %H:%M:%S


def red(t) -> str:
    return Fore.RED + t + Fore.RESET # retorna a string com a cor aplicada nela e o reset de cor logo após


def green(t) -> str:
    return Fore.GREEN + t + Fore.RESET # retorna a string com a cor aplicada nela e o reset de cor logo após


def yellow(t) -> str:
    return Fore.YELLOW + t + Fore.RESET # retorna a string com a cor aplicada nela e o reset de cor logo após


def update_pares_abertos():
    global binary
    global digital
    global api

    par = api.get_all_open_time() # pega todos os pares (isso demora uns 3-5 segundos pra retornar)
    for paridade in par['binary']:
        if par['binary'][paridade]['open'] == True and paridade not in binary:
            binary.append(paridade) # caso o par esteja aberto e ainda nao esteja na lista...
        if par['binary'][paridade]['open'] == False and paridade in binary:
            binary.pop(binary.index(paridade)) # caso o par esteja fechado e esteja na lista

    for paridade in par['digital']:
        if par['digital'][paridade]['open'] == True and paridade not in digital:
            digital.append(paridade)
        if par['digital'][paridade]['open'] == False and paridade in digital:
            digital.pop(digital.index(paridade))


def check_stop(valor):
    global lucro_global
    global balance

    lucro_global += valor
    print(yellow(horario()) + ' Lucro atual: ' + (green(str(lucro_global)) if lucro_global > 0 else red(str(lucro_global))))

    if lucro_global >= .15*balance : # 15% stopwin
        print(Fore.YELLOW + ' Stopwin batido :)')
        input('Presssione ENTER para sair\n')
        sys.exit()
    elif lucro_global <= -abs(.15*balance): # 15% stoploss
        print(Fore.YELLOW + ' Stoploss batido :(')
        input('Presssione ENTER para sair\n')
        sys.exit()


if __name__ == "__main__":
    # api = IQ_Option('email', 'password')
    api = IQ_Option(input(' Email: '), getpass.getpass(prompt=' Senha: ')) # esconde a senha no terminal, mas nao funciona no terminal do pycharm
    api.connect()

    print()

    if not api.check_connect():
        print(yellow(horario()) + ' Falha ao se conectar')
        input('Presssione ENTER para sair\n')
        sys.exit()
    else:
        print(yellow(horario()) + ' Conectado com sucesso')
        print(yellow(horario()) + ' Carregando configurações...')
        api.change_balance('PRACTICE')


    binary = [] # lista de ativos binarios abertos
    digital = [] # lista de ativos digitais abertos
    balance = api.get_balance()  # banca
    lucro_global = 0 # pra checar os stop
    lista = ler_lista() # lista de sinais

    print()
    print(yellow(horario()) + ' Porcentagem da banca como entrada (ex 1.5): ', end='')
    valor = round(float(input())/100*balance, 2)
    print(yellow(horario()) + ' Delay até o servidor (milissegundos): ', end = '')
    delay_usuario = int(input())
    print(yellow(horario()) + ' Quantidade de gales da lista: ', end = '')
    gale = int(input())

    # valor = round(balance*.05, 2)
    # delay_usuario = 2500
    # gale = 1

    print()
    print(yellow(horario()) + ' Banca inicial: ' + str(balance))
    print(yellow(horario()) + ' Valor das entradas: ' + str(valor))
    print()

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:  # multithreading

        delay = []  # lista de delays entre o horario atual e o horario da entrada
        entradas = {} #lista de dados das entradas
        results = [] # retorno das threads

        i = 0 # index da lista delay (pega todos os delays independentemente de faltar pouco tempo ou o tempo já ter passado
        j = 0 # index da lista de entradas (só pega as informações das entradas válidas)
        for l in lista:
            entrada, d = run_at(lista[l][2]) # horario de entrada e delay em segundos
            delay.append(d)

            if 10 > delay[i] > 0: # se faltar 10 segundos ou menos pra entrada
                print(yellow(horario()) + ' Falha na entrada, horário muito próximo | ' + str(entrada) + ' | ' + lista[l][1] + ' | ' + str(
                        valor) + ' | ' + str(lista[l][3]) + ' | M' + str(lista[l][0]))
            elif delay[i] >= 10:
                entradas[j] = [lista[l][1], valor, lista[l][3], int(lista[l][0]), entrada] #lista de argumentos das entradas cadastradas (DELAY NAO É INSERIDO AQUI)
                print(
                    yellow(horario()) + ' Entrada cadastrada | ' + str(entrada) + ' | ' + lista[l][1] + ' | ' + str(
                        valor) + ' | ' + str(lista[l][3]) + ' | M' + str(lista[l][0]))
                j = j+1

            i = i+1

        print()

        entradas_popadas = 0 # nao sei explicar direito, sem isso o "i" do loop de entradas nao vai funcionar pq o tamanho da lista diminui enquanto o index da entrada aumenta, eventualmente nao da pra acessar a entrada e para de funcionar
        while len(entradas) > 0:
            update_pares_abertos()
            for i in range(entradas_popadas, len(entradas)+entradas_popadas):
                try: # para cada entrada, verifica se o horário dela está dentro dos próximos 3 minutos
                    if next_3_min(entradas[i][4]): # caso esteja, adiciona o delay atualizado na lista de entradas (de AGORA até a entrada)
                        entradas[i].append(run_at(str(entradas[i][4])[11:-3])[1])
                        results.append(executor.submit(entrada_inicial, entradas[i])) # cria a thread para a entrada
                        entradas.pop(i) # tira a entrada da lista
                        entradas_popadas += 1 # incrementa entradas popadas pra nao dar erro de index mais tarde
                except:
                    pass

            time.sleep(10) # vai testar umas 4 vezes a cada minuto, é o suficiente

        print()

        for f in concurrent.futures.as_completed(results): # printa se tiver alguma coisa no return das threads
            return_value = f.result()
            if return_value is not None:
                print(f.return_value)

    input('Pressione ENTER para sair\n')
