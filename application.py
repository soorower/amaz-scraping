from ssl import SSLSocket
from flask import Flask, request, send_from_directory, render_template
from threading import Thread
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

application = Flask(__name__)

status_text = "not running"

def middleof(text, left,right,multi=False):
    if(not multi):
        try:
            middle = text.split(left)[1].split(right)[0]
            return middle
        except:
            return ""
    else:
        right_text=text
        items=[]
        while(True):
            try:
                item = right_text.split(left)[1].split(right)[0]
                items.append(item)
                right_text = right_text.split(left,1)[1].split(right,1)[1]
            except:
                break
        return items


def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def remove_numbers(inputString):
    return ''.join(i for i in inputString if not i.isdigit())

def get_only_numbers(inputString):
    return ''.join(i for i in inputString if i.isdigit())

def categorize_address(address_list):
    categorized_address = ["","","","","",""]
    for_development = ['Strasse','haus','stadt','bundesh','plz','land']

    if (len(address_list) > 3 and len(address_list) < 7):
        try:
            if (not has_numbers(address_list[-1].text)):
                categorized_address[5] = address_list[-1].text
        except:
            pass

        try:
            if (address_list[-2].text.isnumeric()):
                categorized_address[4] = address_list[-2].text
        except:
            pass


        if (has_numbers(address_list[0].text)):
            try:
                categorized_address[0] = remove_numbers(address_list[0].text)
            except:
                pass
            try:
                categorized_address[1] = get_only_numbers(address_list[0].text)
            except:
                pass
            try:
                categorized_address[2] = address_list[1].text
            except:
                pass
        else:
            try:
                categorized_address[0] = address_list[0].text
            except:
                pass
            try:
                if (address_list[1].text.isnumeric()):
                    categorized_address[1] = address_list[1].text
            except:
                pass
            if (len(address_list) > 5):
                try:
                    categorized_address[2] = address_list[-4].text
                except:
                    pass
                try:
                    categorized_address[3] = address_list[-3].text
                except:
                    pass

    return categorized_address

category_mother_category_name_dic = {}
category_mother_category_url_dic = {}
checked_child_url_list = []

def find_child_urls(url):
    try:
        print("find_child_urls()")
        url = url.split('/ref=')[0]

        global checked_child_url_list
        if(url in checked_child_url_list):
            print("This url already checked. Skipping.")
            return []
        checked_child_url_list.append(url)

        child_url = 'http://api.scraperapi.com?api_key=e59b5548e36da5aadaab906ac45d9743&url=' + url
        r = requests.get(child_url)
        soup = BeautifulSoup(r.content,'html.parser')

        mother_category_name = soup.find('title').text.strip().split('in')[1].strip()
        print(mother_category_name)
        print(url)
        category_mother_category_name_dic[url] = mother_category_name
        category_mother_category_url_dic[url] = url
        try:
            collected_urls = []
            child_link_box = soup.find('div',attrs ={'role':'group'}).findAll('div')
            for child_link in child_link_box:
                child_link ='https://www.amazon.de' + str(child_link.find('a')['href'])
                collected_urls.append(child_link)
            status_text = 'Scraping the child category urls...'
        except:
            collected_urls = [url]
            status_text = f'You have used a child url instead of a mother url. This url does not have any child. Scraping this category..{url}'

        return collected_urls
    except Exception as e:
        print("Issue in method >>> find_child_urls -> "+str(e))
        return []


item_category_name_dic = {}
item_category_url_dic = {}

def get_bestsellers_items(url):
    try:
        best_seller_item_urls = []

        for i in range(1,4):

            category_name = ""
            for h in range(1,5): # trying for several times
                try:
                    print("get_bestsellers_items try: "+str(h))
                    page_url = url + '?ie=UTF8&pg='+str(i)
                    print("Getting items from bestseller page -----> "+page_url)
                    page_url = 'http://api.scraperapi.com?api_key=e59b5548e36da5aadaab906ac45d9743&url=' + page_url
                    
                    try:
                        response = requests.get(page_url)
                        print(response)
                    except:
                        print("issue in response, moving to next")
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')
                    # import pyperclip
                    # pyperclip.copy(str(soup))
                    category_name = soup.find('title').text.strip().split('in')[1].strip()
                    break
                except:
                    continue


            for item in soup.find_all('a', class_='a-link-normal a-text-normal'):
                item_url = 'https://www.amazon.de' + item['href'].split('/ref=')[0]
                item_category_name_dic[item_url] = category_name
                item_category_url_dic[item_url] = page_url
                best_seller_item_urls.append(item_url)

        print("best_seller_item_urls count: "+str(len(best_seller_item_urls)))
        return best_seller_item_urls

    except Exception as e:
        print("Issue in method >>> get_bestsellers_items -> "+str(e))
        return []


def get_item_details(url):
    try:
        item_dic = {}
        print("# Getting item details from: " + url)

        for z in range(1, 11):
            print("try: " + str(z))
            each_item_url = 'http://api.scraperapi.com?api_key=e59b5548e36da5aadaab906ac45d9743&url=' + url
            response = requests.get(each_item_url)
            print(response)
            if (response.status_code == 200):
                break

        soup = BeautifulSoup(response.text, 'html.parser')

        item_dic["product_url"]=url

        try:
            product_name = soup.find('span', {"id": "productTitle"}).text.strip()
            item_dic["product_name"] = product_name
        except:
            pass

        try:
            store_name = soup.find('a', {"id": "bylineInfo"}).text.strip()
            item_dic["store_name"] = store_name
        except:
            pass

        try:
            sold_by = soup.find('div', {"id": "merchant-info"}).a.span.text.strip()
            item_dic["sold_by"] = sold_by
        except:
            pass

        try:
            olp_text_box_text = soup.find('div', {"class":"olp-text-box"}).span.text
            item_dic["product_seller_amount"] = middleof(olp_text_box_text,'(',')').strip()

        except:
            item_dic["product_seller_amount"] = "1"

        try:
            product_rating_amount = soup.find('span', {"id": "acrCustomerReviewText"}).text.strip().split(" ")[0]
            item_dic["product_rating_amount"] = product_rating_amount
        except:
            pass

        try:
            item_dic["product_rating"] = soup.find("span", {"class":"reviewCountTextLinkedHistogram"})["title"].split(" ")[0]
        except:
            pass

        try:
            item_dic["asin"] = url.split('dp/')[-1].strip()
        except:
            pass

        try:
            product_details_tech_table_rows = soup.find('table', {"id":"productDetails_techSpec_section_1"}).find_all('tr')
            for row in product_details_tech_table_rows:
                if(row.th.text.strip()=="Marke"):
                    item_dic["marke"] = row.td.text.strip().replace('\u200e','')
                if (row.th.text.strip() == "Hersteller"):
                    item_dic["product_creator"] = row.td.text.strip().replace('\u200e', '')

        except:
            pass

        try:
            product_details_zus_table_rows = soup.find('table', {"id": "productDetails_detailBullets_sections1"}).find_all('tr')
            for row in product_details_zus_table_rows:
                # if (row.th.text.strip() == "ASIN"):
                #     try:
                #         item_dic["asin"] = row.td.text.strip()
                #     except:
                #         pass
                if (row.th.text.strip() == "Im Angebot von Amazon.de seit"):
                    try:
                        item_dic["product_online_since"] = row.td.text.strip()
                    except:
                        pass
                if (row.th.text.strip() == "Amazon Bestseller-Rang"):
                    try:
                        soup_temp = BeautifulSoup(str(row.td.span), 'html.parser')
                        bestseller_spans = soup_temp.find('span').find_all('span')
                        try:
                            bestseller_1 = bestseller_spans[0].text.split(" in ")
                            item_dic["bestseller_rank_name_1"] = bestseller_1[1].split(" ")[0]
                            item_dic["bestseller_ranking_1"] = bestseller_1[0].split(" ")[-1]
                        except:
                            pass

                        try:
                            bestseller_2 = bestseller_spans[1].text.split(" in ")
                            item_dic["bestseller_rank_name_2"] = bestseller_2[1].split(" ")[0]
                            item_dic["bestseller_ranking_2"] = bestseller_2[0].split(" ")[-1]
                        except:
                            pass
                    except:
                       pass
        except:
            pass

        item_dic['profile_url'] = ""
        try:
            item_dic['profile_url'] = "https://www.amazon.de" + soup.find('div', {"id": "merchant-info"}).a['href']
        except:
            pass


        if(item_dic['profile_url'] != ""):
            print(" *** This item has profile url, getting data from it: "+item_dic['profile_url'])

            for t in range(1,11):
                print("Try: "+str(t))
                seller_profile_link = 'http://api.scraperapi.com?api_key=e59b5548e36da5aadaab906ac45d9743&url=' + item_dic['profile_url']
                response = requests.get(seller_profile_link)
                print(response)

                soup_prof = BeautifulSoup(response.text, 'html.parser')

                try:
                    item_dic['profile_name'] = soup_prof.find('h1', {'id':'sellerName'}).text.strip()
                    break
                except:
                    pass


            try:
                item_dic['profile_image'] = soup_prof.find('img', {'id': 'sellerLogo'})['src']
            except:
                pass

            try:
                scoring_text = soup_prof.find('a', {'class': 'feedback-detail-description'}).text
            except:
                pass

            try:
                item_dic['scoring'] = scoring_text.split("%")[0]
            except:
                pass

            try:
                item_dic['scoring_amount'] = scoring_text.split("(")[1].split(" ")[0]
            except:
                pass

            item_dic['profile_top_text'] = ""
            try:
                item_dic['profile_top_text'] = soup_prof.find('span', {'id': 'about-seller-expanded'}).text
            except:
                pass

            try:
                if(item_dic['profile_top_text'] == ""):
                    item_dic['profile_top_text'] = soup_prof.find('span', {'id': 'about-seller-text'}).text
            except:
                pass

            try:
                for list_item in soup_prof.find_all('span', {'class': 'a-list-item'}):
                    item_data = list_item.text.split(":")
                    if(item_data[0]=="Geschäftsname"):
                        try:
                            item_dic['geschaftsname'] = item_data[1].strip()
                        except:
                            pass
                    if(item_data[0]=="Geschäftsart"):
                        try:
                            item_dic['geschaftsart'] = item_data[1].strip()
                        except:
                            pass
                    if(item_data[0]=="Handelsregisternummer"):
                        try:
                            item_dic['handelsregisternummer'] = item_data[1].strip()
                        except:
                            pass
                    if(item_data[0]=="UStID"):
                        try:
                            item_dic['ustid'] = item_data[1].strip()
                        except:
                            pass
                    if(item_data[0]=="Unternehmensvertreter"):
                        try:
                            item_dic['unternehmensvertreter'] = item_data[1].strip()
                        except:
                            pass
                    if(item_data[0]=="Telefonnummer"):
                        try:
                            item_dic['telefonnummer'] = item_data[1].strip()
                        except:
                            pass
                    if (item_data[0] == "Kundendienstadresse"):
                        try:
                            soup_list_item = BeautifulSoup(str(list_item.ul), 'html.parser')
                            kundendienstadresse_list = soup_list_item.find_all("li")
                            item_dic['kundendienstadresse_raw']=""
                            for k_item in kundendienstadresse_list:
                                item_dic['kundendienstadresse_raw']+=k_item.text+"\n"
                            categorized_address = categorize_address(kundendienstadresse_list)
                            item_dic['kundendienstadresse_strasse'] = categorized_address[0]
                            item_dic['kundendienstadresse_hausnummer'] = categorized_address[1]
                            item_dic['kundendienstadresse_stadt'] = categorized_address[2]
                            item_dic['kundendienstadresse_bundesland'] = categorized_address[3]
                            item_dic['kundendienstadresse_plz'] = categorized_address[4]
                            item_dic['kundendienstadresse_land'] = categorized_address[5]
                        except:
                            pass
                    if (item_data[0] == "Geschäftsadresse"):
                        try:
                            soup_list_item = BeautifulSoup(str(list_item.ul), 'html.parser')
                            geschaftsadresse_list = soup_list_item.find_all("li")
                            item_dic['geschaftsadresse_raw']=""
                            for g_item in geschaftsadresse_list:
                                item_dic['geschaftsadresse_raw']+=g_item.text+"\n"

                            categorized_address = categorize_address(geschaftsadresse_list)
                            item_dic['geschaftsadresse_strasse'] = categorized_address[0]
                            item_dic['geschaftsadresse_hausnummer'] = categorized_address[1]
                            item_dic['geschaftsadresse_stadt'] = categorized_address[2]
                            item_dic['geschaftsadresse_bundesland'] = categorized_address[3]
                            item_dic['geschaftsadresse_plz'] = categorized_address[4]
                            item_dic['geschaftsadresse_land'] = categorized_address[5]
                        except:
                            pass
            except:
                pass

            item_dic['seller_product_page_url'] = ""
            try:
                item_dic['seller_product_page_url'] = 'https://www.amazon.de' + soup_prof.find('li', {'id': 'products-link'}).a['href']
            except:
                pass

            if (item_dic['seller_product_page_url'] != ""):
                print("getting seller product page url ...")
                for z in range(1,11):
                    print("try: "+str(z))
                    seller_product_page_url = 'http://api.scraperapi.com?api_key=e59b5548e36da5aadaab906ac45d9743&url=' + item_dic['seller_product_page_url']
                    response = requests.get(seller_product_page_url)
                    print(response)
                    if(response.status_code==200):
                        break

                try:
                    if("Ergebnissen</span>" in response.text):
                        item_dic['seller_product_amount'] = response.text.split(' Ergebnissen</span>')[0].split(" ")[-1].strip()
                    elif("Ergebnisse</span>" in response.text):
                        item_dic['seller_product_amount'] = response.text.split(' Ergebnisse</span>')[0].split(">")[-1].strip()
                    else:
                        item_dic['seller_product_amount'] = ""
                except:
                    pass

                try:
                    soup_product_page = BeautifulSoup(response.text, 'html.parser')
                    seller_brands_list = []
                    for brand_item in soup_product_page.find_all("a",{"class":"s-navigation-item"}):
                        seller_brands_list.append(brand_item.span.text.strip())
                    item_dic['seller_brands'] = ", ".join(seller_brands_list)
                except:
                    pass



        print("These are the items collected data to be saved")
        print(item_dic)
        try:
            with open('output.csv', 'a', encoding='UTF8', newline='') as f:
                now = datetime.now()
                date_now = now.strftime("%d/%m/%Y %H:%M:%S")

                writer = csv.writer(f)
                header_row = ["timestamp","category","category-url","mothercategory","mothercategory-url","product-url","product-name","store-name","sold-by","Marke","product-creator","product-seller-amount","product-rating","product-rating-amount","product-online-since","ASIN","bestseller-rank-name-1","bestseller-ranking-1","bestseller-rank-name-2","bestseller-ranking-2","profile-url","profile-name","profile-image","scoring","scoring-amount","profile-top-text","profile-top-phone-extraction","profile-top-email-extraction","Geschäftsname","Geschäftsart","Handelsregisternummer","UStID","Unternehmensvertreter","Telefonnummer","Kundendienstadresse-Raw","Kundendienstadresse-Strasse","Kundendienstadresse-hausnummer","Kundendienstadresse-stadt","Kundendienstadresse-bundesland","Kundendienstadresse-plz","Kundendienstadresse-land","Geschäftsadresse-Raw","Geschäftsadresse-strasse","Geschäftsadresse-hausnummer","Geschäftsadresse-stadt","Geschäftsadresse-bundesland","Geschäftsadresse-plz","Geschäftsadresse-land","seller-product-page-url","seller-product-amount","seller-brands"]
                data_row = [date_now,item_category_name_dic.get(url),item_category_url_dic.get(url),category_mother_category_name_dic.get(url),category_mother_category_url_dic.get(url),item_dic.get("product_url"),item_dic.get("product_name"),item_dic.get("store_name"),item_dic.get("sold_by"),item_dic.get("marke"),item_dic.get("product_creator"),item_dic.get("product_seller_amount"),item_dic.get("product_rating"),item_dic.get("product_rating_amount"),item_dic.get("product_online_since"),item_dic.get("asin"),item_dic.get("bestseller_rank_name_1"),item_dic.get("bestseller_ranking_1"),item_dic.get("bestseller_rank_name_2"),item_dic.get("bestseller_ranking_2"),item_dic.get("profile_url"),item_dic.get("profile_name"),item_dic.get("profile_image"),item_dic.get("scoring"),item_dic.get("scoring_amount"),item_dic.get("profile_top_text"),item_dic.get("profile_top_phone_extraction"),item_dic.get("profile_top_email_extraction"),item_dic.get("geschaftsname"),item_dic.get("geschaftsart"),item_dic.get("handelsregisternummer"),item_dic.get("ustid"),item_dic.get("unternehmensvertreter"),item_dic.get("telefonnummer"),item_dic.get("kundendienstadresse_raw"),item_dic.get("kundendienstadresse_strasse"),item_dic.get("kundendienstadresse_hausnummer"),item_dic.get("kundendienstadresse_stadt"),item_dic.get("kundendienstadresse_bundesland"),item_dic.get("kundendienstadresse_plz"),item_dic.get("kundendienstadresse_land"),item_dic.get("geschaftsadresse_raw"),item_dic.get("geschaftsadresse_strasse"),item_dic.get("geschaftsadresse_hausnummer"),item_dic.get("geschaftsadresse_stadt"),item_dic.get("geschaftsadresse_bundesland"),item_dic.get("geschaftsadresse_plz"),item_dic.get("geschaftsadresse_land"),item_dic.get("seller_product_page_url"),item_dic.get("seller_product_amount"),item_dic.get("seller_brands")]
                writer.writerow(data_row)
                print("saved to output file")
        except:
            print("Issue in saving data into csv")
            pass
    except Exception as e:
        print("Issue in method >>> get_item_details -> "+str(e))

# url = 'https://www.amazon.de/CFH-L%C3%B6tspitze-meisselform-L%C3%B6tkolben-L%C3%B6tstation/dp/B09JKN3241'
# url = 'https://www.amazon.de/Ovalleuchte-Kellerleuchte-Oktaplex-lighting-Neutralweiss/dp/B076PCC9NZ'
# url = 'https://www.amazon.de/Medizinisch-zertifizierte-Mundschutzmasken-Gesichtsmaske-Einwegmaske/dp/B095J8MGHQ'
# url = 'https://www.amazon.de/atmungsaktiv%EF%BC%88typ-3-lagige-Mundbedeckung-Einweg-Masken-Mund-Nasen-Masken-als-Kindermasken/dp/B0922ZYXK3'
# url = 'https://www.amazon.de/AUPROTEC-St%C3%BCck-Maske-Atemschutzmaske-Zertifiziert/dp/B08T6K33SP'
# get_item_details(url)

def start_scrapping(mother_url):

    global status_text
    global checked_child_url_list
    checked_child_url_list=[]
    try:
        with open('output.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            header_row = ["timestamp","category","category-url","mothercategory","mothercategory-url","product-url","product-name","store-name","sold-by","Marke","product-creator","product-seller-amount","product-rating","product-rating-amount","product-online-since","ASIN","bestseller-rank-name-1","bestseller-ranking-1","bestseller-rank-name-2","bestseller-ranking-2","profile-url","profile-name","profile-image","scoring","scoring-amount","profile-top-text","profile-top-phone-extraction","profile-top-email-extraction","Geschäftsname","Geschäftsart","Handelsregisternummer","UStID","Unternehmensvertreter","Telefonnummer","Kundendienstadresse-Raw","Kundendienstadresse-Strasse","Kundendienstadresse-hausnummer","Kundendienstadresse-stadt","Kundendienstadresse-bundesland","Kundendienstadresse-plz","Kundendienstadresse-land","Geschäftsadresse-Raw","Geschäftsadresse-strasse","Geschäftsadresse-hausnummer","Geschäftsadresse-stadt","Geschäftsadresse-bundesland","Geschäftsadresse-plz","Geschäftsadresse-land","seller-product-page-url","seller-product-amount","seller-brands"]
            writer.writerow(header_row)
    except:
        print("Issue in initial creation of output file")
        status_text = "not running. Issue in initial creation of output file"
        return

    status_text = "finding all child urls ..."
    for c in range(1,5): # trying for multiple times if response only contains 1 child url
        print("Main try: "+str(c))
        child_urls = find_child_urls(mother_url)
        child_urls_count = len(child_urls)
        print("child_urls_count: "+str(child_urls_count))
        if(child_urls_count>1):
            break

    if(status_text=='stopping...'):
        status_text = "not running"
        return


    print("All child urls ->")
    child_urls = list(dict.fromkeys(child_urls))
    print(child_urls)
    print("************************************************************************************** Number of child urls: "+str(len(child_urls)))

    status_text = "finding all item urls ..."
    item_urls = []
    for child_url in child_urls:
        if (status_text == 'stopping...'):
            status_text = "not running"
            return
        item_urls += get_bestsellers_items(child_url)

    item_urls = list(dict.fromkeys(item_urls))
    tot_items = len(item_urls)
    print("************************************************************************************** Number of item urls: " + str(tot_items))

    item_count = 0
    for item_url in item_urls:

        if (status_text == 'stopping...'):
            status_text = "not running"
            return

        item_count+=1
        status_text = "scraping item "+str(item_count) + " out of all "+str(tot_items) + " items."
        # if(item_count==30):
        #     break
        get_item_details(item_url)

    status_text = "not running. scraped all "+str(tot_items) + " items."


@application.route('/', methods=['GET','POST'])
def start_scraping():
    if request.method == 'POST':
        mother_url = request.form['mother_url']
        print(mother_url)

        global status_text
        if("not running" in status_text):
            status_text = "just started scraping process"
            t = Thread(target=start_scrapping, args=(mother_url,))
            t.start()
        else:
            return "You cannot start another scraping while scraping is in process. check in '/status'. it should be *not running* before you start scraping again. you can use '/stop' command to stop the current scraping process."


    return render_template('ui.html')


@application.route('/status', methods=['GET', 'POST'])
def status():
    global status_text
    return status_text

@application.route('/download', methods=['GET', 'POST'])
def download():
    return send_from_directory("./", "output.csv",as_attachment=True)

@application.route('/stop', methods=['GET', 'POST'])
def stop():
    global status_text
    print(status_text)
    if("not running" not in status_text):
        status_text = "stopping..."
        return "scraping process will stop in few seconds"
    return "nothing is running now"

if __name__ == "__main__":
    application.run(host='0.0.0.0',port=8080)