from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import matplotlib.pyplot as plt

def analyze(last_2_digits,card_id):
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    driver.get("https://ppc.magnati.com/ppc-inquiry/")

    time.sleep(3)

    driver.find_element(By.ID, "cardNo").send_keys(last_2_digits)
    driver.find_element(By.ID, "cardId").send_keys(card_id)

    driver.execute_script("ppcFormSubmit()")

    time.sleep(10)


    driver.find_element(By.ID, "noOfTxns").send_keys("1000")
    driver.execute_script("ppcFormSubmit()")

    time.sleep(5)

    table = driver.find_element(By.ID, "printTable2")
    table_html = table.get_attribute('outerHTML')

    df = pd.read_html(table_html)[0]
    df.columns = ['id', 'date', 'name', 'paid', 'received', 'balance']

    driver.quit()

    df['paid'] = pd.to_numeric(df['paid'], errors='coerce')
    df['received'] = pd.to_numeric(df['received'], errors='coerce')

    df['date'] = pd.to_datetime(df['date'])


    one_year_ago = pd.Timestamp.today() - pd.DateOffset(months=36)
    df_recent = df[df['date'] >= one_year_ago]

    df_recent['month'] = df_recent['date'].dt.to_period('M').dt.to_timestamp()

    monthly_spendings = df_recent.groupby('month')['paid'].sum().reset_index()
    monthly_earnings = df_recent.groupby('month')['received'].sum().reset_index()

    plt.figure(figsize=(10, 5))
    bars = plt.bar(monthly_earnings['month'].dt.strftime('%Y-%m'), monthly_earnings['received'],color='green', alpha =1 )
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    plt.title('Total Earnings per Month (Last 12 Months)')
    plt.xlabel('Month')
    plt.ylabel('Earnings (AED)')
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig("static/earnings"+str(card_id)+".jpg")


    plt.figure(figsize=(10, 5))


    spendingsbar = plt.bar(monthly_spendings['month'].dt.strftime('%Y-%m'), monthly_spendings['paid'],color='red', alpha =0.5 )
    for bar in spendingsbar:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:.0f}', 
                ha='center', va='bottom', fontsize=9)
    plt.title('Total Spendings per Month (Last 12 Months)')
    plt.xlabel('Month')
    plt.ylabel('Spendings (AED)')    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/spendings"+str(card_id)+".jpg")
    total_received = df['received'].sum()
    total_spent = df['paid'].sum()
    balance = total_received - total_spent
    pull_rows = df[df['name'].str.contains("PULL", case=False, na=False)]
    grouped = df.groupby('name')

    summary = grouped[['paid', 'received']].sum().reset_index()
    sorted_summary = summary.sort_values(by='paid', ascending=False)
    top20vendors = sorted_summary[0:20]
    
    
    daily_spendings = df.groupby(df['date'].dt.date)['paid'].sum()

    highest_day = daily_spendings.idxmax()

    highest_total = df.groupby(df['date'].dt.date)['paid'].sum().max()
    top_5 = daily_spendings.sort_values(ascending=False).head(5)
    def detect_subscriptions(df):
        df['date'] = pd.to_datetime(df['date'])
        df['paid'] = pd.to_numeric(df['paid'], errors='coerce')

        subscriptions = []

        for name, group in df.groupby('name'):
            group = group.sort_values('date')

            if len(group) <= 4:
                continue  

            date_diffs = group['date'].diff().dropna().dt.days
            avg_diff = date_diffs.mean()

            amount_std = group['paid'].std()
            amount_mean = group['paid'].mean()

            if (
                20 <= avg_diff <= 80 and       
                amount_std < amount_mean * 0.3  
            ):
                subscriptions.append({
                    'name': name,
                    'avg_days_between': round(avg_diff, 1),
                    'avg_amount': round(amount_mean, 2),
                    'num_occurrences': len(group),
                    'total_spent': round(len(group)*round(amount_mean, 2))
                })

        return pd.DataFrame(subscriptions)

    subs = detect_subscriptions(df)
    
    def plot_balance(df):
        df['date'] = pd.to_datetime(df['date'])
        df['paid'] = pd.to_numeric(df['paid'], errors='coerce').fillna(0)
        df['received'] = pd.to_numeric(df['received'], errors='coerce').fillna(0)
        df = df.sort_values('date')
        df['net'] = df['received'] - df['paid']
        df['balance'] = df['net'].cumsum()

        plt.figure(figsize=(10, 5))
        plt.plot(df['date'], df['balance'], marker='none', linewidth=2, color='green')
        plt.title("Running Balance Over Time")
        plt.xlabel("Date")
        plt.ylabel("Balance (AED)")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(rotation=45)
        # 
        plt.rcParams.update({
        'axes.edgecolor': 'black',
        'axes.labelcolor': 'black',
        'xtick.color': 'black',
        'ytick.color': 'black',
        'grid.color': 'darkgrey',
        'grid.linestyle': '-',
        'figure.facecolor': 'none', 
        'axes.facecolor': 'none'     
        })
        plt.savefig('balancegraph'+card_id+'.png', transparent=True, dpi=300)

    plot_balance(df)
    

    
    
    
    
    

    return total_received, total_spent, balance, "static/spendings"+str(card_id)+".jpg","static/earnings"+str(card_id)+".jpg", top20vendors,top_5,subs,'static/balancegraph'+card_id+'.png'


last = input('last 2 digits: ')
id = input('card id: ')
print(analyze(last,id))


