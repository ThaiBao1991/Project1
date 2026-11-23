import subprocess, time, xml.etree.ElementTree as ET
import set_billing_account
import test_switch_account
import test_switch_g1

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'

def setup_account(email: str):
    print(f"\n==========================================")
    print(f"   SETUP FOR: {email}")
    print(f"==========================================")
    
    # 1. Switch Play Store
    test_switch_account.switch_play_account(email)
    
    # 2. Switch Google One
    test_switch_g1.switch_google_one_account(email)
    
    # 3. Set localappstate.db
    set_billing_account.set_play_billing_account(email)

if __name__ == '__main__':
    setup_account('gamesvendn@gmail.com')
