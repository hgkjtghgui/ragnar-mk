import requests, os, sys, jwt, json, binascii, time, urllib3, xKEys, base64, datetime, re, socket, threading
import asyncio
from protobuf_decoder.protobuf_decoder import Parser
from byte import *
from byte import xSEndMsg
from byte import Auth_Chat
from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from flask import Flask, request, jsonify
from black9 import openroom, spmroom
from google_play_scraper import app as google_play_app

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

connected_clients = {}
connected_clients_lock = threading.Lock()

active_spam_targets = {}
active_spam_lock = threading.Lock()

app = Flask(__name__)

current_server_domain = None
current_release_version = None
current_play_version = None
current_payload_template = None

def EnV(n):
    if n < 0:
        raise ValueError("non-negative only")
    o = []
    while True:
        b = n & 0x7F
        n >>= 7
        o.append(b | 0x80 if n else b)
        if not n:
            break
    return bytes(o)

def VFi(f, v):
    return EnV((f << 3) | 0) + EnV(v)

def LFi(f, v):
    b = v.encode() if isinstance(v, str) else v
    return EnV((f << 3) | 2) + EnV(len(b)) + b

def TerGeT(d):
    p = bytearray()
    for k, v in d.items():
        f = int(k)
        if isinstance(v, dict):
            p += LFi(f, TerGeT(v))
        elif isinstance(v, int):
            p += VFi(f, v)
        elif isinstance(v, (str, bytes)):
            p += LFi(f, v)
    return bytes(p)

def fetch_latest_data():
    global current_server_domain, current_release_version, current_play_version, current_payload_template
    
    result = google_play_app('com.dts.freefireth', lang="fr", country='fr')
    current_play_version = result['version']
    
    r = requests.get(f'https://bdversion.ggbluefox.com/live/ver.php?version={current_play_version}&lang=ar&device=android&channel=android&appstore=googleplay&region=ME&whitelist_version=1.3.0&whitelist_sp_version=1.0.0&device_name=google%20G011A&device_CPU=ARMv7%20VFPv3%20NEON%20VMH&device_GPU=Adreno%20(TM)%20640&device_mem=1993', timeout=30, verify=False).json()
    
    server_url = r['server_url']
    full_domain = server_url.replace('https://', '').replace('http://', '').split('/')[0]
    domain_parts = full_domain.split('.')
    current_server_domain = '.'.join(domain_parts[-2:])
    current_release_version = r['latest_release_version']
    
    fields = {
        3: "2025-11-26 01:51:28",
        4: "free fire",
        5: 1,
        7: current_play_version,
        8: "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)",
        9: "Handheld",
        10: "MTN/Spacetel",
        11: "WIFI",
        12: 1280,
        13: 720,
        14: "240",
        15: "x86-64 SSE3 SSE4.1 SSE4.2 AVX AVX2 | 2400 | 4",
        16: 3942,
        17: "Adreno (TM) 640",
        18: "OpenGL ES 3.2",
        19: "Google|625f716f-91a7-495b-9f16-08fe9d3c6533",
        20: "176.28.139.185",
        21: "ar",
        22: "4306245793de86da425a52caadf21eed",
        23: "4",
        24: "Handheld",
        25: "OnePlus A5010",
        29: "c69ae208fad72738b674b2847b50a3a1dfa25d1a19fae745fc76ac4a0e414c94",
        30: 1,
        41: "MTN/Spacetel",
        42: "WIFI",
        57: "1ac4b80ecf0478a44203bf8fac6120f5",
        60: 46901,
        61: 32794,
        62: 2479,
        63: 900,
        64: 34727,
        65: 46901,
        66: 34727,
        67: 46901,
        70: 4,
        73: 1,
        74: "/data/app/com.dts.freefireth-fpXCSphIV6dKC7jL-WOyRA==/lib/arm",
        76: 1,
        77: "e62ab9354d8fb5fb081db338acb33491|/data/app/com.dts.freefireth-fpXCSphIV6dKC7jL-WOyRA==/base.apk",
        78: 6,
        79: 1,
        81: "32",
        83: "2019119026",
        85: 3,
        86: "OpenGLES2",
        87: 255,
        88: 4,
        92: 16190,
        93: "3rd_party",
        94: "KqsHT8W93GdcG3ZozENfFwVHtm7qq1eRUNaIDNgRobozIBtLOiYCc4Y6zvvpcICxzQF2sOE4cbytwLs4xZbRnpRMpmWRQKmeO5vcs8nQYBhwqH7K",
        95: 111207,
        97: 1,
        98: 1,
        99: "4",
        100: "4",
        102: "\u0013R\u0011FP\u000eY\u0003IQ\u000eF\t\u0000\u0011XC9_\u0000[Q\u000fh[V\na\u0007Wm\u000f\u0003f"
    }
    
    current_payload_template = TerGeT(fields)
    
    print(f"تم جلب البيانات: Domain={current_server_domain}, Release={current_release_version}, Version={current_play_version}")
    
    return True

class SimpleAPI:
    def __init__(self):
        self.running = True
        
    def process_spam_command(self, target_id, duration_hours=None):
        try:
            if not ChEck_Commande(target_id):
                return {"status": "error", "message": " user_id غير صالح"}
                
            with active_spam_lock:
                if target_id not in active_spam_targets:
                    active_spam_targets[target_id] = {
                        'active': True,
                        'start_time': datetime.now(),
                        'duration': duration_hours
                    }
                    threading.Thread(target=spam_worker, args=(target_id, duration_hours), daemon=True).start()
                    message = f" تم بدء السبام على المستخدم: {target_id}"
                    if duration_hours:
                        message += f" لمدة {duration_hours} ساعة"
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f" السبام يعمل بالفعل على المستخدم: {target_id}"}
                    
        except Exception as e:
            return {"status": "error", "message": f" خطأ في معالجة الأمر: {str(e)}"}
            
    def process_stop_command(self, target_id):
        try:
            with active_spam_lock:
                if target_id in active_spam_targets:
                    del active_spam_targets[target_id]
                    message = f" تم إيقاف السبام على المستخدم: {target_id}"
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f" لا يوجد سبام نشط على المستخدم: {target_id}"}
                    
        except Exception as e:
            return {"status": "error", "message": f" خطأ في معالجة الأمر: {str(e)}"}
            
    def get_status(self):
        try:
            with active_spam_lock:
                active_targets = list(active_spam_targets.keys())
                active_targets_info = []
                for target_id in active_targets:
                    info = active_spam_targets[target_id]
                    duration_info = ""
                    if info['duration']:
                        elapsed = datetime.now() - info['start_time']
                        remaining = info['duration'] * 3600 - elapsed.total_seconds()
                        if remaining > 0:
                            duration_info = f" ({int(remaining/3600)} ساعة متبقية)"
                    active_targets_info.append(f"{target_id}{duration_info}")
                    
            with connected_clients_lock:
                accounts_count = len(connected_clients)
                accounts_list = list(connected_clients.keys())
                
            status_data = {
                "active_targets_count": len(active_targets),
                "active_targets": active_targets_info,
                "connected_accounts_count": accounts_count,
                "connected_accounts": accounts_list,
                "release_version": current_release_version,
                "server_domain": current_server_domain,
                "play_version": current_play_version
            }
            
            return {"status": "success", "data": status_data}
            
        except Exception as e:
            return {"status": "error", "message": f" خطأ في الحصول على الحالة: {str(e)}"}

def spam_worker(target_id, duration_hours=None):
    print(f" بدء السبام على الهدف: {target_id}" + (f" لمدة {duration_hours} ساعة" if duration_hours else ""))
    
    start_time = datetime.now()
    
    while True:
        with active_spam_lock:
            if target_id not in active_spam_targets:
                print(f"️ توقف السبام على الهدف: {target_id}")
                break
                
            if duration_hours:
                elapsed = datetime.now() - start_time
                if elapsed.total_seconds() >= duration_hours * 3600:
                    print(f" انتهت مدة السبام على الهدف: {target_id}")
                    del active_spam_targets[target_id]
                    break
                
        try:
            send_spam_from_all_accounts(target_id)
            time.sleep(0.1)  
        except Exception as e:
            print(f" خطأ في السبام على {target_id}: {e}")
            time.sleep(1)

def send_spam_from_all_accounts(target_id):
    with connected_clients_lock:
        for account_id, client in connected_clients.items():
            try:
                if (hasattr(client, 'CliEnts2') and client.CliEnts2 and 
                    hasattr(client, 'key') and client.key and 
                    hasattr(client, 'iv') and client.iv):
                    
                    try:
                        client.CliEnts2.send(openroom(client.key, client.iv))
                        print(f" فتح الروم من الحساب: {account_id}")
                    except Exception as e:
                        print(f" خطأ في فتح الروم من الحساب {account_id}: {e}")
                    
                    for i in range(10):  
                        try:
                            client.CliEnts2.send(spmroom(client.key, client.iv, target_id))
                            print(f" إرسال سبام من الحساب {account_id} إلى {target_id} - المحاولة {i+1}")
                        except (BrokenPipeError, ConnectionResetError, OSError) as e:
                            print(f" خطأ اتصال للحساب {account_id}: {e}")
                            break
                        except Exception as e:
                            print(f" خطأ في الإرسال من الحساب {account_id}: {e}")
                            break
                else:
                    print(f" اتصال الحساب {account_id} غير نشط")
            except Exception as e:
                print(f" خطأ في إرسال السبام من الحساب {account_id}: {e}")

api = SimpleAPI()

@app.route('/spam', methods=['GET'])
def start_spam():
    target_id = request.args.get('user_id')
    duration = request.args.get('duration', type=int)
    
    if not target_id:
        return jsonify({"status": "error", "message": " يرجى إدخال الـ user_id"})
    
    result = api.process_spam_command(target_id, duration)
    return jsonify(result)

@app.route('/stop', methods=['GET'])
def stop_spam():
    target_id = request.args.get('user_id')
    
    if not target_id:
        return jsonify({"status": "error", "message": " يرجى إدخال الـ user_id"})
    
    result = api.process_stop_command(target_id)
    return jsonify(result)

@app.route('/status', methods=['GET'])
def get_status():
    result = api.get_status()
    return jsonify(result)

@app.route('/accounts', methods=['GET'])
def get_accounts():
    try:
        with connected_clients_lock:
            accounts_count = len(connected_clients)
            accounts_list = list(connected_clients.keys())
            
        accounts_data = {
            "connected_accounts_count": accounts_count,
            "connected_accounts": accounts_list
        }
        
        return jsonify({"status": "success", "data": accounts_data})
        
    except Exception as e:
        return jsonify({"status": "error", "message": f" خطأ في الحصول على الحسابات: {str(e)}"})

def run_api():
    print("🌐 بدء تشغيل API...")
    app.run(host='0.0.0.0', port=7860, debug=False)

def GeT_Time(timestamp):
    last_login = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    diff = now - last_login   
    d = diff.days
    h , rem = divmod(diff.seconds, 3600)
    m , s = divmod(rem, 60)    
    return d, h, m, s

def Time_En_Ar(t): 
    return ' '.join(t.replace("Day","يوم").replace("Hour","ساعة").replace("Min","دقيقة").replace("Sec","ثانية").split(" - "))
    
ACCOUNTS = []

def load_accounts_from_json(filename="AlliFF.json"):
    accounts = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            
            for item in data:
                uid = str(item.get('uid', ''))  
                password = item.get('password', '')
                
                if uid:  
                    accounts.append({'id': uid, 'password': password})
                    
        print(f"✅ تم تحميل {len(accounts)} حساب من {filename}")
        
    except FileNotFoundError:
        print(f"❌ ملف {filename} غير موجود!")
    except json.JSONDecodeError as e:
        print(f"❌ خطأ في تنسيق JSON في ملف {filename}: {e}")
    except Exception as e:
        print(f"❌ حدث خطأ أثناء قراءة الملف {filename}: {e}")
    
    return accounts

ACCOUNTS = load_accounts_from_json()
            
class FF_CLient():

    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.key = None
        self.iv = None
        self.connection_active = True
        self.Get_FiNal_ToKen_0115()     
            
    def Connect_SerVer_OnLine(self , Token , tok , host , port , key , iv , host2 , port2):
            try:
                self.AutH_ToKen_0115 = tok    
                self.CliEnts2 = socket.create_connection((host2 , int(port2)))
                self.CliEnts2.send(bytes.fromhex(self.AutH_ToKen_0115))                  
            except:pass        
            while self.connection_active:
                try:
                    self.DaTa2 = self.CliEnts2.recv(99999)
                    if '0500' in self.DaTa2.hex()[0:4] and len(self.DaTa2.hex()) > 30:	         	    	    
                            self.packet = json.loads(DeCode_PackEt(f'08{self.DaTa2.hex().split("08", 1)[1]}'))
                            self.AutH = self.packet['5']['data']['7']['data']
                except:pass
                                                            
    def Connect_SerVer(self , Token , tok , host , port , key , iv , host2 , port2):
            self.AutH_ToKen_0115 = tok    
            self.CliEnts = socket.create_connection((host , int(port)))
            self.CliEnts.send(bytes.fromhex(self.AutH_ToKen_0115))  
            self.DaTa = self.CliEnts.recv(1024)          	        
            threading.Thread(target=self.Connect_SerVer_OnLine, args=(Token , tok , host , port , key , iv , host2 , port2)).start()
            self.Exemple = xMsGFixinG('12345678')
            
            self.key = key
            self.iv = iv
            
            with connected_clients_lock:
                connected_clients[self.id] = self
                print(f" تم تسجيل الحساب {self.id} في القائمة العالمية، عدد الحسابات الآن: {len(connected_clients)}")
            
            while True:      
                try:
                    self.DaTa = self.CliEnts.recv(1024)   
                    if len(self.DaTa) == 0 or (hasattr(self, 'DaTa2') and len(self.DaTa2) == 0):	            		
                        print(f"❌ فقد الاتصال بالحساب {self.id}، محاولة إعادة الاتصال...")
                        try:            		    
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            
                            time.sleep(3)
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)                    		                    
                        except:
                            print(f"❌ فشل إعادة الاتصال للحساب {self.id}")
                            with connected_clients_lock:
                                if self.id in connected_clients:
                                    del connected_clients[self.id]
                            break	            
                                      
                    if '/pp/' in self.input_msg[:4]:
                        self.target_id = self.input_msg[4:]	 
                        self.Zx = ChEck_Commande(self.target_id)
                        if True == self.Zx:	            		     
                            threading.Thread(target=send_spam_from_all_accounts, args=(self.target_id,)).start()
                            time.sleep(2.5)    			         
                            self.CliEnts.send(xSEndMsg(f'\n[b][c][{ArA_CoLor()}] SuccEss Spam To {xMsGFixinG(self.target_id)} From All Accounts\n', 2 , self.DeCode_CliEnt_Uid , self.DeCode_CliEnt_Uid , key , iv))
                            time.sleep(1.3)
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)	            		      	
                        elif False == self.Zx: 
                            self.CliEnts.send(xSEndMsg(f'\n[b][c][{ArA_CoLor()}] - PLease Use /pp/<id>\n - Ex : /pp/{self.Exemple}\n', 2 , self.DeCode_CliEnt_Uid , self.DeCode_CliEnt_Uid , key , iv))	
                            time.sleep(1.1)
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)	            		

                except Exception as e:
                    print(f"Error in Connect_SerVer: {e}")
                    try:
                        self.CliEnts.close()
                        if hasattr(self, 'CliEnts2'):
                            self.CliEnts2.close()
                    except:
                        pass
                    time.sleep(5)
                    try:
                        self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)
                    except:
                        print(f"❌ فشل إعادة الاتصال النهائي للحساب {self.id}")
                        with connected_clients_lock:
                            if self.id in connected_clients:
                                del connected_clients[self.id]
                        break
                                    
    def GeT_Key_Iv(self , serialized_data):
        my_message = xKEys.MyMessage()
        my_message.ParseFromString(serialized_data)
        timestamp , key , iv = my_message.field21 , my_message.field22 , my_message.field23
        timestamp_obj = Timestamp()
        timestamp_obj.FromNanoseconds(timestamp)
        timestamp_seconds = timestamp_obj.seconds
        timestamp_nanos = timestamp_obj.nanos
        combined_timestamp = timestamp_seconds * 1_000_000_000 + timestamp_nanos
        return combined_timestamp , key , iv    

    def Guest_GeneRaTe(self , uid , password):
        self.url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        self.headers = {"Host": "100067.connect.garena.com","User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)","Content-Type": "application/x-www-form-urlencoded","Accept-Encoding": "gzip, deflate, br","Connection": "close",}
        self.dataa = {"uid": f"{uid}","password": f"{password}","response_type": "token","client_type": "2","client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3","client_id": "100067",}
        try:
            self.response = requests.post(self.url, headers=self.headers, data=self.dataa).json()
            self.Access_ToKen , self.Access_Uid = self.response['access_token'] , self.response['open_id']
            time.sleep(0.2)
            return self.ToKen_GeneRaTe(self.Access_ToKen , self.Access_Uid)
        except Exception as e: 
            print(f"Error in Guest_GeneRaTe: {e}")
            time.sleep(10)
            return self.Guest_GeneRaTe(uid, password)
                                        
    def GeT_LoGin_PorTs(self , JwT_ToKen , PayLoad):
        self.UrL = f'https://clientbp.{current_server_domain}/GetLoginData'
        self.HeadErs = {
            'Expect': '100-continue',
            'Authorization': f'Bearer {JwT_ToKen}',
            'X-Unity-Version': '2022.3.47f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': current_release_version,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Host': f'clientbp.{current_server_domain}',
            'Connection': 'close',
            'Accept-Encoding': 'deflate, gzip',}        
        try:
                self.Res = requests.post(self.UrL , headers=self.HeadErs , data=PayLoad , verify=False)
                self.BesTo_data = json.loads(DeCode_PackEt(self.Res.content.hex()))  
                address , address2 = self.BesTo_data['32']['data'] , self.BesTo_data['14']['data'] 
                ip , ip2 = address[:len(address) - 6] , address2[:len(address) - 6]
                port , port2 = address[len(address) - 5:] , address2[len(address2) - 5:]             
                return ip , port , ip2 , port2          
        except requests.RequestException as e:
                print(f" - Bad Requests !")
        print(" - Failed To GeT PorTs !")
        return None, None, None, None
        
    def ToKen_GeneRaTe(self , Access_ToKen , Access_Uid):
        self.UrL = f'https://loginbp.{current_server_domain}/MajorLogin'
        self.HeadErs = {
            'X-Unity-Version': '2022.3.47f1',
            'ReleaseVersion': current_release_version,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-GA': 'v1 1',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Host': f'loginbp.{current_server_domain}',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'deflate, gzip'}   
        
        self.dT = current_payload_template
        
        self.dT = self.dT.replace(b'2025-11-26 01:51:28', str(datetime.now())[:-7].encode())
        self.dT = self.dT.replace(b'4306245793de86da425a52caadf21eed', Access_Uid.encode())
        self.dT = self.dT.replace(b'c69ae208fad72738b674b2847b50a3a1dfa25d1a19fae745fc76ac4a0e414c94', Access_ToKen.encode())
        
        try:
            hex_data = self.dT.hex()
            encoded_data = EnC_AEs(hex_data)
            
            if not all(c in '0123456789abcdefABCDEF' for c in encoded_data):
                print(" Invalid hex output from EnC_AEs, using alternative encoding")
                encoded_data = hex_data  
            
            self.PaYload = bytes.fromhex(encoded_data)
        except Exception as e:
            print(f" Error in encoding: {e}")
            self.PaYload = self.dT
        
        self.ResPonse = requests.post(self.UrL, headers = self.HeadErs ,  data = self.PaYload , verify=False)        
        if self.ResPonse.status_code == 200 and len(self.ResPonse.text) > 10:
            try:
                self.BesTo_data = json.loads(DeCode_PackEt(self.ResPonse.content.hex()))
                self.JwT_ToKen = self.BesTo_data['8']['data']           
                self.combined_timestamp , self.key , self.iv = self.GeT_Key_Iv(self.ResPonse.content)
                ip , port , ip2 , port2 = self.GeT_LoGin_PorTs(self.JwT_ToKen , self.PaYload)            
                return self.JwT_ToKen , self.key , self.iv, self.combined_timestamp , ip , port , ip2 , port2
            except Exception as e:
                print(f" Error parsing response: {e}")
                time.sleep(5)
                return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
        else:
            print(f" Error in ToKen_GeneRaTe, status: {self.ResPonse.status_code}")
            time.sleep(5)
            return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
      
    def Get_FiNal_ToKen_0115(self):
        try:
            result = self.Guest_GeneRaTe(self.id , self.password)
            if not result:
                print(" Failed to get tokens, retrying...")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            token , key , iv , Timestamp , ip , port , ip2 , port2 = result
            
            if not all([ip, port, ip2, port2]):
                print(" Failed to get ports, retrying...")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            self.JwT_ToKen = token        
            try:
                self.AfTer_DeC_JwT = jwt.decode(token, options={"verify_signature": False})
                self.AccounT_Uid = self.AfTer_DeC_JwT.get('account_id')
                self.EncoDed_AccounT = hex(self.AccounT_Uid)[2:]
                self.HeX_VaLue = DecodE_HeX(Timestamp)
                self.TimE_HEx = self.HeX_VaLue
                self.JwT_ToKen_ = token.encode().hex()
                print(f' ProxCed Uid : {self.AccounT_Uid}')
            except Exception as e:
                print(f" Error In ToKen : {e}")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            try:
                self.Header = hex(len(EnC_PacKeT(self.JwT_ToKen_, key, iv)) // 2)[2:]
                length = len(self.EncoDed_AccounT)
                self.__ = '00000000'
                if length == 9: self.__ = '0000000'
                elif length == 8: self.__ = '00000000'
                elif length == 10: self.__ = '000000'
                elif length == 7: self.__ = '000000000'
                else:
                    print('Unexpected length encountered')                
                self.Header = f'0115{self.__}{self.EncoDed_AccounT}{self.TimE_HEx}00000{self.Header}'
                self.FiNal_ToKen_0115 = self.Header + EnC_PacKeT(self.JwT_ToKen_ , key , iv)
            except Exception as e:
                print(f" Error In Final Token : {e}")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            self.AutH_ToKen = self.FiNal_ToKen_0115
            self.Connect_SerVer(self.JwT_ToKen , self.AutH_ToKen , ip , port , key , iv , ip2 , port2)        
            return self.AutH_ToKen , key , iv
            
        except Exception as e:
            print(f" Error in Get_FiNal_ToKen_0115: {e}")
            time.sleep(10)
            return self.Get_FiNal_ToKen_0115()

def start_account(account):
    try:
        print(f" Starting account: {account['id']}")
        FF_CLient(account['id'], account['password'])
    except Exception as e:
        print(f" Error starting account {account['id']}: {e}")
        time.sleep(5)
        start_account(account)  

def StarT_SerVer():
    fetch_latest_data()
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    threads = []
    
    for account in ACCOUNTS:
        thread = threading.Thread(target=start_account, args=(account,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(3)  
    
    for thread in threads:
        thread.join()
  
StarT_SerVer()