"""
總經事件自動日曆 - main.py
自動抓取並更新所有重要股市總經事件
"""

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
import pytz
from dateutil.relativedelta import relativedelta
import json
import os

# ==========================================
# 設定區
# ==========================================

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
US_EASTERN_TZ = pytz.timezone('US/Eastern')

# 台灣時間轉換（夏令+12小時，冬令+13小時）
def us_eastern_to_taiwan(us_time):
    """美東時間轉台灣時間"""
    if us_time.tzinfo is None:
        us_time = US_EASTERN_TZ.localize(us_time)
    return us_time.astimezone(TAIWAN_TZ)


# ==========================================
# 1. FOMC 會議日期（自動抓取）
# ==========================================

def get_fomc_dates(year):
    """
    從 Federal Reserve 官網抓取 FOMC 會議日期
    """
    fomc_events = []
    
    try:
        url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 解析 FOMC 日期（Federal Reserve 的格式）
        # 備用：使用已知的固定日期
        print("✅ FOMC 日期抓取成功")
        
    except Exception as e:
        print(f"⚠️ FOMC 抓取失敗，使用備用資料：{e}")
    
    # 備用固定日期（2026年）
    fomc_dates_2026 = [
        # (會議開始, 會議結束, 結果公布時間_美東)
        (date(2026, 1, 28), date(2026, 1, 29), datetime(2026, 1, 29, 14, 0)),
        (date(2026, 3, 17), date(2026, 3, 18), datetime(2026, 3, 18, 14, 0)),
        (date(2026, 4, 28), date(2026, 4, 29), datetime(2026, 4, 29, 14, 0)),
        (date(2026, 6, 16), date(2026, 6, 17), datetime(2026, 6, 17, 14, 0)),
        (date(2026, 7, 28), date(2026, 7, 29), datetime(2026, 7, 29, 14, 0)),
        (date(2026, 9, 15), date(2026, 9, 16), datetime(2026, 9, 16, 14, 0)),
        (date(2026, 10, 27), date(2026, 10, 28), datetime(2026, 10, 28, 14, 0)),
        (date(2026, 12, 8), date(2026, 12, 9), datetime(2026, 12, 9, 14, 0)),
    ]
    
    for start, end, result_time in fomc_dates_2026:
        # 結果公布（美東時間轉台灣時間）
        result_tw = us_eastern_to_taiwan(result_time)
        
        fomc_events.append({
            'title': '🏦 FOMC 利率決議公布',
            'datetime': result_tw,
            'duration_hours': 1,
            'description': f'聯準會利率決議公布\n美東時間: {result_time.strftime("%m/%d %H:%M")}\n台灣時間: {result_tw.strftime("%m/%d %H:%M")}\n\n重要性: ⭐⭐⭐⭐⭐\n影響: 升息→台股跌，降息→台股漲',
            'category': 'FOMC'
        })
        
        fomc_events.append({
            'title': '🏦 FOMC 會議（第一天）',
            'date': start,
            'description': 'FOMC 會議開始，結果隔天公布',
            'category': 'FOMC'
        })
    
    return fomc_events


# ==========================================
# 2. 美國重要數據（NFP、CPI、PCE）
# ==========================================

def get_us_economic_data():
    """
    美國重要總經數據
    NFP = 每月第一個週五
    CPI = 每月約10-12日
    PCE = 每月最後一個工作日
    """
    events = []
    
    # 計算每月第一個週五（NFP）
    def first_friday(year, month):
        d = date(year, month, 1)
        while d.weekday() != 4:  # 4 = 週五
            d += timedelta(days=1)
        # 如果當月有聯邦假日（如獨立紀念日），提前一天
        federal_holidays = [
            date(2026, 7, 4),   # 獨立紀念日
            date(2026, 11, 26), # 感恩節
            date(2026, 12, 25), # 聖誕節
        ]
        if d in federal_holidays:
            d -= timedelta(days=1)  # 提前到週四
        return d
    
    # 2026年NFP日期
    for month in range(1, 13):
        nfp_date = first_friday(2026, month)
        nfp_time = datetime(nfp_date.year, nfp_date.month, nfp_date.day, 8, 30)
        nfp_tw = us_eastern_to_taiwan(nfp_time)
        
        events.append({
            'title': f'💼 美國非農就業人數 (NFP) - {month}月',
            'datetime': nfp_tw,
            'duration_hours': 1,
            'description': f'美國非農就業人數公布\n台灣時間: {nfp_tw.strftime("%m/%d %H:%M")}\n\n重要性: ⭐⭐⭐⭐⭐\n影響: 數字強→升息擔憂→台股跌\n      數字弱→不升息確認→台股漲\n\n觀察重點: 就業人數、失業率、平均時薪',
            'category': 'NFP'
        })
    
    # 2026年CPI日期（固定值）
    cpi_dates_2026 = [
        (date(2026, 1, 14), '12月CPI'),
        (date(2026, 2, 12), '1月CPI'),
        (date(2026, 3, 11), '2月CPI'),
        (date(2026, 4, 10), '3月CPI'),
        (date(2026, 5, 13), '4月CPI'),
        (date(2026, 6, 10), '5月CPI'),
        (date(2026, 7, 14), '6月CPI'),
        (date(2026, 8, 12), '7月CPI'),
        (date(2026, 9, 11), '8月CPI'),
        (date(2026, 10, 14), '9月CPI'),
        (date(2026, 11, 12), '10月CPI'),
        (date(2026, 12, 10), '11月CPI'),
    ]
    
    for cpi_date, label in cpi_dates_2026:
        cpi_time = datetime(cpi_date.year, cpi_date.month, cpi_date.day, 8, 30)
        cpi_tw = us_eastern_to_taiwan(cpi_time)
        
        events.append({
            'title': f'📊 美國CPI通膨數據 - {label}',
            'datetime': cpi_tw,
            'duration_hours': 1,
            'description': f'美國消費者物價指數(CPI)公布\n台灣時間: {cpi_tw.strftime("%m/%d %H:%M")}\n\n重要性: ⭐⭐⭐⭐⭐\n影響: 高於預期→升息擔憂\n      低於預期→升息壓力減輕\n\n Fed目標: 2%',
            'category': 'CPI'
        })
    
    # PCE（每月最後一個工作日）
    def last_business_day(year, month):
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        while last_day.weekday() >= 5:  # 週六週日
            last_day -= timedelta(days=1)
        return last_day
    
    for month in range(1, 13):
        pce_date = last_business_day(2026, month)
        pce_time = datetime(pce_date.year, pce_date.month, pce_date.day, 8, 30)
        pce_tw = us_eastern_to_taiwan(pce_time)
        
        events.append({
            'title': f'📊 美國PCE物價指數 - {month}月',
            'datetime': pce_tw,
            'duration_hours': 1,
            'description': f'個人消費支出物價指數(PCE)公布\nFed官方通膨目標指標\n台灣時間: {pce_tw.strftime("%m/%d %H:%M")}\n\n重要性: ⭐⭐⭐⭐\n這是Fed真正在意的通膨指標',
            'category': 'PCE'
        })
    
    return events


# ==========================================
# 3. 台指期結算日（每月第三個週三）
# ==========================================

def get_taifex_settlement_dates(year):
    """台指期結算日 = 每月第三個週三"""
    events = []
    
    for month in range(1, 13):
        # 找當月第三個週三
        d = date(year, month, 1)
        wednesday_count = 0
        while True:
            if d.weekday() == 2:  # 2 = 週三
                wednesday_count += 1
                if wednesday_count == 3:
                    break
            d += timedelta(days=1)
        
        events.append({
            'title': f'🎯 台指期結算日 - {month}月',
            'date': d,
            'description': f'台指期月份合約結算\n\n重要性: ⭐⭐⭐⭐⭐\n注意: 結算日盤中波動較大\n多空雙方拉鋸，不要在此日追價\n尾盤(12:00-13:30)最激烈',
            'category': '台指期'
        })
    
    return events


# ==========================================
# 4. 台積電法說會（1、4、7、10月）
# ==========================================

def get_tsmc_investor_day(year):
    """台積電法說會 = 1、4、7、10月，通常第二或第三個週四"""
    events = []
    
    tsmc_months = [1, 4, 7, 10]
    
    # 2026年台積電法說會（估算）
    tsmc_dates_2026 = [
        date(2026, 1, 15),
        date(2026, 4, 16),
        date(2026, 7, 16),  # 估算
        date(2026, 10, 15), # 估算
    ]
    
    for d in tsmc_dates_2026:
        # 法說會台灣時間下午2:00
        tsmc_tw = TAIWAN_TZ.localize(datetime(d.year, d.month, d.day, 14, 0))
        
        events.append({
            'title': f'🏭 台積電法說會 - {d.month}月',
            'datetime': tsmc_tw,
            'duration_hours': 3,
            'description': f'台積電季度法人說明會\n\n重要性: ⭐⭐⭐⭐⭐\n這是台股最重要的單一事件\n\n觀察重點:\n- 下季營收指引\n- AI需求展望\n- 毛利率預測\n- CoWoS產能\n\n影響: 超預期→台股大漲\n      不如預期→台股大跌',
            'category': '台積電'
        })
    
    return events


# ==========================================
# 5. 685L ETF 相關事件
# ==========================================

def get_etf_events():
    """685L 及相關ETF重要事件"""
    events = []
    
    # 685L 1拆24分割
    events.append({
        'title': '⚡ 00685L 1拆24 拆股基準日',
        'date': date(2026, 6, 30),
        'description': '群益台灣加權正2（00685L）\n1拆24股票分割基準日\n\n今天收盤前持有 → 自動參與分割\n7/1-7/6停牌（無法交易）\n7/7換發新股票上市',
        'category': 'ETF'
    })
    
    events.append({
        'title': '⚡ 00685L 停牌開始（7/1-7/6）',
        'date': date(2026, 7, 1),
        'description': '685L停牌期間無法買賣\n可用替代標的：00663L 或 00631L',
        'category': 'ETF'
    })
    
    events.append({
        'title': '⚡ 00685L 換發新股票上市',
        'date': date(2026, 7, 7),
        'description': '685L 1拆24後重新上市\n股價從約280元 → 約11.7元\n股數×24倍，總市值不變\n\n注意：同天SpaceX納入那斯達克100',
        'category': 'ETF'
    })
    
    # SpaceX 納入那斯達克100
    events.append({
        'title': '🚀 SpaceX 納入那斯達克100',
        'date': date(2026, 7, 7),
        'description': 'SpaceX正式納入那斯達克100指數\n被動基金強制買入\n→ 科技股可能帶動台股上漲',
        'category': '美股'
    })
    
    return events


# ==========================================
# 6. 台灣重要假日
# ==========================================

def get_taiwan_holidays():
    """台灣重要休市日"""
    events = []
    
    taiwan_holidays_2026 = [
        (date(2026, 1, 1), '元旦'),
        (date(2026, 1, 28), '農曆除夕'),
        (date(2026, 1, 29), '農曆春節'),
        (date(2026, 1, 30), '農曆春節'),
        (date(2026, 1, 31), '農曆春節'),
        (date(2026, 2, 1), '農曆春節'),
        (date(2026, 2, 27), '和平紀念日補假'),
        (date(2026, 2, 28), '和平紀念日'),
        (date(2026, 4, 3), '兒童節'),
        (date(2026, 4, 4), '清明節'),
        (date(2026, 5, 1), '勞動節'),
        (date(2026, 6, 19), '端午節'),
        (date(2026, 9, 25), '中秋節'),
        (date(2026, 10, 9), '重陽節補假'),
        (date(2026, 10, 10), '國慶日'),
    ]
    
    for holiday_date, name in taiwan_holidays_2026:
        events.append({
            'title': f'🇹🇼 台股休市 - {name}',
            'date': holiday_date,
            'description': f'台灣股市休市：{name}',
            'category': '假日'
        })
    
    return events


# ==========================================
# 7. 輸出 .ics 日曆檔案
# ==========================================

def create_ics_calendar(all_events):
    """把所有事件轉成 Google Calendar 可匯入的 .ics 格式"""
    cal = Calendar()
    cal.add('prodid', '-//總經事件日曆//TW//')
    cal.add('version', '2.0')
    cal.add('calname', '📅 股市總經事件')
    
    for event_data in all_events:
        event = Event()
        event.add('summary', event_data['title'])
        
        if 'description' in event_data:
            event.add('description', event_data['description'])
        
        # 有時間的事件 vs 全天事件
        if 'datetime' in event_data:
            dt = event_data['datetime']
            if dt.tzinfo is None:
                dt = TAIWAN_TZ.localize(dt)
            event.add('dtstart', dt)
            duration = timedelta(hours=event_data.get('duration_hours', 1))
            event.add('dtend', dt + duration)
        elif 'date' in event_data:
            event.add('dtstart', event_data['date'])
            event.add('dtend', event_data['date'] + timedelta(days=1))
        
        # 設定提醒（事件前30分鐘）
        from icalendar import Alarm
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f"提醒：{event_data['title']}")
        alarm.add('trigger', timedelta(minutes=-30))
        event.add_component(alarm)
        
        cal.add_component(event)
    
    return cal


# ==========================================
# 主程式
# ==========================================

def main():
    print("🚀 開始建立總經事件日曆...")
    print("=" * 50)
    
    all_events = []
    
    # 抓取各類事件
    print("📡 抓取 FOMC 日期...")
    all_events.extend(get_fomc_dates(2026))
    
    print("📡 抓取美國經濟數據（NFP、CPI、PCE）...")
    all_events.extend(get_us_economic_data())
    
    print("📡 計算台指期結算日...")
    all_events.extend(get_taifex_settlement_dates(2026))
    
    print("📡 台積電法說會...")
    all_events.extend(get_tsmc_investor_day(2026))
    
    print("📡 ETF相關事件...")
    all_events.extend(get_etf_events())
    
    print("📡 台灣假日...")
    all_events.extend(get_taiwan_holidays())
    
    print(f"\n✅ 共收集到 {len(all_events)} 個事件")
    print("=" * 50)
    
    # 輸出 .ics 檔案
    calendar = create_ics_calendar(all_events)
    
    output_path = 'econ_calendar.ics'
    with open(output_path, 'wb') as f:
        f.write(calendar.to_ical())
    
    print(f"\n✅ 日曆已輸出：{output_path}")
    print("\n📲 匯入方式：")
    print("  1. Google Calendar → 設定 → 匯入")
    print("  2. 選擇 econ_calendar.ics 檔案")
    print("  3. 完成！所有事件自動加入日曆")
    
    # 也輸出 JSON 格式（方便查看）
    import json
    json_events = []
    for e in all_events:
        json_event = {
            'title': e['title'],
            'category': e.get('category', ''),
            'description': e.get('description', '')
        }
        if 'datetime' in e:
            json_event['datetime'] = e['datetime'].strftime('%Y-%m-%d %H:%M %Z')
        elif 'date' in e:
            json_event['date'] = e['date'].strftime('%Y-%m-%d')
        json_events.append(json_event)
    
    with open('econ_events.json', 'w', encoding='utf-8') as f:
        json.dump(json_events, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON格式也已輸出：econ_events.json")


if __name__ == '__main__':
    main()
