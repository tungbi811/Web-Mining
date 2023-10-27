import re
import os
import time
import selenium
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

hightlight_script = """
    // Define the highlighted_texts array and a flag for capturing in the global context
    window.highlighted_texts = [];
    window.isCapturing = true;
    var currentText = "dat22";
    var label = 0;  // Variable to store the pressed number

    document.addEventListener('keydown', function(event) {
        if (event.key === 'd') {
            var highlightedText = window.getSelection().toString().trim();
            if (highlightedText !== '') {
                var highlightedItem = {
                    'label': label,
                    'text': currentText
                };
                window.highlighted_texts.push(highlightedItem);
                console.log('Highlighted text added:', highlightedItem);
            }
        }

        if (event.key === 'a') {
            var element = document.querySelectorAll(":hover");
            var lastElement = element[element.length - 1]; 
            var textContent = lastElement.innerText;
            currentText = textContent;
            console.log('Current text retrieved:', currentText);
        }

        if(event.key === 's') {
            // Save the currentText to the list of highlighted texts
            var highlightedItem = {
                'text': currentText,
                'label': label
            };
            window.highlighted_texts.push(highlightedItem);
            console.log(highlightedItem['text'] + ' has label ' + highlightedItem['label'] + ' is saved');
         }
        
        if (event.key >= '0' && event.key <= '9') {
            // Store the pressed number in the label variable
            label = event.key;
            console.log('Label set to:', label);
        }

        if (event.key === 'f') {
            console.log('Highlighted_texts_array:', JSON.stringify(window.highlighted_texts));
        }

        if(event.key === 'q') {
            // Stop capturing when 'q' is pressed
            window.isCapturing = false;
        }
    });
"""

get_text_script = """
    var allText = '';
    function getText(element) {
        if (element) {
            var innerText = element.innerText;
            if (innerText && innerText.trim() !== "") {
                allText += innerText.trim() + '\\n';
            }
            var children = element.children;
            for (var i = 0; i < children.length; i++) {
                getText(children[i]);
            }
        }
    }
    getText(document.body);
    return allText;
"""

class Crawler:
    def __init__(self) -> None:
        service = Service(executable_path='chromedriver.exe')
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless=new')
        # options.add_argument("--auto-open-devtools-for-tabs")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)

    def scrape_web(self, link):
        try:
            self.driver.get(link)
            self.driver.maximize_window()
        except:
            print("Cannot connect to web!", link)
            return None

        # Scrape all text from the website
        all_text = self.driver.execute_script(get_text_script)
        all_text = all_text.split('\n')
        all_text = [re.sub('\t', '', text) for text in all_text]
        all_text = [text.strip() for text in all_text if text.strip() not in ['', ' ']]
        all_text = [text for text in all_text if len(text)<50]
        all_text = list(set(all_text))

        # Get label
        self.driver.execute_script(hightlight_script)

        while True:
            # Retrieve whether capturing is ongoing from JavaScript console
            isCapturing = self.driver.execute_script("return isCapturing;")
            if isCapturing:
                time.sleep(0.1)
            else:
                # Capture is complete, retrieve the highlighted texts
                highlighted_texts = self.driver.execute_script("return highlighted_texts;")
                if highlighted_texts == []:
                    return None
                items = {}
                for item in highlighted_texts:
                    items[item['text']] = item['label']

                data = {}
                for text in all_text:
                    if text in items.keys():
                        data[text] = "SRV"
                    else:
                        data[text] = "O"
                return data

    def label_save_data(self, csv_file, last_page):
        folder = './business'
        os.makedirs(folder, exist_ok=True)

        df = pd.read_csv(csv_file, index_col=0)
        df = df.dropna(subset=['Company Website']).reset_index(drop=True)

        for i in range(last_page, len(df)):
            print(i)
            company_name = df.iloc[i][0]
            company_web = df.iloc[i][1]
            
            if company_web.endswith('jp'):
                print(company_web)
                continue

            if 'http' not in company_web:
                company_web = f'https://{company_web}' 

            if f'{company_name}.txt' in os.listdir(folder):
                continue

            data = self.scrape_web(company_web)

            if data is None:
                continue
            else:
                company_file = os.path.join(folder,company_name+'.txt')
                
                if os.path.isfile(company_file):
                    continue
                else:
                    f = open(company_file , 'w', encoding='utf-8')

                    for k, v in data.items():
                        f.write(k+'\t'+v+'\n')
                
if __name__ == "__main__":
    crawler = Crawler()
    # data = crawler.scrape_web('https://www.qsoft.com/')
    # print(data)
    crawler.label_save_data('1.csv', 25)