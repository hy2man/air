import base64
import requests
import time
import hashlib
import json
import re
import datetime



def generate_sign():
    appkey = "147359109"
    secret = "b875f29a586906c335143acb3c8b80df"
    mayi_url = "s5.proxy.mayidaili.com"
    mayi_port = "8123"
    mayi_proxy = 'http://{}:{}'.format(mayi_url, mayi_port)

    paramMap = {
        "app_key": appkey,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    keys = sorted(paramMap)
    codes = "%s%s%s" % (secret, str().join('%s%s' % (key, paramMap[key]) for key in keys), secret)

    sign = hashlib.md5(codes.encode('utf-8')).hexdigest().upper()

    paramMap["sign"] = sign

    keys = paramMap.keys()
    authHeader = "MYH-AUTH-MD5 " + str('&').join('%s=%s' % (key, paramMap[key]) for key in keys)
    return authHeader, mayi_proxy


def get_price(Origin, Destination, Departure):
    authHeader, mayi_proxy = generate_sign()
    headers = {
        "Mayi-Authorization": authHeader,
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBMXoyUWloUEtXSWdtYlJ3a0ExWXpHcjNobFZKN1hJMiIsImlhdCI6MTU0NDQzODIwOCwiZXhwIjoxNjA3NTk2NjA4LCJhdWQiOiJQV0EgRGV2Iiwic3ViIjoicHJhZGVlcGt1bWFyckBhaXJhc2lhLmNvbSJ9.QJPYvJvzx8IZFP6mYTAKwva7eQ_DVT_4JRwk75Uhhd8',
        'Referer': 'https://www.airasia.com/booking/select/zh/cn/CAN/KUL/2019-01-11/N/1/0/0/O/N/CNY/ST',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'X-Custom-Flag': '1',
    }

    proxies = {
        "http": mayi_proxy,
        "https": mayi_proxy,
    }
    session = requests.session()
    target_url = "https://k.airasia.com/shopprice/0/0/{}/{}/{}/1/0/0".format(Origin, Destination, Departure)
    response = session.get(target_url, proxies=proxies, headers=headers, allow_redirects=False, verify=False)
    # print(response.headers['X-Outbound-Ip'])           #打印本次使用的ip
    dict_all_price = json.loads(response.content.decode())
    print('查询所有价格：', dict_all_price)
    return dict_all_price, session


def chroise_fare(dict, session):
    # FaresInfo_list =dict['GetAvailability'][0]['FaresInfo']
    #     # for fareinfo in FaresInfo_list:
    #         # print(fareinfo)
    #     # #航班信息按时间早晚排序
    fare_info = dict['GetAvailability'][0]['FaresInfo']
    # #选择最早的一班print(fare_info[0])
    pareprice_info = fare_info[0]['BrandedFares']['LowFare']  # 低价票       PremiumFlex高价票
    InventoryLegs = fare_info[0]['InventoryLegs']  # 航司编号     5134822
    JourneySellKey = fare_info[0]['JourneySellKey']  # 航班信息     AK~ 119~ ~~CAN~01/15/2019 01:35~KUL~01/15/2019 05:40~
    FareSellKey = pareprice_info['FareSellKey']  # 航司信息     0~O~~O02H00~AAB1~~1625~X
    FareItems = pareprice_info['FareItems']  # 票价含税
    tatol_price = pareprice_info['TotalPrice']
    ProductClass = pareprice_info['ProductClass']
    url_price_select = 'https://sch.apiairasia.com/inventory/{}/file.json'.format(InventoryLegs)
    headers_select = {
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.airasia.com/booking/select/zh/cn/CAN/KUL/2019-01-11/N/1/0/0/O/N/CNY/ST',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    }
    res_select = session.get(url=url_price_select, headers=headers_select, allow_redirects=False, verify=False)
    print('选择价格信息：', res_select.content.decode())  # 再次查询价格
    dict_select = json.loads(res_select.content.decode())

    return JourneySellKey, FareSellKey, session, dict_select, InventoryLegs, tatol_price, ProductClass


def pege_turn(JourneySellKey, FareSellKey, session):
    url_add = 'https://k.airasia.com/addons/getPreselectedSSR/0/0/1'
    headers_add = {
        'Host': 'k.airasia.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'text/html',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.airasia.com/',
        'Content-Type': 'application/json',
        'Content-Length': '115',
        'Origin': 'https://www.airasia.com',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    add_data = [{
        "JourneySellKey": JourneySellKey,
        "FareSellKey": FareSellKey
    }]

    res_add = session.post(url=url_add, data=json.dumps(add_data), headers=headers_add, allow_redirects=False,
                           verify=False)
    dict_page = json.loads(res_add.content.decode())
    print('翻页价格查询：', dict_page)

    return dict_page, session


def post_person_age_info(Origin, Destination, Departure, DoB, session, header_per):
    url_cos = 'https://k.airasia.com/passengerservice/getPaxType'
    data_cos = [{"DoB": DoB, "Origin": Origin, "Destination": Destination, "Departure": Departure}]
    res_cos = session.post(url=url_cos, data=json.dumps(data_cos), headers=header_per, allow_redirects=False,
                           verify=False)
    print('成年人信息', res_cos.content.decode())


def post_person_name_info(dict_page, session, dict_select, firstName, lastName, gender, DoB, header_per):
    currency = dict_page['PassengerFees'][0]['Currency']
    departAirlineCode = dict_select['CarrierCode']
    departStationCode = dict_select['DepartureStation']
    DepartureDatetime = dict_select['STD']
    departFlightNo = dict_select['FlightNumber']
    arrivalStationCode = dict_select['ArrivalStation']
    dob = str(DoB) + ' 00:00:00'
    identityNo = '999999' + str(DoB).replace('-', '') + '9999'

    url_coss = 'https://k.airasia.com/tuneinsurance/getavailableplans'
    data_coss = {"currency": currency, "totalPremium": 0, "cultureCode": "zh-cn", "totalAdults": 1, "totalChild": 0,
                 "totalInfants": 0, "countryCode": "MY", "flightData": [
            {"departStationCode": departStationCode, "departCountryCode": "CN", "departAirlineCode": departAirlineCode,
             "departDateTime": DepartureDatetime, "departFlightNo": departFlightNo,
             "arrivalStationCode": arrivalStationCode,
             "arrivalCountryCode": "MY", "returnAirlineCode": 'null', "returnDateTime": DepartureDatetime,
             "returnFlightNo": 'null'}], "passengerData": [
            {"isInfant": "false", "firstName": firstName, "lastName": lastName, "gender": gender, "DOB": DoB,
             "identityType": "Passport", "identityNo": identityNo, "isQualified": "false",
             "currencyCode": currency, "passengerPremiumAmount": 0}]}
    res_coss = session.post(url=url_coss, data=json.dumps(data_coss), headers=header_per, allow_redirects=False,
                            verify=False)
    print('传递姓名', res_coss.content.decode())  # 填写乘机人信息页面获取数去


def get_airport_info():
    url_air_info = 'https://sch.apiairasia.com/stationoperate/zh-cn/file.json'

    headers_air_info = {
        'Host': 'sch.apiairasia.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0'
    }
    res_air_info = requests.get(url=url_air_info, headers=headers_air_info)
    data_air_info = json.loads(res_air_info.content.decode())
    dict = {}
    for data_info in data_air_info:
        dict[data_info['StationCode']] = data_info
    return dict


def chectout_price(dict_page, session, dict_select, JourneySellKey, FareSellKey, InventoryLegs, DoB, tatol_price,
                   ProductClass, Departure, gender, firstName, lastName,dict_air_info):
    currency = dict_page['PassengerFees'][0]['Currency']  # CNY
    departAirlineCode = dict_select['CarrierCode']  # AK
    departStationCode = dict_select['DepartureStation']  # CAN
    DepartureDatetime = dict_select['STD'].replace(' ', 'T')  # "2019-01-15 01:35"
    departAirdatetime = dict_select['STA'].replace(' ', 'T')
    departFlightNo = dict_select['FlightNumber']  # 119
    arrivalStationCode = dict_select['ArrivalStation']  # KUL
    EquipmentTypeSuffix = dict_select['EquipmentTypeSuffix']
    identityNo = '999999' + str(DoB).replace('-', '') + '9999'  # 999999199203059999

    #机场信息
    depart_air_info =dict_air_info[departStationCode]
    arrive_air_info =dict_air_info[arrivalStationCode]
    print('出发机场信息',depart_air_info)
    print('目的地机场信息',arrive_air_info)
    arrive_air_name = arrive_air_info['AirportName']
    arrive_air_AlternativeName = arrive_air_info['AlternativeName']
    arrive_air_CountryCode = arrive_air_info['CountryCode']
    arrive_air_CountryName = arrive_air_info['CountryName']
    arrive_air_Lat = arrive_air_info['Lat']
    arrive_air_Long = arrive_air_info['Long']
    arrive_air_PinYin = arrive_air_info['PinYin']
    arrive_air_StationName = arrive_air_info['StationName']
    arrive_air_StationType = arrive_air_info['StationType']
    arrive_air_TimeZone = arrive_air_info['TimeZone']

    depart_air_name = arrive_air_info['AirportName']
    depart_air_AlternativeName = arrive_air_info['AlternativeName']
    depart_air_CountryCode = arrive_air_info['CountryCode']
    depart_air_CountryName = arrive_air_info['CountryName']
    depart_air_Lat = arrive_air_info['Lat']
    depart_air_Long = arrive_air_info['Long']
    depart_air_PinYin = arrive_air_info['PinYin']
    depart_air_StationName = arrive_air_info['StationName']
    depart_air_StationType = arrive_air_info['StationType']
    depart_air_TimeZone = arrive_air_info['TimeZone']


    url_cheng = 'https://k.airasia.com/checkout/v1/bookingcheckout/0/0'
    headers_cheng = {
        'Host': 'k.airasia.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'text/html',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.airasia.com/',
        'Content-Type': 'application/json',
        'Content-Length': '3320',
        'Origin': 'https://www.airasia.com',
        'Connection': 'keep-alive',
    }

    data_cheng = {"NbId": "95286", "FareType": "LF", "OrderData": [
        {"WheelChairCartOrder": 0, "id": 1, "arrivalstation": arrivalStationCode, "currencycode": currency,
         "departurestation": departStationCode,
         "DepartOrReturn": "Depart", "faresellkey": FareSellKey, "CartOrder": tatol_price, "ProductClass": ProductClass,
         "HasSSRBundle": False, "IsAddOnsOpen": False,
         "journeysellkey": JourneySellKey, "opsuffix": "", "paxcount": 1,
         "std": DepartureDatetime, "sta": departAirdatetime, "ClassOfService": "K",
         "InventoryLegs": InventoryLegs,
         "TotalCartOrder": tatol_price,
         "LegsInfo": [
             {"Id": InventoryLegs, "LegDetail": {"ArrivalStation": arrivalStationCode, "CarrierCode": departAirlineCode,
                                                 "DepartureDate": Departure,
                                                 "DepartureStation": departStationCode, "Duration": 245,
                                                 "ETSF": "", "EquipmentType": "320",
                                                 "EquipmentTypeSuffix": EquipmentTypeSuffix,
                                                 "FlightNumber": departFlightNo, "Lid": 180,
                                                 "STA": "2019-01-11 05:40",
                                                 "STD": "2019-01-11 01:35", "Status": 0},
              "ArrivalStationDetails": {
                  "AirportName": arrive_air_name,
                  "AlternativeName": arrive_air_AlternativeName, "CountryCode": arrive_air_CountryCode, "CountryName": arrive_air_CountryName,
                  "Lat":arrive_air_Lat, "Long": arrive_air_Long, "PinYin": arrive_air_PinYin, "StationCode": arrivalStationCode,
                  "StationName": arrive_air_StationName, "StationType": arrive_air_StationType,
                  "TimeZone": arrive_air_TimeZone}, "DepartureStationDetails": {
                 "AirportName": depart_air_name, "AlternativeName": depart_air_AlternativeName,
                 "CountryCode": depart_air_CountryCode, "CountryName": depart_air_CountryName, "Lat": depart_air_Lat, "Long": depart_air_Long, "PinYin": depart_air_PinYin,
                 "StationCode": departStationCode, "StationName": depart_air_StationName, "StationType": depart_air_StationType,
                 "TimeZone": depart_air_TimeZone}}],
         "FeeDetails": [{"FeeCode": "Adult", "Quantity": 1, "TotalPrice": tatol_price}], "IsTaxOpen": True,
         "FareType": "LF",
         "Passengers": [
             {"DocNumber": "12345", "ExpirationDate": "2025-11-25", "IssuedByCode": "US", "IdNum": "80052", "Save": 0,
              "BigShotId": "", "CustomerNumber": "", "LoyaltyTier": "", "IsPWD": False, "IsOFW": False,
              "PassengerInfants": [], "TravelDocs": [], "PriceHash": "", "OptionValue": "", "PassengerNumber": "0",
              "PaxType": "ADT", "Sex": gender, "PaxOfTypeIndex": 1, "SSRBundle": [],
              "SSRList": {"MEALS": [], "INSURANCE": [], "BAGGAGE": [], "INFANT": [], "ACCESSIBILITY": []},
              "DoB": DoB, "Nationalty": "", "Seat": []}], "BundleCartOrder": tatol_price}], "PaxDetails": [
        {"DocNumber": "12345", "ExpirationDate": "2025-11-25", "IssuedByCode": "US", "IdNum": "19865", "Save": 0,
         "BigShotId": "", "CustomerNumber": "", "LoyaltyTier": "", "IsPWD": False, "IsOFW": False,
         "PassengerInfants": [],
         "TravelDocs": [], "PriceHash": "", "OptionValue": "", "PassengerNumber": "0", "PaxType": "ADT", "Sex": gender,
         "PaxOfTypeIndex": 1, "SSRBundle": [], "SSRList": [], "DoB": DoB, "GivenName": firstName, "Nationalty": "",
         "Surname": lastName, "IdentityNo": identityNo, "PaxTypeDesc": "ADT", "SequenceValue": 'null',
         "Title": "Mr"}], "TotalCart": 0, "PaxAndAncillaries": [
        {"DocNumber": "12345", "ExpirationDate": "2025-11-25", "IssuedByCode": "US", "IdNum": "19865", "Save": 0,
         "BigShotId": "", "CustomerNumber": "", "LoyaltyTier": "", "IsPWD": False, "IsOFW": False,
         "PassengerInfants": [],
         "TravelDocs": [], "PriceHash": "", "OptionValue": "", "PassengerNumber": "0", "PaxType": "ADT", "Sex": gender,
         "PaxOfTypeIndex": 1, "SSRBundle": [], "SSRList": [], "DoB": DoB, "GivenName": firstName, "Nationalty": "",
         "Surname": lastName, "IdentityNo": identityNo, "PaxTypeDesc": "ADT", "SequenceValue": 'null',
         "Title": "Mr"}], "IsInsurance": False, "BookingContacts": [], "DeviceId": "",
                  "GaId": "GA1.2.1767886061.1544597964",
                  "UserId": "", "CultureCode": "en-gb",
                  "CurrencyDetails": {"CollectedCurrency": "CNY", "CurrencyCode": "CNY", "IsMccLabel": False,
                                      "CollectedCurrencyExponent": 2, "ExchangeRate": 1}, "InsuranceType": ""}
    res_cheng = session.post(url=url_cheng, data=json.dumps(data_cheng), headers=headers_cheng, verify=False)
    dict_checkout = json.loads((res_cheng.content.decode()))
    # 做判断验证
    # print('检验结果',dict_checkout)
    return dict_checkout, session


def get_cookie(dict_checkout, session):
    print('检验结果', dict_checkout)
    dotRezSignatu = dict_checkout["dotRezSignature"]
    userSessio = dict_checkout["userSession"]
    strq = dotRezSignatu[0:82]
    strd = dotRezSignatu[82:]
    str = strq + '99002BCF' + strd
    dotRezSignature = base64.b64encode(str.encode('utf-8')).decode('utf-8')
    return dotRezSignature, userSessio, session


def get_booking(dotRezSignature, userSessio, session):
    url_booking = 'https://jace.airasia.com/BookingService/GetBooking'
    session.cookies.set('dotRezSignature', dotRezSignature)
    session.cookies.set('userSession', userSessio)
    headers_book = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'content-length': '45',
        'content - type': 'application / json',
        'origin': 'https://booking3.airasia.com',
        'referer': 'https://booking3.airasia.com/payment/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'x-jace-session-id': dotRezSignature,
    }
    data_booking = {"RecordLocator": "", "GetBookingFilter": 28125}
    res_booking = session.post(url=url_booking, data=json.dumps(data_booking), headers=headers_book, verify=False)
    print('28125booking', res_booking.content.decode())
    dict = json.loads(res_booking.content.decode())
    dicts = {}
    book_info = dict['BookingResponse']['BookingInfo']
    BookingSum = dict['BookingResponse']['BookingSum']
    CurrencyCode = dict['BookingResponse']['CurrencyCode']
    Journeys = dict['BookingResponse']['Journeys']
    Passengers = dict['BookingResponse']['Passengers']
    dicts['book_info'] = book_info
    dicts['BookingSum'] = BookingSum
    dicts['CurrencyCode'] = CurrencyCode
    dicts['Journeys'] = Journeys
    dicts['Passengers'] = Passengers
    url_deteck = 'https://jace.airasia.com/BookingService/Booking/Detect'
    res_deteck = session.post(url=url_deteck, data=json.dumps(dicts), headers=headers_book, verify=False)
    print(res_deteck.content.decode())  # {"IsMultiBookings":false}是正确结果
    print('订单后获取信息', json.dumps(dicts))
    return book_info, session


# 线程池
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
pool = ThreadPoolExecutor(128)
# 线程池

def get_addpay(dotRezSignature, book_info, session, firstName, lastName, email, phonenum):
    t = "AddPaymentToBookingDirectDebit"
    o = dotRezSignature
    phon_num = '86' + phonenum

    e_list = [firstName + lastName + email, firstName + lastName + 'P', firstName + lastName + phon_num,
              firstName + lastName + '1', firstName + email + 'P',
              firstName + email + phon_num, firstName + email + '1', firstName + 'P86' + phonenum, firstName + 'P1',
              firstName + phon_num + '1', lastName + email + 'P', lastName + email + phon_num, lastName + email + '1',
              lastName + 'P86' + phonenum, lastName + 'P1', lastName + phon_num + '1', email + 'P86' + phonenum,
              email + phon_num + '1', 'P86' + phonenum + '1', email + 'P1', firstName + lastName + email + 'P',
              firstName + lastName + email + phon_num, firstName + lastName + email + '1',
              firstName + lastName + email + phon_num + '1', firstName + lastName + email + 'P1',
              firstName + lastName + email + 'P' + phon_num, firstName + email + 'P' + phon_num,
              firstName + email + 'P1',
              firstName + email + phon_num + '1', firstName + 'P' + phon_num + '1', email + 'P' + phon_num + '1',
              lastName + 'P' + phon_num + '1', lastName + email + phon_num + '1', lastName + email + 'P1',
              lastName + email + 'P' + phon_num, firstName + lastName, firstName + email, firstName + 'P',
              firstName + phon_num, firstName + '1',
              lastName + email, lastName + 'P', lastName + phon_num, lastName + '1', email + 'P',
              email + phon_num, email + '1', 'P' + phon_num, 'P1', phon_num + '1',
              firstName + lastName + email + 'P' + phon_num, firstName + lastName + email + 'P1',
              firstName + lastName + email + phon_num + '1', firstName + lastName + 'P' + phon_num + '1',
              firstName + email + 'P' + phon_num + '1',
              lastName + email + 'P' + phon_num + '1', firstName, lastName, email, 'P', phon_num, '1',
              firstName + lastName + email + 'P' + phon_num + '1']


    def func(e):    
        sha256 = hashlib.sha256()
        sha256.update(t.encode('utf-8'))
        sha256.update(o.encode('utf-8'))
        sha256.update(e.encode('utf-8'))
        string = sha256.hexdigest().upper()

        url_infp = 'https://jace.airasia.com/PaymentService/AddPaymentToBookingDirectDebit'
        headers_info = {
            'Host': 'jace.airasia.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://booking3.airasia.com/payment/DA',
            'Content-Type': 'application/json',
            'Authorization': "User " + string,
            'X-JAce-Session-Id': dotRezSignature,
            'Content-Length': '859',
            'Origin': 'https://booking3.airasia.com',
            'Connection': 'keep-alive',
            'TE': 'Trailers',
        }
        data_info = {"CarrierCode": "AK", "FromStation": "CAN", "FromCountry": "CN", "ToStation": "KUL",
                     "ToCountry": "MY",
                     "BookingContacts": [
                         {"Name": {"FirstName": firstName, "LastName": lastName}, "EmailAddress": "744687707@QQ.COM",
                          "TypeCode": "P", "OtherPhone": "8618827506531", "NotificationPreference": "1",
                          "CultureCode": "zh-CN", "CountryCode": "CN", "CustomerNumber": ""}], "EmergencyContact": {},
                     "BookingComments": [{"CommentText": "SessionID: ", "CommentType": "Default",
                                          "CreatedDate": book_info['BookingDate']},
                                         {"CommentText": "GAuserID: 1767886061.1544597964", "CommentType": "Default",
                                          "CreatedDate": book_info['BookingDate']}], "QuotedCurrency": "CNY",
                     "CollectedCurrency": "CNY", "ExternalRateBatchId": "", "RateQuotedId": "", "RoleCode": "WWWA",
                     "CultureCode": "zh-CN", "ReturnUrl": "https://booking3.airasia.com/",
                     "DirectDebit": {"PaymentID": "42", "TabCode": "DA", "PayMethodCode": "C2"}, "PaymentID": "42",
                     "TabCode": "DA"}
        res_addpay = session.post(url=url_infp, data=json.dumps(data_info), headers=headers_info, verify=False)
        dict_info = json.loads(res_addpay.content.decode())

        if dict_info['ItineraryStatus'] == 0:
            # 获取下一步的参数
            ReturnHtml = dict_info['ReturnHtml']
            list = ReturnHtml.split("name='")
            dict = {}
            for a in list:
                b = a.split("' value='")
                c = b[0]
                d = b[-1].split("' />")[0]
                dict[c] = d

            url_order = 'https://paygate.airasia.com/aapg/faces/ddpayment.xhtml'
            headers_order = {
                'Host': 'paygate.airasia.com',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://booking3.airasia.com/payment/DA',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': '1147',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            data_order = {
                'h001_MTI': dict['h001_MTI'],
                'h002_VNO': dict['h002_VNO'],
                'h003_TDT': dict['h003_TDT'],
                'h004_TTM': dict['h004_TTM'],
                'f001_MID': dict['f001_MID'],
                'f003_ProcCode': dict['f003_ProcCode'],
                'f006_TxnDateTime': dict['f006_TxnDateTime'],
                'f007_TxnAmt': dict['f007_TxnAmt'],
                'f010_CurrCode': dict['f010_CurrCode'],
                'f019_ExpTxnAmt': dict['f019_ExpTxnAmt'],
                'f247_OrgTxnAmt': dict['f247_OrgTxnAmt'],
                'f248_OrgCurrCode': dict['f248_OrgCurrCode'],
                'f249_TxnCh': dict['f249_TxnCh'],
                'f256_FICode': dict['f256_FICode'],
                'f260_ServID': dict['f260_ServID'],
                'f261_HostID': dict['f261_HostID'],
                'f262_SessID': dict['f262_SessID'],
                'f263_MRN': dict['f263_MRN'],
                'f264_Locale': dict['f264_Locale'],
                'f270_ORN': dict['f270_ORN'],
                'f271_ODesc': dict['f271_ODesc'],
                'f275_RURL_DD': dict['f275_RURL_DD'],
                'f276_URL_VMPS': dict['f276_URL_VMPS'],
                'f278_EMailAddr': dict['f278_EMailAddr'],
                'f279_HP': dict['f279_HP'],
                'f285_IPAddr': dict['f285_IPAddr'],
                'f287_ExpOrgTxnAmt': dict['f287_ExpOrgTxnAmt'],
                't001_SHT': dict['t001_SHT'],
                't002_SHV': dict['t002_SHV'],
            }
            res_or = session.post(url=url_order, data=data_order, headers=headers_order, allow_redirects=False,
                                    verify=False)

            next_url = res_or.headers['Location']
            print('支付页面的连接', next_url)
            next_res = requests.get(url=next_url)
            page_soure = next_res.text
            return page_soure
    futures = []
    def done(f):
        nonlocal result
        try:
            if not result:
                result = f.result()
            print("线程成功:", result[:200])
        except:
            print("线程失败")
    for e in e_list:
        future = pool.submit(func, e)
        future.add_done_callback(done)
        futures.append(future)
    result = None
    for f in as_completed(futures, 300):
        try:
            result = f.result()
            break
            print("线程成功")
        except:
            print("线程失败")
    print("result : ", result[:500])
    return result


def get_order_number(page_soure):
    order = re.findall('\<span class="first long-content\">(.*?)\<', page_soure, re.S)
    order_number = order[0].strip()
    print('订单编号', order_number)


def save_data(name, data):
    with open(name, 'w')as f:
        f.write(data)
        f.close()


def run(Origin, Destination, Departure, DoB, firstName, lastName, gender, email, phonenum):
    start_time = datetime.datetime.now()
    '''    b变量名解释
    {'Origin': '出发地', 'Destination': '目的地', 'Departure': '出发时间', 'DoB': '出生日期', 'firstName': '名', 'lastName': '姓',
    'gender': '性别', 'Male': '男', 'female': '女', '': '', }
    '''

    dict_all_price, session = get_price(Origin, Destination, Departure)  # 查询当日航司的所有价格

    if dict_all_price['GetAvailability'] == []:
        print('无可用航班')
        pass
    else:
    # 保存信息

        name = str(Departure) + str(Origin)
     # save_data(name, json.dumps(dict))

    # 选择价格
        JourneySellKey, FareSellKey, session, dict_select, InventoryLegs, tatol_price, ProductClass = chroise_fare(
            dict_all_price, session)

        # 查询页面翻页   添加保险食物等（未）
        dict_page, session = pege_turn(JourneySellKey, FareSellKey, session)

        # 输入乘机人出生信息          #判断是否是成年人
        header_per = {
            'Host': 'k.airasia.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept': 'text/html',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.airasia.com/',
            'Content-Type': 'application/json',
            'Content-Length': '82',
            'Origin': 'https://www.airasia.com',
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        }
        post_person_age_info(Origin, Destination, Departure, DoB, session, header_per)

        # 输入乘机人出生信息
        post_person_name_info(dict_page, session, dict_select, firstName, lastName, gender, DoB, header_per)

        # 获取机场信息
        dict_air_info = get_airport_info()

        # 检查是否有票
        dict_checkout, session = chectout_price(dict_page, session, dict_select, JourneySellKey, FareSellKey, InventoryLegs,
                                                DoB, tatol_price,
                                                ProductClass, Departure, gender, firstName, lastName, dict_air_info)
        if 'The requested class of service is sold out' in str(dict_checkout):
            print('航班机票已售完')
            pass
        else:
        # 获取cookie信息
            dotRezSignature, userSessio, session = get_cookie(dict_checkout, session)

            # 预定页面
            book_info, session = get_booking(dotRezSignature, userSessio, session)

            # 支付页面
            page_soure = get_addpay(dotRezSignature, book_info, session, firstName, lastName, email, phonenum)

            # 获取订单编号
            get_order_number(page_soure)
            print(datetime.datetime.now() - start_time)


if __name__ == '__main__':
    run('CAN', 'KUL', '2019-01-17', '1992-03-05', 'xun', 'cao', 'Male', '744687707@QQ.COM', '18827506531')
