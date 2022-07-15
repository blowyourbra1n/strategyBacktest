import csv
from time import sleep
from art import tprint
import time
#SETTINGS

#
printPerm = True

# список монет для анализа, можно оставить одну, или проверить сразу много
token_list = ['ETH']

# количество сигналов (начиная с конца), 0 если не нужен
nLastSygnals = 10

# шаг выставления ордера
orderStep = 2

# торговое плечо
leverage = 5

# 0-100 процентов
balancePartTuple = [50]
balancePart = 50

# условный стартовый баланс
startBalance = 100

#тейк-профит в процентах, выставить 0, если не используется
takeProfit = 5

#тейк-профит в процентах, выставить 0, если не используется
stopLoss = 1

#fees true or false
fees = True

# 
#/SETTINGS

def start():

	for el in token_list:
		bestBalance = 0
		csvfileJapanBars = f'clearJapan/{el} J.csv'
		csvfileHiekenAshi = f'clearHieken/{el} H.csv'
		list_pos, all_data = get_data_from_csv(csvfileJapanBars, csvfileHiekenAshi)

		backtest(
					list_pos, 
					all_data,
					token = el, 
					orderStep = orderStep, 
					leverage = leverage, 
					balancePart = balancePart, 
					takeProfit = takeProfit, 
					stopLoss = stopLoss,
					printPerm = True
		)

		# for leverage in range(5,11):
		# 	for orderStep in range(1, 4):
		# 		for balancePart in balancePartTuple:
		# 			for takeProfit in range(1,5):
		# 				for stopLoss in range(1,5):
		# 					balance, orderStep, leverage, balancePart, takeProfit, stopLoss = backtest(
		# 							list_pos, 
		# 							all_data, 
		# 							token = el,
		# 							orderStep = orderStep, 
		# 							leverage = leverage, 
		# 							balancePart = balancePart, 
		# 							takeProfit = takeProfit, 
		# 							stopLoss = stopLoss,
		# 							printPerm = False
		# 							)



		# 					if balance > bestBalance:
		# 						bestBalance = balance
		# 						bestLeverage = leverage
		# 						bestOrderStep = orderStep
		# 						bestBalancePart = balancePart
		# 						bestTakeProfit = takeProfit
		# 						bestStopLoss = stopLoss


		# backtest(
		# 	list_pos, 
		# 	all_data,
		# 	token = el, 
		# 	orderStep = bestOrderStep, 
		# 	leverage = bestLeverage, 
		# 	balancePart = bestBalancePart, 
		# 	takeProfit = bestTakeProfit, 
		# 	stopLoss = bestStopLoss,
		# 	printPerm = True
		# )
					
def backtest(list_pos, all_data, token, orderStep, leverage, balancePart, takeProfit, stopLoss, printPerm):
	countSygnals, orderHit, marginCall, balance, tpCount, slCount = place_order(list_pos, all_data, orderStep, leverage, balancePart, takeProfit, stopLoss)

	if printPerm:
		print(f'Монета: {token}\n'+
			f'Первый сигнал: {(list_pos[-nLastSygnals]["date"].split(" ")[0].replace("-","month ")+"day")}\n'+
			f'Общее количество сигналов: {countSygnals}\n'+
			f'Шаг ордера: {orderStep} %\n'+
			f'Ордеров сработало: {orderHit}\n'+
			f'Плечо: {leverage} X\n'+
			f'Процент от баланса: {balancePart}%\n'+
			f'Комиссия с учетом плеча: {round((0.07*leverage), 3)}%\n'+
			f'Ликвидации: {marginCall}\n'+
			f'Количество тейк-профитов {takeProfit}%: {tpCount}\n'+
			f'Количество стоп-лоссов {stopLoss}%: {slCount}\n'+
			f'Итоговый баланс: {round(balance, 1)}$\n'
			f'Множитель баланса: {round((balance/100),3)} X\n\n'
			)

	return balance, orderStep, leverage, balancePart, takeProfit, stopLoss

def get_data_from_csv(csvfileJapanBars, csvfileHiekenAshi):
	all_data = []
	list_pos = []

	with open(csvfileJapanBars, newline='') as csvfile:
		spamreaderJapan = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in spamreaderJapan:
			row = ', '.join(row).split(',')
			date = row[0].split('+03:00')[0].split('2022-')[-1].replace('T', ' ')
			date = date.split('2021-')[-1]
			priceHigh = row[2]
			priceLow = row[3]
			priceClose = row[4]
			dictAllData = {'date':date, 'high':priceHigh, 'low':priceLow, 'close':priceClose}
			all_data.append(dictAllData)
	all_data = all_data[1:len(all_data)]

	with open(csvfileHiekenAshi, newline='') as csvfile:
		spamreaderHieken = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in spamreaderHieken:
			row = ', '.join(row).split(',')
			dateHieken = row[0].split('+03:00')[0].split('2022-')[-1].replace('T', ' ')
			dateHieken = dateHieken.split('2021-')[-1]
			sideSellHieken = row[5]
			sideBuyHieken = row[6]
			if sideBuyHieken != '0' or sideSellHieken != '0':
				for el in all_data:
					if el['date'] == dateHieken:

						if sideBuyHieken == '1':
							dictHieken = {'date': el['date'], 'high':el['high'], 'low': el['low'], 'close':el['close'], 'side':'Buy'}
							list_pos.append(dictHieken)
						elif sideSellHieken == '1':
							dictHieken = {'date': el['date'], 'high':el['high'], 'low': el['low'], 'close':el['close'], 'side':'Sell'}
							list_pos.append(dictHieken)

	if nLastSygnals != 0:
			list_pos = list_pos[len(list_pos)-nLastSygnals:len(list_pos)]

	return list_pos, all_data

def place_order(list_pos, all_data, orderStep, leverage, balancePart, takeProfit, stopLoss):

	try:

		#const
		countSygnals = 0
		n = 0
		orderHit = 0
		marginCall = 0
		balance = startBalance
		tpCount = 0
		slCount = 0
		newStart = 0
		#/const

		for sygnal in list_pos:
			countSygnals += 1


			#get current sygnal info:
			dateSygnal = sygnal['date']
			sideSygnal = sygnal['side']
			priceSygnal = sygnal['close']
			#/get current sygnal info

			#get next sygnal info:
			n += 1
			dateNextSygnal = list_pos[n]['date']
			sideNextSygnal = list_pos[n]['side']
			priceNextSygnal = list_pos[n]['close']
			#/get next sygnal info

			#where start point in all_data:
			start = 0
			for data in all_data:
				#check start:
				if data['date'] == dateSygnal:
					start += 1
					break
				else:
					start += 1
			#/where start point in all_data

			#where end point in all_data:
			end = 0
			for data in all_data:
				#check end:
				if data['date'] == dateNextSygnal:
					end += 1
					break
				else:
					end += 1
			#/where end point in all_data


			#place order with step
			dataStartToEnd = all_data[start:end] # вот тут я нахожу диапазон пути сигнала
			for price in dataStartToEnd:

				if sideSygnal == 'Buy':
					orderPrice = float(priceSygnal)*((100-orderStep)/100)
					if float(price['low']) <= orderPrice:
						orderHit +=1 # количество успешных ордеров
						orderTrigger = True
						PNL = float(all_data[end]['close'])/orderPrice # получение базового пнл
						print(f'{sygnal} сработал {price} а сигнал длился до {dateNextSygnal}')
						break
					else:
						orderTrigger = False


				elif sideSygnal == 'Sell':
					orderPrice = float(priceSygnal)*((100+orderStep)/100)
					if float(price['high']) >= orderPrice:
						orderHit +=1 # количество успешных ордеров
						PNL = orderPrice/float(all_data[end]['close']) # получение базового пнл
						orderTrigger = True
						print(f'{sygnal} сработал {price} а сигнал длился до {dateNextSygnal}')
					else:
						orderTrigger = False


				if orderTrigger:
					#where start point in all_data:
					start = 0
					for data in dataStartToEnd:
						#check start:
						if data['date'] == price['date']:
							start += 1
							break
						else:
							start += 1
					#/where start point in all_data

					dataStartToEnd = dataStartToEnd[start:end]
					print(f'{dataStartToEnd}\n\n')		
					

	except IndexError:
		countSygnals -= 1
		return countSygnals, orderHit, marginCall, balance, tpCount, slCount

if __name__ == '__main__':
	start()