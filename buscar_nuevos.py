from dotenv import load_dotenv; load_dotenv()
from fantasy import _api_get
import time

for nombre in ['Federico Valverde', 'Takefusa Kubo', 'Kouadio']:
    r = _api_get('players/profiles', {'search': nombre.replace(' ', '%20')})
    p = r.get('response', [])
    print(f"\n{nombre}:")
    for jug in p[:5]:
        j = jug['player']
        print(f"  {j['id']} {j['name']} {j.get('nationality','?')}")
    time.sleep(1)