import csv
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
import time

# 爬取最第三层的数据
def get_3():
    for i in range(1, 3):
        sel_B = web.find_elements(By.XPATH, f'//*[@id="c_list{i}"]/ul/li/a')
        for sel_b in sel_B:
            sel_b.click()
            # driver.find_element_by_xpath("//a[contains(text(),"出")])` #文本部分匹配
            try:                                 # /html/body/div[6]/div/div[2]/ul/li[1]
                Name = web.find_element(By.XPATH, '//*[@id="sms_content"]//li[contains(text(),"【药品名称】")]').text
            except NoSuchElementException:
                Name =''
            try:                                 # /html/body/div[6]/div/div[2]/ul/li[2]
                Component = web.find_element(By.XPATH, '//*[@id="sms_content"]//li[contains(text(),"【成份】")]').text
            except NoSuchElementException:
                Component = ''
            try:                                
                Trait = web.find_element(By.XPATH, '//*[@id="sms_content"]//li[contains(text(),"【性状】")]').text
            except NoSuchElementException:
                Trait = ''
            try:
                Drug_efficacy = web.find_element(By.XPATH, '//*[@id="sms_content"]//li[contains(text(),"【功能主治】")]').text
            except NoSuchElementException:
                Drug_efficacy = ''
            writer.writerow([Name, Component, Trait, Drug_efficacy])
            time.sleep(1)
            web.back()
            time.sleep(1)

# 获取第二层数据
def get_2():
    sel_B = web.find_element(By.XPATH,'//*[@id="sms_page"]')
    # //*[@id="sms_page"]/a[11]

    # 对数据进行清洗,注意它的页码规则，只有1-9，所以进一步做区分
    num=sel_B.text.strip('第').strip('页').replace(' ','')
    page=list(num)
    if len(page)>9:
        max_page_num = int(page[-2]+page[-1])
    else:
        max_page_num = int(page[-1])

    # 开始遍历
    for i in range(1, max_page_num+1):

        if i == 1:
            get_3()

        # 实现页面的切换
        try:
            sel = web.find_element(By.XPATH, f'//*[@id="sms_page"]/a[{int(i)}]')
            sel.click()
        except NoSuchElementException:
            pass

        if i != max_page_num:
            get_3()


# 获取第一层数据 # //*[@id="huayao_mulu_nav"]/a[20] /html/body/div[5]/div[2]/div[2]/div[2]/a[1] /html/body/div[5]/div[2]/div[2]/div[2]/a[2] /html/body/div[5]/div[2]/div[2]/div[2]/a[22]
def get_1():
    for i in range(1,23):
        sel_A = web.find_element(By.XPATH,f'/html/body/div[5]/div[2]/div[2]/div[2]/a[{i}]')
        sel_A.click()
        get_2()
        web.get('https://www.yaopinnet.com/tools/sms.asp')


if __name__ == '__main__':
    # 打开文件并初始化
    f = open('药源网中药.csv', 'a', encoding='utf-8', newline="")
    writer = csv.writer(f)
    # writer.writerow(['药品名称', '主要成分', '主要特性', '药品疗效'])

    web = webdriver.Chrome()

    web.get('https://www.yaopinnet.com/tools/sms.asp')
    get_1()