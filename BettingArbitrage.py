from gevent.pool import Pool
from gevent import monkey

monkey.patch_all()

import time, logging, sys, linecache, random
import undetected_chromedriver as uc
from tkinter import *
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse

class ArbFinder(object):
    def __init__(self, URL):
        try:
            self.sport = 'Tennis'
            self.driver = uc.Chrome(version_main=149)
            self.driver.implicitly_wait(5)
            self.driver.get(URL)
            # self.driver.set_window_size(800, 600)
        except:
            print(f"Error initializing ArbFinder {URL}")

class App(object):
    def __init__(self):
        self.num_threads = 2
        self.pool = Pool(self.num_threads)

        self.bid = ArbFinder('https://www.snai.it/scommesse-live/sport/tennis')
        self.bid.driver.implicitly_wait(5)

        self.ask = ArbFinder('https://www.eurobet.it/it/scommesse-live/tennis')
        self.ask.driver.implicitly_wait(5)

        self.running = False
        self.bet_amount = 100
        self.tot_profit = 0

    def findBidList(self):
        self.bid.results = self.bid.driver.find_elements(By.XPATH,
                        "//div[contains(@class,'grid_mg-row-wrapper') and .//a[contains(@href,'/scommesse-live/evento/tennis/')]]")

        for i, res in enumerate(self.bid.results):
            try:
                # 1. Find teams
                xpath_teams = res.find_elements(By.XPATH, ".//a[contains(@href,'/scommesse-live/evento/tennis/')]//span[contains(@class,'tw-fr-capitalize') and contains(@class,'tw-fr-truncate')]")
                if len(xpath_teams) < 2:
                    continue 

                team1_bid, team2_bid = \
                    xpath_teams[0].text.strip(), \
                    xpath_teams[1].text.strip()
                team1_bid = team1_bid.split(',')[0].strip() if ',' in team1_bid else team1_bid.split(' ')[-1]
                team2_bid = team2_bid.split(',')[0].strip() if ',' in team2_bid else team2_bid.split(' ')[-1]

                # 2. Find wagers
                try:
                    team1_wager, team2_wager = \
                        res.find_element(By.XPATH, ".//button[contains(@data-qa,'_20540_0_1')]//span").text.strip(), \
                        res.find_element(By.XPATH, ".//button[contains(@data-qa,'_20540_0_2')]//span").text.strip()
                except Exception:
                    continue 
            
                if (team1_wager == '' or  team2_wager == ''):
                    continue
                
                team1_wager, team2_wager = \
                    round(float(team1_wager), 2), round(float(team2_wager), 2)

                self.bid_dict[team1_bid.lower() + " vs " + team2_bid.lower()] = \
                                [team1_wager,
                                team2_wager,
                                team1_bid,
                                team2_bid]
            except StaleElementReferenceException:
                continue

    def findAskList(self):
        self.ask.results = self.ask.driver.find_elements(By.XPATH,
                        "//div[contains(@class,'bet-hub__row') and .//a[contains(@class,'bet-hub__players')]]")

        for i, res in enumerate(self.ask.results):
            try:
                # 1. Find teams
                xpath_teams = res.find_elements(By.XPATH, ".//a[contains(@class,'bet-hub__players')]//div[contains(@class,'bet-hub__player-home') or contains(@class,'bet-hub__player-away')]")
                if len(xpath_teams) < 2:
                    continue 

                team1_ask, team2_ask = \
                    xpath_teams[0].text.strip(), \
                    xpath_teams[1].text.strip()
                team1_ask, team2_ask = \
                    team1_ask.split(' ')[0], \
                    team2_ask.split(' ')[0]

                xpath_wagers = res.find_elements(By.XPATH, ".//div[contains(@class,'odds__col--default')]//div[contains(@class,'odds__footer')]")
                if len(xpath_wagers) < 2:
                    continue

                # 2. Find wagers
                team1_wager, team2_wager = \
                    xpath_wagers[0].text.strip(), \
                    xpath_wagers[1].text.strip()
                
                if (team1_wager == '' or  team2_wager == ''):
                    continue

                team1_wager, team2_wager = \
                    round(float(team1_wager), 2), round(float(team2_wager), 2)
                
                self.ask_dict[team1_ask.lower() + " vs " + team2_ask.lower()] = \
                                [team1_wager,
                                team2_wager,
                                team1_ask,
                                team2_ask]
            except StaleElementReferenceException:
                continue
            
    def selectWager(self, ask_or_bid, bet, looper=None):

        website = self.bid if (ask_or_bid == "BID") else self.ask
        xml_path = "//div[contains(@class,'grid_mg-row-wrapper') and .//a[contains(@href,'/scommesse-live/evento/tennis/')] and contains(.,'" +\
                        bet[1][2] + "') and contains(.,'" +\
                        bet[1][3] + "')]//button[contains(@data-qa,'" + ('_20540_0_1' if looper == 0 else '_20540_0_2') + "')]"\
                        if (ask_or_bid == "BID") else \
                        "//div[contains(@class,'bet-hub__row') and .//a[contains(@class,'bet-hub__players')] and contains(.,'" +\
                        bet[0][2] + "') and contains(.,'" +\
                        bet[0][3] + "')]//div[contains(@class,'odds__col--default')]//div[contains(@class,'odds__item')]"


        wager = website.driver.find_element(By.XPATH, xml_path) if (ask_or_bid == "BID")\
                else website.driver.find_elements(By.XPATH, xml_path)[looper]

        website.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wager)
        website.driver.execute_script("arguments[0].click();", wager)
            

    def submitBid(self, ask_or_bid, stake):
        try:
            website = self.bid if (ask_or_bid == "BID") else self.ask
            print(f"{ask_or_bid} - {urlparse(website.driver.current_url).netloc.split('.')[-2]}: {stake}")
            xpath = "//*[@data-qa='biglietto_puntata']" if (ask_or_bid == "BID") else "//input[contains(@class,'counter__input')]"

            self.bet_input = website.driver.find_element(By.XPATH, xpath)
            stake_formatted = f"{stake:.2f}".replace('.', ',')

            website.driver.execute_script("""
                const input = arguments[0];
                const value = arguments[1];
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(input, '');
                input.dispatchEvent(new Event('input', { bubbles: true }));
                nativeSetter.call(input, value);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.blur();
            """, self.bet_input, stake_formatted)
        except NoSuchElementException as ex:
            # print(f"[submitBid] element not found: {ex}")
            print(f"[submitBid] {ask_or_bid} didn't go through ...")
        except StaleElementReferenceException as ex:
            # print(f"[submitBid] element went stale: {ex}")
            print(f"[submitBid] {ask_or_bid} didn't go through ...")
        except Exception as ex:
            print(f"[submitBid] unexpected error: {type(ex).__name__}: {ex}")


    def checkArbitrage(self, prob_ask, prob_bid):
        return True if (prob_ask + prob_bid < 1) else False
    
    def emptyBids(self):
        try:
            for elem in self.bid.driver.find_elements(By.XPATH, "//button[.//span[contains(text(),'Svuota tutto')]]"):
                            elem.click()
            for elem in self.ask.driver.find_elements(By.XPATH, "//div[contains(@class,'betslip__options-btn')][.//span[contains(text(),'Elimina tutto')]]"):
                            elem.click()
                            time.sleep(2)  # hope it's rendered by now
                            si_button = self.ask.driver.find_element(By.XPATH, "//div[contains(@class,'modals__container')]//button[contains(@class,'modals__btn-primary') and normalize-space(text())='Si']")
                            si_button.click()
        except:
            print(f"[emptyBids] error:")

    def arbitrage(self):
        # 1. if running, then start checks
        # 2. create threads to find bets on each website
        # 3. find common bets
        # 4. for each common bet, find if there is arbitrage
        # 5. if arbitrage, 
        #   5.1. select wager and add it to schedina
        #   5.2. compute and enter stake
        #   5.3. submit bid and clear schedina

        try:
            if self.running:
                self.bid_dict, self.ask_dict, self.shared_keys, self.common_bets = \
                    dict(), dict(), None, None

                self.pool.apply_async(self.findAskList)
                self.pool.apply_async(self.findBidList)
                # Join the pools so they run in parallel
                self.pool.join()

                self.shared_keys = self.ask_dict.keys() & self.bid_dict.keys()
                self.common_bets = {k: [self.ask_dict[k], self.bid_dict[k]] for k in self.shared_keys}

                for key in self.common_bets:
                    bet = self.common_bets[key]

                    for i in range(2):
                        implied_prob_ask = 1/bet[0][i]
                        implied_prob_bid = 1/bet[1][1-i]
                        is_arbitrage = self.checkArbitrage(implied_prob_ask, implied_prob_bid)

                        if is_arbitrage:
                            stake_ask, stake_bid = \
                                self.bet_amount * implied_prob_ask/(implied_prob_ask + implied_prob_bid), \
                                self.bet_amount * implied_prob_bid/(implied_prob_ask + implied_prob_bid)

                            print(f"Betting {stake_ask} on {bet[0][i+2]} at {bet[0][i]} - {stake_bid} on {bet[1][2+i]} at {bet[1][1-i]}")

                            self.pool.apply_async(self.selectWager, args=("ASK", bet, i))
                            self.pool.apply_async(self.selectWager, args=("BID", bet))
                            # Join the pools so they run in parallel
                            self.pool.join()

                            self.pool.apply_async(self.submitBid, args=("ASK", stake_ask))
                            self.pool.apply_async(self.submitBid, args=("BID", stake_bid))
                            # Join the pools so they run in parallel
                            self.pool.join()

                            profit = (stake_ask*bet[0][i] + stake_bid*bet[1][1-i] \
                                            - 2*self.bet_amount)/2
                            self.tot_profit += profit
                            print(f"profit: {profit} - tot profit: {self.tot_profit}")

                            self.emptyBids()

                            time.sleep(60 * random.randint(1, 1))
        except Exception as ex:
            print(f"[Exception]: {ex}")

        self.root.after(1, self.arbitrage)    
    

    def start(self):
        self.running = True
        print("Start scanning bids")

    def stop(self):
        self.running = False
        print("Stopping...")

    def addToBid(self):
        self.submitBid("BID", 5)
        return

    def addToAsk(self):
        self.submitBid("ASK", 5)
        return

    def run(self):
        self.root = Tk()
        self.root.title("Arb Finder")
        self.root.geometry("420x200")

        app = Frame(self.root)
        app.grid()

        start = Button(app, text="Start", command=self.start)
        stop = Button(app, text="Stop", command=self.stop)
        start.grid(row=0, column=0, padx=(40, 40), pady=(40, 40))
        stop.grid(row=0, column=1, padx=(40, 40), pady=(40, 40))

        # btn_frame = Frame(self.root)
        # btn_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # add_btn = Button(btn_frame, text=f"+5 EUR", width=10, command=self.addToBid)
        # sub_btn = Button(btn_frame, text=f"-5 EUR", width=10, command=self.addToAsk)
        # empty_btn = Button(btn_frame, text=f"empty", width=10, command=self.emptyBids)
        # add_btn.pack(side=LEFT, padx=5)
        # sub_btn.pack(side=LEFT, padx=5)
        # empty_btn.pack(side=LEFT, padx=5)

        self.root.after(1, self.arbitrage)  # After 1 second, call scanning
        self.root.mainloop()
        
app = App()
app.run()

