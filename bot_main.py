from kucoin.client import Client
from keys import getKeys
import yaml
import time
from datetime import datetime
import requests
import json
import os
import sys
from matplotlib import pyplot as plt
import matplotlib.dates
import pandas as pd

moneyAxis = []
lastCheck = int(time.mktime(datetime.now().timetuple()))
def sendPackage(telegramAPI,chatID,tradeMessage,portfolioMessage,assetMessage):
    sendMessage(telegramAPI,chatID,tradeMessage)
    if portfolioMessage is not None:
        sendMessage(telegramAPI,chatID,portfolioMessage)
    sendMessage(telegramAPI,chatID,assetMessage)
offset = None
def pollCommand(telegramAPI,chatID,tradeMessage,portfolioMessage,assetMessage):
    global lastCheck
    try:
        updateURL = "https://api.telegram.org/bot"+str(telegramAPI)+"/getUpdates"
        global offset
        if(offset!=None):
            updateURL += "?offset="+offset
            # print(offset)
        response = requests.get(updateURL, timeout=5)
        # print(response.status_code)
        updateInfo = response.content.decode("utf-8")
        updateInfo = json.loads(updateInfo)
        commandList = updateInfo['result']
        # print("Last message",commandList[len(commandList)-1]["message"]["date"])
        for item in commandList:
            try:
                if(item["message"]["date"]>lastCheck):
                    print("Received:",item["message"]["text"], item["message"]["date"])
                    # exit()
                    # print(botResponses(item["message"]["text"]))
                    messageText = item["message"]["text"].lower()
                    # print(botIdentifier)
                    # print(messageText)
                    if botIdentifier in messageText:
                        messageText = messageText.replace(botIdentifier,"")
                        print("Parsed:",messageText)
                        if ("hi" in messageText) or ("hello" in messageText):
                            sendPackage(telegramAPI,chatID,tradeMessage,portfolioMessage,assetMessage)
                        elif "help" in messageText:
                            helpMessage = "KucoinBot will notify of any rebalances that occurs. \n" + botIdentifier +"help for this message. \n"+botIdentifier+"hi or "+botIdentifier+"hello to get an update manually."
                            helpMessage += "\n"+botIdentifier+"restart or"+botIdentifier+"reboot to restart the bot"
                            # helpMessage += "\n"+botIdentifier+"portfolio [tokenA:proportion,tokenA:proportion] to update portfolio"
                            helpMessage += "\n"+botIdentifier+"rebalanceRatio:Ratio to update rebalance Ratio"
                            helpMessage += "\n"+botIdentifier+"chart to display the balance chart"
                            sendMessage(telegramAPI,chatID,helpMessage)
                        elif ("restart" in messageText) or ("reboot" in messageText):
                            sendMessage(telegramAPI,chatID,"Restarting bot...")
                            time.sleep(1)
                            os.execl(sys.executable, sys.executable, *sys.argv)
                        elif "rebalanceratio" in messageText:
                            try:
                                newRatio = float(messageText.replace("rebalanceratio:",""))
                                # print(newRatio)
                                try:
                                    file = open("config.yml", "r")
                                    newFile = ""
                                    for line in file:
                                        # line = line.strip()
                                        if ("rebalanceRatio" in line):
                                            newFile += "rebalanceRatio: "+str(newRatio)+"\n"
                                            oldRatio = line.replace("rebalanceRatio: ","")
                                        else:
                                            newFile += line
                                    file.close()
                                    fout = open("config.yml", "w")
                                    fout.write(newFile)
                                    fout.close()
                                    rebalanceMessage = "Rebalance ratio changed from " + str(oldRatio) + " to " + str(newRatio)
                                    sendMessage(telegramAPI,chatID,rebalanceMessage)
                                    sendMessage(telegramAPI,chatID,"Restarting bot...")
                                    time.sleep(1)
                                    os.execl(sys.executable, sys.executable, *sys.argv)
                                except Exception as e:
                                    # print(e)
                                    # print("Failed to update config file.")
                                    sendMessage(telegramAPI,chatID,e)
                            except:
                                rebalanceError = str(messageText)+"\n"+r"\rebalanceRatio command invalid format"
                                sendMessage(telegramAPI,chatID,r"\rebalanceRatio command invalid format")
                                # return 0
                        elif "chart" in messageText:
                            # https://api.telegram.org/bot5066081530:AAFmNOcqwAvHeHCzSlPt8PLKrvnnejRECsc/sendChatAction?chat_id=-582136934&action=upload_photo
                            actionURL = "https://api.telegram.org/bot"+str(telegramAPI)+"/sendMessage?chat_id="+str(chatID)+"&action=upload_photo"
                            requests.get(actionURL)
                            # make the chart here
                            # img = open("gura.png", 'rb')
                            df = pd.DataFrame(moneyAxis)
                            # print(df)
                            plt.figure(1)
                            plt.tight_layout()
                            for key in moneyAxis[0]:
                                if key != 'time':
                                    plt.plot(df['time'],df[key],label=key)
                                    # print(key)
                            plt.ylabel('Value in USDT')
                            plt.xlabel('Time')
                            plt.title('KucoinBot Assets')
                            plt.legend()
                            plt.savefig('chart.png')
                            plt.close()
                            img = open("chart.png", 'rb')
                            photoURL = "https://api.telegram.org/bot"+str(telegramAPI)+"/sendPhoto?chat_id="+str(chatID)
                            photoStatus = requests.post(photoURL, files={'photo':img})
                            # print(photoStatus)
                            if photoStatus.status_code == 200:
                                pass
                            else:
                                sendMessage(telegramAPI,chatID,"Failed to send chart")
                        else:
                            unknownMessage = "I don't understand: " + messageText
                            sendMessage(telegramAPI,chatID,unknownMessage)
                    lastCheck = int(time.mktime(datetime.now().timetuple()))
                    offset = str(item["update_id"])
            except Exception as e:
                print(e)
                offset = str(int(item["update_id"])+1)
                print("Cannot parse:",offset)
            offset = str(int(item["update_id"])+1)
    except Exception as e:
        print("pollCommand failed")
        print(e)

def sendMessage(telegramAPI,chatID,message):
    try:
        sendURL = "https://api.telegram.org/bot"+str(telegramAPI)+"/sendMessage?chat_id="+str(chatID)+"&text="+message
        requests.get(sendURL)
    except:
        print("Send message failed")

def error(update, context):
    print(f"Update {update} caused {context.error}")

config = yaml.safe_load(open('config.yml'))
configPackage = "Config: "
if config is None:
    print('Config file is invalid')
    # exit()
    configPackage += '\nConfig file is invalid'
else:
    # Check target portfolio
    portfolioSum = 0
    try:
        portfolio = config['portfolio']
        print("Target Portfolio:")
        configPackage += '\nTarget Portfolio'
        for key in portfolio:
            print(key, ' : ', portfolio[key])
            configPackage += "\n"+str(key) + " : " +str(portfolio[key])
            portfolioSum += round(float(portfolio[key]),2)
            if (round(float(portfolio[key]),2) == 0) or (portfolio[key] is None):
                raise Exception()
    except:
        print('Portfolio not found in config or is invalid.')
        configPackage += '\nPortfolio not found in config or is invalid.'
    if(portfolioSum!=100):
        print("Portfolio does not equal to 100.")
        configPackage += '\nPortfolio does not equal to 100.'
    try:
        mode = config['mode'] # sandbox, sandbox_futures, main, futures
        print("Mode:",mode)
        configPackage += '\nMode: '+str(mode)
    except:
        print('mode not found in config.')
        configPackage += '\nmode not found in config.'
        # exit()

    try:
        rebalanceRatio = round(float(config['rebalanceRatio']),2)
        print("rebalanceRatio is",str(rebalanceRatio)+"%")
        configPackage += '\nrebalanceRatio is '+str(rebalanceRatio)+"%"
    except:
        print("rebalanceRatio not found in config.")
        configPackage += '\nrebalanceRatio not found in config.'
        # exit()

    try:
        telegramAPI = config['telegramAPI']
        print("telegramAPI:",telegramAPI)
        configPackage += '\ntelegramAPI: '+str(telegramAPI)

    except:
        print("telegramAPI is invalid.")
        configPackage += '\ntelegramAPI is invalid.'
    try:
        chatID = config['chatID']
        print("chatID:",chatID)
        configPackage += '\nchatID: '+str(chatID)
    except:
        print("chatID is invalid")
        configPackage += '\nchatID is invalid'

    try:
        sleepTimer = int(config['sleepTimer'])
        print("sleepTimer is",str(sleepTimer)+" seconds")
        configPackage += "\nsleepTimer is "+str(sleepTimer)+" seconds"
    except:
        print("sleepTimer not found in config.")
        configPackage += "\nsleepTimer not found in config"
        # exit()
    try:
        botIdentifier = str(config['botIdentifier'])
        print("botIdentifier is:",botIdentifier)
        configPackage += "\nbotIdentifier is: " + str(botIdentifier)
    except:
        print("botIdentifier not found in config.")
        configPackage += "\nbotIdentifier not found in config"
        # exit()
if(getKeys(mode)==-1):
    raise Exception('Invalid mode.')
    configPackage += "\nInvalid mode"
else:
    api_key, api_secret, api_passphrase, sandbox_key = getKeys(mode)
rebalanceCount = 0
startingMoney = 0
sendUpdate = False
sendMessage(telegramAPI,chatID,configPackage)
# print(configPackage)
# exit()
# print("Would you like to start bot with these settings? (y/n) ")
# sendMessage(telegramAPI,chatID,"Would you like to start bot with these settings? (y/n) ")
while(True):
    val = "y"
    print("val:",val)
    if(val=="n"):
        # sendMessage(telegramAPI,chatID,"Would you like to change config?")
        # exit()
        pass
    elif(val=="y"):
        start=datetime.now()
        sendUpdate = True
        try:
            welcomeMessage = "Bot started at "+str(start).split(".")[0]
            sendMessage(telegramAPI,chatID,welcomeMessage)
        except Exception as e:
            print("Starting telegram bot failed.")

        client = Client(api_key, api_secret, api_passphrase, sandbox=sandbox_key)

        # Check portfolio currencies on kucoin
        for item in portfolio:
            # print("Checking: ", item)
            try:
                client.get_currency(item)
            except Exception as e:
                raise SystemExit(e)
        print("Portfolio check done. All coins are found on kucoin.")
        while(True):
            try:
                accounts = client.get_accounts()
                # print(accounts)
                tempAssets = []
                USDTTotal = 0
                print("")
                print("Trade Account:")
                moneyAxisDict = {}
                for item in accounts:
                    # print(item)
                    if(item['type']=='trade'):
                        if(float(item['balance']) > 0.1):
                            # for key in item:
                            #     print(key, ' : ', item[key])
                            # print('ID: ', item['id'])
                            # print(item['currency'], end=' : ')
                            coin = item['currency']
                            pair = item['currency'] + '-USDT'
                            # print(item['currency'])
                            if(item['currency'] == "USDT"):
                                USDTPrice = float(item['balance'])
                                tempAssets.append([coin,USDTPrice,1,1])
                            else:
                                ticker = client.get_ticker(pair)
                                USDTPrice = round(float(ticker['bestBid'])* float(item['balance']),2)
                                tempAssets.append([coin,USDTPrice,float(ticker['bestAsk']),float(ticker['bestBid'])])
                            moneyAxisDict[item['currency']] = USDTPrice
                            USDTTotal += USDTPrice
                # print(tradeMessage)
                # exit()
                assets=[]
                tradeMessage = "Trade Account:"
                for item in tempAssets:
                    ratio = round((item[1]/USDTTotal)*100,2)
                    # print(ratio)
                    item.append(ratio)
                    assets.append(item)
                    print(item[0], ": $", item[1],"-", str(item[4])+"%")
                    print("Ask:",item[2],"Bid:",item[3])
                    tradeMessage += "\n"+str(item[0])+" : $ "+str(item[1]) + " - " + str(item[4])+"%"+"\nAsk: "+str(item[2])+" Bid: "+str(item[3])
                # print(tradeMessage)
                # exit()
                # print(assets)
                print("Total: $", USDTTotal)
                tradeMessage += "\nTotal: $" + str(USDTTotal)
                if(startingMoney==0):
                    startingMoney = USDTTotal
                print("")
                portfolioMessage = None
                print("Portfolio status:")
                rebalanceCheck = False
                for key in portfolio:
                    keyFound = False
                    for item in tempAssets:
                        if(key in item):
                            keyFound = True
                            currentRatio = item[4]
                            targetRatio = portfolio[key]
                            diffRatio = round(currentRatio - targetRatio,4)
                            print(item[0], str(currentRatio)+"%", "vs", str(targetRatio)+"%", "diff:", str(diffRatio)+"%")
                            if(abs(diffRatio)>=rebalanceRatio) and (key!="USDT"):
                                if portfolioMessage is None:
                                    portfolioMessage = ("Portfolio status:")
                                rebalanceCheck = True
                                USDTValue = abs(diffRatio)*USDTTotal/100
                                pair = key + '-USDT'
                                if(item[0]!="USDT"):
                                    if(diffRatio<0):
                                        # orderSize = round(float(USDTValue/item[2]),6)
                                        # Increase buy order size by still buying according best bid instead of bet ask
                                        orderSize = round(float(USDTValue/item[3]),4)
                                        # print("Buy $"+str(USDTValue)+" of", key)
                                        print("Buy",orderSize,key,"at $"+str(round(float(item[2]),6)))
                                        portfolioMessage += "\nBuy $" + str(round(USDTValue,4)) + " of "+str(key)
                                        portfolioMessage += "\n" + "Buy " + str(orderSize) + " " + str(key) +" at $"+ str(round(float(item[2]),8))
                                        try:
                                            order = client.create_market_order(pair, Client.SIDE_BUY, size=orderSize)
                                            time.sleep(1)
                                            orderInfo = client.get_order(order['orderId'])
                                            print("Effective buy price:", round(float(orderInfo['dealFunds'])/float(orderInfo['dealSize']),4))
                                        except:
                                            print("Market order failed")
                                    else:
                                        orderSize = round(float(USDTValue/item[3]),4)
                                        # print("Sell $"+str(USDTValue)+" of", key)
                                        print("Sell",orderSize,key,"at $"+str(round(float(item[3]),6)))
                                        portfolioMessage += "\nSell $" + str(round(USDTValue,4)) + " of "+str(key)
                                        portfolioMessage += "\n" + "Sell " + str(orderSize) + " " + str(key) +" at $"+ str(round(float(item[3]),8))
                                        try:
                                            order = client.create_market_order(pair, Client.SIDE_SELL, size=orderSize)
                                            time.sleep(1)
                                            orderInfo = client.get_order(order['orderId'])
                                            print("Effective sell price:", round(float(orderInfo['dealFunds'])/float(orderInfo['dealSize']),4))
                                        except:
                                            print("Market order failed")
                            # print("Current USDT value:", item[1])
                            # print("Target USDT value:", round(USDTTotal*portfolio[key]/100,2))
                    if keyFound is False:
                        if portfolioMessage is None:
                            portfolioMessage = ("Portfolio status:")
                        rebalanceCheck = True
                        currentRatio = 0
                        targetRatio = portfolio[key]
                        diffRatio = round(currentRatio - targetRatio,2)
                        print(key, "0% vs", str(portfolio[key])+"%", "diff:", str(diffRatio)+"%")
                        if(abs(diffRatio)>=rebalanceRatio) and (key!="USDT"):
                            USDTValue = abs(diffRatio)*USDTTotal/100
                            pair = key + '-USDT'
                            if(key!="USDT"):
                                # print(key)
                                if(diffRatio<0):
                                    # orderSize = round(float(USDTValue/item[2]),6)
                                    # Increase buy order size by still buying according best bid instead of bet ask
                                    orderSize = round(float(USDTValue/item[3]),4)
                                    # print("Buy $"+str(USDTValue)+" of", key)
                                    print("Buy",orderSize,key,"at $"+str(round(float(item[2]),6)))
                                    portfolioMessage += "\nBuy $" + str(round(USDTValue,4)) + " of "+str(key)
                                    portfolioMessage += "\n" + "Buy " + str(orderSize) + " " + str(key) +" at $"+ str(round(float(item[2]),8))
                                    try:
                                        order = client.create_market_order(pair, Client.SIDE_BUY, size=orderSize)
                                        time.sleep(1)
                                        orderInfo = client.get_order(order['orderId'])
                                        print("Effective buy price:", round(float(orderInfo['dealFunds'])/float(orderInfo['dealSize']),4))
                                    except:
                                        print("Market order failed")
                                else:
                                    orderSize = round(float(USDTValue/item[3]),4)
                                    # print("Sell $"+str(USDTValue)+" of", key)
                                    print("Sell",orderSize,key,"at $"+str(round(float(item[3]),6)))
                                    portfolioMessage += "\nSell $" + str(round(USDTValue,4)) + " of "+str(key)
                                    portfolioMessage += "\n" + "Sell " + str(orderSize) + " " + str(key) +" at $"+ str(round(float(item[3]),8))
                                    try:
                                        order = client.create_market_order(pair, Client.SIDE_SELL, size=orderSize)
                                        time.sleep(1)
                                        orderInfo = client.get_order(order['orderId'])
                                        print("Effective sell price:", round(float(orderInfo['dealFunds'])/float(orderInfo['dealSize']),4))
                                    except:
                                        print("Market order failed")
                        # print("Current USDT value: 0")
                        # print("Target USDT value:", round(USDTTotal*portfolio[key]/100,2))
                if rebalanceCheck is True:
                    sendUpdate = True
                    rebalanceCount += 1
                    portfolioMessage += "\nRebalance triggered"
                    print("Rebalance triggered")
                else:
                    print("No rebalance necessary")

                print("")
                print("Starting assets:",startingMoney)
                print("Current assets:",USDTTotal,end=" ")
                profitPercentage = round(((USDTTotal - startingMoney)/startingMoney)*100,2)
                print("("+str(profitPercentage)+"%)")
                print("Total rebalances:",rebalanceCount)
                currentTime = datetime.now()
                runTime = datetime.now()-start
                print("Total runtime:",runTime)
                assetMessage = "Starting assets: " + str(startingMoney) + "\nCurrent assets: " + str(USDTTotal) + " ("+str(profitPercentage)+"%)"
                assetMessage += "\nTotal rebalances: " + str(rebalanceCount) + "\nTotal runtime: "+str(runTime)
                if sendUpdate is True:
                    sendUpdate = False
                #     sendMessage(telegramAPI,chatID,tradeMessage)
                #     if portfolioMessage is not None:
                #         sendMessage(telegramAPI,chatID,portfolioMessage)
                #     sendMessage(telegramAPI,chatID,assetMessage)
                    sendPackage(telegramAPI,chatID,tradeMessage,portfolioMessage,assetMessage)
                moneyAxisDict['time'] = currentTime
                moneyAxis.append(moneyAxisDict)

                # plt.show()
                print("\nSleeping for",sleepTimer,"seconds.")
                # time.sleep(sleepTimer)
                sleepTime = 0
                while(sleepTime<sleepTimer):
                    time.sleep(0.5)
                    sleepTime += 0.5
                    pollCommand(telegramAPI,chatID,tradeMessage,portfolioMessage,assetMessage)
                print("Done sleeping")
            except Exception as e:
                print(e)
                print("Error in main loop.")
    else:
        pass
