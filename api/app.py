import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

class Rule:
    def __init__(self, rid, dim, name, conds, cons, conf, pri, sev, rec):
        self.rule_id=rid; self.dimension=dim; self.name=name; self.conditions=conds
        self.consequences=cons; self.confidence=conf; self.priority=pri; self.severity=sev; self.recommendation=rec
    def matches(self, facts):
        for c in self.conditions:
            p,o,v = c['p'], c['o'], c['v']
            if p not in facts: return False
            f = facts[p]
            if o=='>' and not f>v: return False
            if o=='<' and not f<v: return False
            if o=='>=' and not f>=v: return False
            if o=='<=' and not f<=v: return False
            if o=='==' and not f==v: return False
        return True

def R(rid,dim,name,conds,cons,conf,pri,sev,rec):
    return Rule(rid,dim,name,conds,cons,conf,pri,sev,rec)

RULES = [
    R("P01","performance","Excellent Startup",[{'p':'st','o':'<','v':1000}],{'sp':'excellent','ss':100},0.95,10,"info","Startup excellent (<1s)."),
    R("P02","performance","Good Startup",[{'p':'st','o':'>=','v':1000},{'p':'st','o':'<','v':2000}],{'sp':'good','ss':85},0.90,9,"info","Good startup. Minor optimizations possible."),
    R("P03","performance","Acceptable Startup",[{'p':'st','o':'>=','v':2000},{'p':'st','o':'<','v':3000}],{'sp':'acceptable','ss':70},0.85,8,"low","Acceptable startup. Reduce initialization overhead."),
    R("P04","performance","Slow Startup",[{'p':'st','o':'>=','v':3000},{'p':'st','o':'<','v':5000}],{'sp':'slow','ss':50},0.90,7,"medium","Slow startup. Defer non-critical loading, use lazy init."),
    R("P05","performance","Very Slow Startup",[{'p':'st','o':'>=','v':5000},{'p':'st','o':'<','v':8000}],{'sp':'very_slow','ss':30},0.95,6,"high","Very slow startup. Implement splash screen and async loading."),
    R("P06","performance","Critical Startup",[{'p':'st','o':'>=','v':8000}],{'sp':'critical','ss':10},0.95,5,"critical","Startup >8s. Users will abandon. Major refactor needed."),
    R("P07","performance","Near Instant",[{'p':'st','o':'<','v':500}],{'sp':'instant','ss':100},0.95,10,"info","Near-instant startup. Outstanding."),
    R("P08","performance","Sub-Second",[{'p':'st','o':'>=','v':500},{'p':'st','o':'<','v':1000}],{'sp':'sub_second','ss':95},0.90,10,"info","Sub-second startup. Excellent UX."),
    R("P09","performance","Borderline Slow",[{'p':'st','o':'>=','v':2500},{'p':'st','o':'<','v':3000}],{'sp':'borderline','ss':65},0.85,8,"low","Borderline slow. Quick wins available."),
    R("P10","performance","Moderate Slow",[{'p':'st','o':'>=','v':4000},{'p':'st','o':'<','v':5000}],{'sp':'mod_slow','ss':45},0.85,7,"medium","4-5s startup. Optimize aggressively."),
    R("P11","performance","Excellent Memory",[{'p':'mer','o':'<','v':10}],{'mp':'excellent','ms':100},0.95,10,"info","Memory excellent (<10%). Outstanding efficiency."),
    R("P12","performance","Good Memory",[{'p':'mer','o':'>=','v':10},{'p':'mer','o':'<','v':20}],{'mp':'good','ms':85},0.90,9,"info","Good memory efficiency."),
    R("P13","performance","Acceptable Memory",[{'p':'mer','o':'>=','v':20},{'p':'mer','o':'<','v':30}],{'mp':'acceptable','ms':70},0.85,8,"low","Acceptable memory. Review for optimization."),
    R("P14","performance","High Memory",[{'p':'mer','o':'>=','v':30},{'p':'mer','o':'<','v':45}],{'mp':'high','ms':50},0.90,7,"medium","High memory. Implement caching, release unused resources."),
    R("P15","performance","Excessive Memory",[{'p':'mer','o':'>=','v':45},{'p':'mer','o':'<','v':60}],{'mp':'excessive','ms':30},0.90,6,"high","Excessive memory. Check for leaks, reduce cache."),
    R("P16","performance","Critical Memory",[{'p':'mer','o':'>=','v':60}],{'mp':'critical','ms':15},0.95,5,"critical","Critical memory (>60%). App will be killed by OS."),
    R("P17","performance","Lean Memory",[{'p':'mer','o':'<','v':5}],{'mp':'lean','ms':100},0.95,10,"info","Extremely lean memory usage."),
    R("P18","performance","Moderate Memory",[{'p':'mer','o':'>=','v':15},{'p':'mer','o':'<','v':20}],{'mp':'moderate','ms':80},0.85,9,"info","Moderate memory. Acceptable."),
    R("P19","performance","Above Avg Memory",[{'p':'mer','o':'>=','v':25},{'p':'mer','o':'<','v':30}],{'mp':'above_avg','ms':65},0.85,8,"low","Above average memory."),
    R("P20","performance","Very High Memory",[{'p':'mer','o':'>=','v':40},{'p':'mer','o':'<','v':45}],{'mp':'very_high','ms':45},0.90,7,"medium","Very high memory. Profile and optimize."),
    R("P21","performance","Perfect FPS",[{'p':'frc','o':'>=','v':98}],{'up':'perfect','fs':100},0.95,10,"info","Perfect frame rate. Buttery smooth."),
    R("P22","performance","Excellent FPS",[{'p':'frc','o':'>=','v':95},{'p':'frc','o':'<','v':98}],{'up':'excellent','fs':95},0.90,10,"info","Excellent frame rate."),
    R("P23","performance","Good FPS",[{'p':'frc','o':'>=','v':90},{'p':'frc','o':'<','v':95}],{'up':'good','fs':85},0.90,9,"info","Good frame rate."),
    R("P24","performance","Acceptable FPS",[{'p':'frc','o':'>=','v':83},{'p':'frc','o':'<','v':90}],{'up':'acceptable','fs':75},0.85,8,"low","Acceptable FPS. Some drops noticed."),
    R("P25","performance","Below Avg FPS",[{'p':'frc','o':'>=','v':75},{'p':'frc','o':'<','v':83}],{'up':'below_avg','fs':60},0.85,8,"low","Below average FPS. Optimize rendering."),
    R("P26","performance","Poor FPS",[{'p':'frc','o':'>=','v':60},{'p':'frc','o':'<','v':75}],{'up':'poor','fs':45},0.90,7,"medium","Poor FPS. Reduce overdraw, optimize layouts."),
    R("P27","performance","Very Poor FPS",[{'p':'frc','o':'>=','v':50},{'p':'frc','o':'<','v':60}],{'up':'very_poor','fs':30},0.90,6,"high","Very poor FPS. App feels sluggish."),
    R("P28","performance","Unacceptable FPS",[{'p':'frc','o':'<','v':50}],{'up':'unacceptable','fs':15},0.95,5,"critical","Unacceptable FPS. Complete UI rewrite needed."),
    R("P29","performance","Near Perfect FPS",[{'p':'frc','o':'>=','v':96},{'p':'frc','o':'<','v':98}],{'up':'near_perfect','fs':97},0.90,10,"info","Near-perfect frames."),
    R("P30","performance","Mostly Smooth",[{'p':'frc','o':'>=','v':87},{'p':'frc','o':'<','v':90}],{'up':'mostly_smooth','fs':80},0.85,9,"info","Mostly smooth. Rare drops."),
    R("P31","performance","Noticeable Jank",[{'p':'frc','o':'>=','v':70},{'p':'frc','o':'<','v':75}],{'up':'jank','fs':55},0.85,7,"medium","Noticeable jank. Profile UI thread."),
    R("P32","performance","Significant Jank",[{'p':'frc','o':'>=','v':65},{'p':'frc','o':'<','v':70}],{'up':'sig_jank','fs':50},0.90,7,"medium","Significant jank."),
    R("P33","performance","Choppy",[{'p':'frc','o':'>=','v':55},{'p':'frc','o':'<','v':60}],{'up':'choppy','fs':35},0.90,6,"high","Choppy UI. Users will leave."),
    R("P34","performance","Slideshow",[{'p':'frc','o':'>=','v':50},{'p':'frc','o':'<','v':55}],{'up':'slideshow','fs':25},0.90,6,"high","Slideshow frame rate."),
    R("P35","performance","Borderline Smooth",[{'p':'frc','o':'>=','v':80},{'p':'frc','o':'<','v':83}],{'up':'borderline','fs':70},0.85,8,"low","Borderline smooth."),
    R("P36","performance","Fast API",[{'p':'api_ms','o':'<','v':200}],{'ap':'fast','as':100},0.90,10,"info","API fast (<200ms)."),
    R("P37","performance","Good API",[{'p':'api_ms','o':'>=','v':200},{'p':'api_ms','o':'<','v':500}],{'ap':'good','as':85},0.85,9,"info","API response good."),
    R("P38","performance","Slow API",[{'p':'api_ms','o':'>=','v':500},{'p':'api_ms','o':'<','v':1000}],{'ap':'slow','as':60},0.85,8,"low","API slow. Add caching."),
    R("P39","performance","Very Slow API",[{'p':'api_ms','o':'>=','v':1000},{'p':'api_ms','o':'<','v':3000}],{'ap':'very_slow','as':40},0.90,7,"medium","API very slow."),
    R("P40","performance","Timeout Risk API",[{'p':'api_ms','o':'>=','v':3000}],{'ap':'timeout','as':20},0.90,6,"high","API timeout risk."),
    R("P41","performance","Low Battery",[{'p':'bat','o':'<','v':3}],{'bi':'low','bs':100},0.90,10,"info","Low battery impact."),
    R("P42","performance","Moderate Battery",[{'p':'bat','o':'>=','v':3},{'p':'bat','o':'<','v':8}],{'bi':'moderate','bs':70},0.85,8,"low","Moderate battery drain."),
    R("P43","performance","High Battery",[{'p':'bat','o':'>=','v':8},{'p':'bat','o':'<','v':15}],{'bi':'high','bs':40},0.90,7,"medium","High battery drain."),
    R("P44","performance","Battery Killer",[{'p':'bat','o':'>=','v':15}],{'bi':'killer','bs':15},0.95,5,"critical","Battery killer app."),
    R("P45","performance","Low CPU",[{'p':'cpu','o':'<','v':10}],{'ci':'low','cs':100},0.90,10,"info","Low CPU usage."),
    R("P46","performance","Moderate CPU",[{'p':'cpu','o':'>=','v':10},{'p':'cpu','o':'<','v':30}],{'ci':'moderate','cs':75},0.85,8,"low","Moderate CPU."),
    R("P47","performance","High CPU",[{'p':'cpu','o':'>=','v':30},{'p':'cpu','o':'<','v':60}],{'ci':'high','cs':45},0.90,7,"medium","High CPU. Thermal risk."),
    R("P48","performance","CPU Hog",[{'p':'cpu','o':'>=','v':60}],{'ci':'hog','cs':20},0.95,5,"critical","CPU hog. Device will overheat."),
    R("P49","performance","Small App",[{'p':'size','o':'<','v':30}],{'si':'small','szs':100},0.90,10,"info","Small app size."),
    R("P50","performance","Medium App",[{'p':'size','o':'>=','v':30},{'p':'size','o':'<','v':100}],{'si':'medium','szs':80},0.85,9,"info","Medium app size."),
    R("P51","performance","Large App",[{'p':'size','o':'>=','v':100},{'p':'size','o':'<','v':250}],{'si':'large','szs':55},0.85,8,"low","Large app."),
    R("P52","performance","Very Large App",[{'p':'size','o':'>=','v':250}],{'si':'very_large','szs':30},0.90,7,"medium","Very large app (>250MB)."),
    R("P53","performance","Tiny App",[{'p':'size','o':'<','v':10}],{'si':'tiny','szs':100},0.95,10,"info","Tiny app. Instant install."),
    R("P54","performance","Compact App",[{'p':'size','o':'>=','v':10},{'p':'size','o':'<','v':30}],{'si':'compact','szs':95},0.90,10,"info","Compact app."),
    R("P55","performance","Efficient Network",[{'p':'net_req','o':'<','v':10}],{'ne':'efficient'},0.85,9,"info","Efficient network usage."),
    R("P56","performance","Heavy Network",[{'p':'net_req','o':'>=','v':10},{'p':'net_req','o':'<','v':30}],{'ne':'moderate'},0.80,8,"low","Moderate network. Batch requests."),
    R("P57","performance","Excessive Network",[{'p':'net_req','o':'>=','v':30}],{'ne':'excessive'},0.85,7,"medium","Excessive network requests."),
    R("P58","performance","Good Payload",[{'p':'payload_kb','o':'<','v':50}],{'pe':'good'},0.85,9,"info","Small payloads."),
    R("P59","performance","Large Payload",[{'p':'payload_kb','o':'>=','v':50},{'p':'payload_kb','o':'<','v':200}],{'pe':'acceptable'},0.80,8,"low","Moderate payloads."),
    R("P60","performance","Bloated Payload",[{'p':'payload_kb','o':'>=','v':200}],{'pe':'bloated'},0.85,7,"medium","Bloated payloads. Use pagination."),
    R("P61","performance","Fast Storage",[{'p':'stor_ms','o':'<','v':50}],{'sto':'fast'},0.85,9,"info","Fast storage I/O."),
    R("P62","performance","Slow Storage",[{'p':'stor_ms','o':'>=','v':50}],{'sto':'slow'},0.85,7,"medium","Slow storage. Use async writes."),
    R("P63","performance","Minimal Battery",[{'p':'bat','o':'<','v':1}],{'bi':'minimal','bs':100},0.95,10,"info","Minimal battery impact."),
    R("P64","performance","Light Battery",[{'p':'bat','o':'>=','v':1},{'p':'bat','o':'<','v':3}],{'bi':'light','bs':90},0.90,9,"info","Light battery usage."),
    R("P65","performance","Heavy Battery",[{'p':'bat','o':'>=','v':10},{'p':'bat','o':'<','v':15}],{'bi':'heavy','bs':30},0.90,6,"high","Heavy battery drain."),
    R("P66","performance","Low Idle CPU",[{'p':'cpu','o':'<','v':5}],{'ci':'idle','cs':100},0.95,10,"info","Very low idle CPU."),
    R("P67","performance","Moderate Active CPU",[{'p':'cpu','o':'>=','v':15},{'p':'cpu','o':'<','v':30}],{'ci':'mod_active','cs':65},0.85,8,"low","Moderate CPU."),
    R("P68","performance","Thermal Risk CPU",[{'p':'cpu','o':'>=','v':50},{'p':'cpu','o':'<','v':60}],{'ci':'thermal','cs':30},0.90,6,"high","Thermal risk from CPU."),
    R("P69","performance","Instant API",[{'p':'api_ms','o':'<','v':100}],{'ap':'instant','as':100},0.95,10,"info","Instant API."),
    R("P70","performance","Moderate API",[{'p':'api_ms','o':'>=','v':300},{'p':'api_ms','o':'<','v':500}],{'ap':'moderate','as':75},0.85,8,"info","Moderate API."),
    R("P71","performance","High Latency API",[{'p':'api_ms','o':'>=','v':2000},{'p':'api_ms','o':'<','v':3000}],{'ap':'high_lat','as':30},0.90,7,"medium","High API latency."),
    R("P72","performance","Acceptable API",[{'p':'api_ms','o':'>=','v':150},{'p':'api_ms','o':'<','v':200}],{'ap':'acceptable','as':90},0.85,9,"info","Acceptable API."),
    R("P73","performance","Slightly Slow API",[{'p':'api_ms','o':'>=','v':500},{'p':'api_ms','o':'<','v':750}],{'ap':'slight_slow','as':65},0.85,8,"low","Slightly slow API."),
    R("P74","performance","Laggy API",[{'p':'api_ms','o':'>=','v':750},{'p':'api_ms','o':'<','v':1000}],{'ap':'laggy','as':55},0.85,8,"medium","Laggy API."),
    R("P75","performance","Fast Enough API",[{'p':'api_ms','o':'>=','v':100},{'p':'api_ms','o':'<','v':150}],{'ap':'fast_enough','as':95},0.90,10,"info","Fast enough API."),
    R("P76","performance","Network Bound",[{'p':'api_ms','o':'>=','v':1000},{'p':'api_ms','o':'<','v':1500}],{'ap':'net_bound','as':45},0.85,7,"medium","Network-bound."),
    R("P77","performance","Borderline API",[{'p':'api_ms','o':'>=','v':400},{'p':'api_ms','o':'<','v':500}],{'ap':'borderline','as':70},0.85,8,"low","Borderline API speed."),
    R("P78","performance","Slightly Large",[{'p':'size','o':'>=','v':80},{'p':'size','o':'<','v':100}],{'si':'slight_large','szs':70},0.85,8,"low","Slightly large app."),
    R("P79","performance","GC Pressure",[{'p':'gc_min','o':'>','v':10}],{'gc':'pressure'},0.85,7,"medium","High GC frequency."),
    R("P80","performance","No GC Issue",[{'p':'gc_min','o':'<=','v':10}],{'gc':'ok'},0.85,9,"info","GC frequency acceptable."),
    R("P81","performance","Good Cache",[{'p':'cache_mb','o':'<','v':50}],{'cache':'good'},0.85,9,"info","Cache size reasonable."),
    R("P82","performance","Large Cache",[{'p':'cache_mb','o':'>=','v':50},{'p':'cache_mb','o':'<','v':100}],{'cache':'large'},0.80,8,"low","Cache growing. Add eviction."),
    R("P83","performance","Excessive Cache",[{'p':'cache_mb','o':'>=','v':100}],{'cache':'excessive'},0.85,7,"medium","Excessive cache. Implement limits."),
    R("P84","performance","Low BG Memory",[{'p':'bg_mem','o':'<','v':30}],{'bgm':'low'},0.85,9,"info","Low background memory."),
    R("P85","performance","High BG Memory",[{'p':'bg_mem','o':'>=','v':30}],{'bgm':'high'},0.85,7,"medium","High background memory. Release on background."),
    R("P86","performance","Good Render",[{'p':'render_ms','o':'<','v':16}],{'rend':'good'},0.90,9,"info","Render time within 16ms budget."),
    R("P87","performance","Slow Render",[{'p':'render_ms','o':'>=','v':16},{'p':'render_ms','o':'<','v':32}],{'rend':'slow'},0.85,7,"medium","Render >16ms. Frame drops likely."),
    R("P88","performance","Very Slow Render",[{'p':'render_ms','o':'>=','v':32}],{'rend':'very_slow'},0.90,6,"high","Render >32ms. Visible stuttering."),
    R("P89","performance","Thread Count OK",[{'p':'threads','o':'<','v':50}],{'thr':'ok'},0.80,8,"info","Thread count reasonable."),

    # STABILITY (72 rules)
    R("S01","stability","Perfect Stability",[{'p':'cr','o':'==','v':0}],{'sr':'perfect','ss':100},0.95,10,"info","Zero crashes. Perfect."),
    R("S02","stability","Excellent Stability",[{'p':'cr','o':'>','v':0},{'p':'cr','o':'<','v':0.1}],{'sr':'excellent','ss':95},0.95,10,"info","Near-zero crash rate."),
    R("S03","stability","Very Good",[{'p':'cr','o':'>=','v':0.1},{'p':'cr','o':'<','v':0.3}],{'sr':'very_good','ss':90},0.90,9,"info","Very good stability."),
    R("S04","stability","Good Stability",[{'p':'cr','o':'>=','v':0.3},{'p':'cr','o':'<','v':0.5}],{'sr':'good','ss':80},0.85,9,"info","Good stability."),
    R("S05","stability","Acceptable",[{'p':'cr','o':'>=','v':0.5},{'p':'cr','o':'<','v':1.0}],{'sr':'acceptable','ss':70},0.85,8,"low","Acceptable crash rate. Fix crashes."),
    R("S06","stability","Below Average",[{'p':'cr','o':'>=','v':1.0},{'p':'cr','o':'<','v':1.5}],{'sr':'below_avg','ss':55},0.90,7,"medium","Below average. Investigate top crashes."),
    R("S07","stability","Poor",[{'p':'cr','o':'>=','v':1.5},{'p':'cr','o':'<','v':2.0}],{'sr':'poor','ss':40},0.90,7,"high","Poor stability. Urgent fixes needed."),
    R("S08","stability","Very Poor",[{'p':'cr','o':'>=','v':2.0},{'p':'cr','o':'<','v':3.0}],{'sr':'very_poor','ss':25},0.95,6,"high","Very poor. Halt features, fix crashes."),
    R("S09","stability","Critical",[{'p':'cr','o':'>=','v':3.0},{'p':'cr','o':'<','v':5.0}],{'sr':'critical','ss':15},0.95,5,"critical","Critical instability."),
    R("S10","stability","Catastrophic",[{'p':'cr','o':'>=','v':5.0}],{'sr':'catastrophic','ss':5},0.95,5,"critical","Catastrophic crash rate. Pull from store."),
    R("S11","stability","Minimal Crashes",[{'p':'cr','o':'>=','v':0.05},{'p':'cr','o':'<','v':0.1}],{'sr':'minimal','ss':93},0.90,10,"info","Minimal crashes."),
    R("S12","stability","Moderate",[{'p':'cr','o':'>=','v':0.7},{'p':'cr','o':'<','v':1.0}],{'sr':'moderate','ss':65},0.85,8,"low","Moderate crashes."),
    R("S13","stability","Concerning",[{'p':'cr','o':'>=','v':1.2},{'p':'cr','o':'<','v':1.5}],{'sr':'concerning','ss':50},0.90,7,"medium","Concerning crash rate."),
    R("S14","stability","Alarming",[{'p':'cr','o':'>=','v':1.8},{'p':'cr','o':'<','v':2.0}],{'sr':'alarming','ss':35},0.90,6,"high","Alarming crashes."),
    R("S15","stability","Dangerous",[{'p':'cr','o':'>=','v':2.5},{'p':'cr','o':'<','v':3.0}],{'sr':'dangerous','ss':20},0.95,6,"high","Dangerous crash levels."),
    R("S16","stability","Borderline",[{'p':'cr','o':'>=','v':0.4},{'p':'cr','o':'<','v':0.5}],{'sr':'borderline','ss':75},0.85,8,"low","Borderline acceptable."),
    R("S17","stability","Slightly Unstable",[{'p':'cr','o':'>=','v':0.8},{'p':'cr','o':'<','v':1.0}],{'sr':'slight','ss':60},0.85,8,"low","Slightly unstable."),
    R("S18","stability","Mod Unstable",[{'p':'cr','o':'>=','v':1.5},{'p':'cr','o':'<','v':1.8}],{'sr':'mod_unstable','ss':45},0.90,7,"medium","Moderately unstable."),
    R("S19","stability","Severe",[{'p':'cr','o':'>=','v':3.5},{'p':'cr','o':'<','v':5.0}],{'sr':'severe','ss':10},0.95,5,"critical","Severely unstable."),
    R("S20","stability","Near Zero",[{'p':'cr','o':'>=','v':0.01},{'p':'cr','o':'<','v':0.05}],{'sr':'near_zero','ss':98},0.95,10,"info","Near-zero crash rate."),
    R("S21","stability","No ANR",[{'p':'anr','o':'<','v':0.05}],{'anr_s':'excellent','anr_sc':100},0.90,10,"info","No ANR issues."),
    R("S22","stability","Minor ANR",[{'p':'anr','o':'>=','v':0.05},{'p':'anr','o':'<','v':0.15}],{'anr_s':'minor','anr_sc':80},0.85,8,"low","Minor ANR. Review main thread."),
    R("S23","stability","Moderate ANR",[{'p':'anr','o':'>=','v':0.15},{'p':'anr','o':'<','v':0.5}],{'anr_s':'moderate','anr_sc':55},0.85,7,"medium","Moderate ANR. Use background threads."),
    R("S24","stability","Severe ANR",[{'p':'anr','o':'>=','v':0.5}],{'anr_s':'severe','anr_sc':25},0.90,6,"high","Severe ANR. App freezes."),
    R("S25","stability","Excellent MTBF",[{'p':'mtbf','o':'>=','v':100}],{'mtbf_r':'excellent','mtbf_sc':100},0.90,10,"info","Excellent MTBF (100+ hours)."),
    R("S26","stability","Good MTBF",[{'p':'mtbf','o':'>=','v':50},{'p':'mtbf','o':'<','v':100}],{'mtbf_r':'good','mtbf_sc':80},0.85,9,"info","Good MTBF."),
    R("S27","stability","Low MTBF",[{'p':'mtbf','o':'>=','v':10},{'p':'mtbf','o':'<','v':50}],{'mtbf_r':'low','mtbf_sc':50},0.85,7,"medium","Low MTBF (10-50 hours)."),
    R("S28","stability","Very Low MTBF",[{'p':'mtbf','o':'<','v':10}],{'mtbf_r':'very_low','mtbf_sc':20},0.90,6,"high","Very low MTBF (<10h)."),
    R("S29","stability","Good Error Handling",[{'p':'ueh','o':'<','v':0.01}],{'eh':'good','eh_sc':100},0.95,10,"info","Good error handling."),
    R("S30","stability","Some Unhandled",[{'p':'ueh','o':'>=','v':0.01},{'p':'ueh','o':'<','v':0.1}],{'eh':'some','eh_sc':75},0.85,8,"low","Some unhandled exceptions."),
    R("S31","stability","Poor Error Handling",[{'p':'ueh','o':'>=','v':0.1}],{'eh':'poor','eh_sc':35},0.90,6,"high","Poor error handling."),
    R("S32","stability","Data Safe",[{'p':'data_loss','o':'==','v':0}],{'ds':'safe'},0.90,10,"info","No data loss."),
    R("S33","stability","Data At Risk",[{'p':'data_loss','o':'>','v':0}],{'ds':'risk'},0.95,5,"critical","Data loss detected."),
    R("S34","stability","BG Stable",[{'p':'bg_crash','o':'<','v':0.1}],{'bg':'stable'},0.85,9,"info","Background stable."),
    R("S35","stability","BG Unstable",[{'p':'bg_crash','o':'>=','v':0.1}],{'bg':'unstable'},0.85,7,"medium","Background crashes."),
    R("S36","stability","No Watchdog",[{'p':'watchdog','o':'==','v':0}],{'wd':False},0.90,10,"info","No watchdog kills."),
    R("S37","stability","Watchdog Kills",[{'p':'watchdog','o':'>','v':0}],{'wd':True},0.90,6,"high","OS killing app."),
    R("S38","stability","Thread Safe",[{'p':'race','o':'==','v':0}],{'ts':'safe'},0.85,9,"info","Thread-safe code."),
    R("S39","stability","Thread Unsafe",[{'p':'race','o':'>','v':0}],{'ts':'unsafe'},0.90,6,"high","Race conditions."),
    R("S40","stability","No Deadlock",[{'p':'deadlock','o':'==','v':0}],{'dl':'free'},0.90,10,"info","No deadlocks."),
    R("S41","stability","Deadlock Risk",[{'p':'deadlock','o':'>','v':0}],{'dl':'risk'},0.95,5,"critical","Deadlocks detected."),
    R("S42","stability","Low OOM",[{'p':'oom','o':'<','v':0.05}],{'oom_s':'low'},0.85,9,"info","Low OOM rate."),
    R("S43","stability","High OOM",[{'p':'oom','o':'>=','v':0.05}],{'oom_s':'high'},0.90,6,"high","High OOM crash rate."),
    R("S44","stability","Network Resilient",[{'p':'net_err','o':'>=','v':0.95}],{'nr':'resilient'},0.85,9,"info","Handles network errors."),
    R("S45","stability","Network Fragile",[{'p':'net_err','o':'<','v':0.95}],{'nr':'fragile'},0.85,7,"medium","Poor network error handling."),
    R("S46","stability","Good Timeout",[{'p':'timeout_h','o':'>=','v':0.9}],{'th':'good'},0.85,9,"info","Good timeout handling."),
    R("S47","stability","Poor Timeout",[{'p':'timeout_h','o':'<','v':0.9}],{'th':'poor'},0.85,7,"medium","Poor timeout handling."),
    R("S48","stability","Good SSL",[{'p':'ssl_err','o':'<','v':0.01}],{'ssl':'good'},0.90,9,"info","SSL working correctly."),
    R("S49","stability","SSL Issues",[{'p':'ssl_err','o':'>=','v':0.01}],{'ssl':'issues'},0.90,6,"high","SSL errors."),
    R("S50","stability","Clean Shutdown",[{'p':'clean_shut','o':'>=','v':0.95}],{'shut':'clean'},0.85,9,"info","Clean shutdowns."),
    R("S51","stability","Dirty Shutdown",[{'p':'clean_shut','o':'<','v':0.95}],{'shut':'dirty'},0.85,7,"medium","Dirty shutdowns."),
    R("S52","stability","Config Robust",[{'p':'config_err','o':'<','v':0.01}],{'conf':'robust'},0.85,9,"info","Config handling robust."),
    R("S53","stability","Config Fragile",[{'p':'config_err','o':'>=','v':0.01}],{'conf':'fragile'},0.85,7,"medium","Config errors."),
    R("S54","stability","Low Retry",[{'p':'retry_rate','o':'<','v':0.1}],{'api_rel':'reliable'},0.85,9,"info","API calls succeed first try."),
    R("S55","stability","High Retry",[{'p':'retry_rate','o':'>=','v':0.1}],{'api_rel':'unreliable'},0.85,7,"medium","High API retry rate."),
    R("S56","stability","Graceful Degrade",[{'p':'graceful','o':'==','v':True}],{'gd':True},0.85,9,"info","Graceful degradation supported."),
    R("S57","stability","No Graceful",[{'p':'graceful','o':'==','v':False}],{'gd':False},0.85,7,"medium","No graceful degradation."),
    R("S58","stability","Long Session OK",[{'p':'long_crash','o':'<','v':0.5}],{'ls':'stable'},0.85,9,"info","Stable long sessions."),
    R("S59","stability","Long Session Bad",[{'p':'long_crash','o':'>=','v':0.5}],{'ls':'unstable'},0.85,7,"medium","Crashes in long sessions."),
    R("S60","stability","Rotation Safe",[{'p':'rot_crash','o':'<','v':0.05}],{'rot':'safe'},0.85,9,"info","Rotation handled."),
    R("S61","stability","Rotation Crash",[{'p':'rot_crash','o':'>=','v':0.05}],{'rot':'unsafe'},0.85,7,"medium","Crashes on rotation."),
    R("S62","stability","Permission Safe",[{'p':'perm_crash','o':'<','v':0.01}],{'perm':'safe'},0.85,9,"info","Permission handling OK."),
    R("S63","stability","Permission Crash",[{'p':'perm_crash','o':'>=','v':0.01}],{'perm':'unsafe'},0.90,6,"high","Crashes on permission deny."),
    R("S64","stability","Multi-Win Safe",[{'p':'mw_crash','o':'<','v':0.1}],{'mw':'safe'},0.80,8,"info","Multi-window stable."),
    R("S65","stability","Multi-Win Bad",[{'p':'mw_crash','o':'>=','v':0.1}],{'mw':'issues'},0.80,7,"medium","Multi-window crashes."),
    R("S66","stability","Locale Safe",[{'p':'locale_crash','o':'<','v':0.01}],{'loc':'safe'},0.85,9,"info","Locale handling safe."),
    R("S67","stability","Locale Crash",[{'p':'locale_crash','o':'>=','v':0.01}],{'loc':'unsafe'},0.85,7,"medium","Locale-related crashes."),
    R("S68","stability","Update Stable",[{'p':'update_spike','o':'==','v':False}],{'upd':'stable'},0.85,9,"info","Stable after updates."),
    R("S69","stability","Update Regression",[{'p':'update_spike','o':'==','v':True}],{'upd':'regression'},0.90,6,"high","Crash spike after update."),
    R("S70","stability","Good Recovery",[{'p':'err_recov','o':'>=','v':0.9}],{'recov':'good'},0.85,9,"info","Good error recovery."),
    R("S71","stability","Poor Recovery",[{'p':'err_recov','o':'<','v':0.9}],{'recov':'poor'},0.85,7,"medium","Poor error recovery."),
    R("S72","stability","Rare Restarts",[{'p':'restarts','o':'<=','v':2}],{'restart':'rare'},0.85,9,"info","Rare forced restarts."),

    # USABILITY (51 rules)
    R("U01","usability","Very Simple",[{'p':'icc','o':'<','v':5}],{'ir':'very_simple','us':100},0.95,10,"info","Very simple interface."),
    R("U02","usability","Simple",[{'p':'icc','o':'>=','v':5},{'p':'icc','o':'<','v':10}],{'ir':'simple','us':90},0.90,9,"info","Simple interface."),
    R("U03","usability","Moderate",[{'p':'icc','o':'>=','v':10},{'p':'icc','o':'<','v':15}],{'ir':'moderate','us':75},0.85,8,"low","Moderate complexity."),
    R("U04","usability","Above Average",[{'p':'icc','o':'>=','v':15},{'p':'icc','o':'<','v':20}],{'ir':'above_avg','us':65},0.85,8,"low","Above average complexity."),
    R("U05","usability","Complex",[{'p':'icc','o':'>=','v':20},{'p':'icc','o':'<','v':30}],{'ir':'complex','us':50},0.90,7,"medium","Complex interface. Streamline flows."),
    R("U06","usability","Very Complex",[{'p':'icc','o':'>=','v':30},{'p':'icc','o':'<','v':50}],{'ir':'very_complex','us':35},0.90,6,"high","Very complex. UX overhaul needed."),
    R("U07","usability","Overwhelming",[{'p':'icc','o':'>=','v':50}],{'ir':'overwhelming','us':15},0.95,5,"critical","Overwhelming. Full redesign needed."),
    R("U08","usability","Minimal",[{'p':'icc','o':'<','v':3}],{'ir':'minimal','us':100},0.95,10,"info","Minimal interface. Outstanding."),
    R("U09","usability","Clean",[{'p':'icc','o':'>=','v':7},{'p':'icc','o':'<','v':10}],{'ir':'clean','us':85},0.85,9,"info","Clean design."),
    R("U10","usability","Slightly Complex",[{'p':'icc','o':'>=','v':12},{'p':'icc','o':'<','v':15}],{'ir':'slight','us':70},0.85,8,"low","Slightly complex."),
    R("U11","usability","Borderline",[{'p':'icc','o':'>=','v':18},{'p':'icc','o':'<','v':20}],{'ir':'borderline','us':58},0.85,7,"medium","Borderline complex."),
    R("U12","usability","Shallow Nav",[{'p':'nav_depth','o':'<=','v':2}],{'nq':'excellent','ns':100},0.90,10,"info","Shallow nav. Easy to find features."),
    R("U13","usability","Good Nav",[{'p':'nav_depth','o':'>=','v':3},{'p':'nav_depth','o':'<=','v':3}],{'nq':'good','ns':85},0.85,9,"info","Good nav (3 levels)."),
    R("U14","usability","Moderate Nav",[{'p':'nav_depth','o':'>=','v':4},{'p':'nav_depth','o':'<=','v':4}],{'nq':'moderate','ns':65},0.85,8,"low","4 nav levels. Add shortcuts."),
    R("U15","usability","Deep Nav",[{'p':'nav_depth','o':'>=','v':5},{'p':'nav_depth','o':'<=','v':6}],{'nq':'deep','ns':45},0.85,7,"medium","Deep nav. Users get lost."),
    R("U16","usability","Very Deep Nav",[{'p':'nav_depth','o':'>','v':6}],{'nq':'very_deep','ns':25},0.90,6,"high","Very deep nav (>6 levels)."),
    R("U17","usability","High Completion",[{'p':'task_comp','o':'>=','v':0.9}],{'tc':'high','tcs':100},0.90,10,"info","High task completion (90%+)."),
    R("U18","usability","Good Completion",[{'p':'task_comp','o':'>=','v':0.75},{'p':'task_comp','o':'<','v':0.9}],{'tc':'good','tcs':75},0.85,8,"low","Good completion."),
    R("U19","usability","Low Completion",[{'p':'task_comp','o':'>=','v':0.5},{'p':'task_comp','o':'<','v':0.75}],{'tc':'low','tcs':45},0.85,7,"medium","Low completion. UX confusing."),
    R("U20","usability","Very Low Completion",[{'p':'task_comp','o':'<','v':0.5}],{'tc':'very_low','tcs':20},0.90,6,"high","Very low completion (<50%)."),
    R("U21","usability","Fast Interactions",[{'p':'interact_sec','o':'<','v':2}],{'is':'fast'},0.85,9,"info","Quick interactions."),
    R("U22","usability","Slow Interactions",[{'p':'interact_sec','o':'>=','v':2},{'p':'interact_sec','o':'<','v':5}],{'is':'moderate'},0.80,8,"low","Moderate interaction time."),
    R("U23","usability","Very Slow Interact",[{'p':'interact_sec','o':'>=','v':5}],{'is':'slow'},0.85,7,"medium","Very slow interactions."),
    R("U24","usability","Good Touch",[{'p':'touch_dp','o':'>=','v':44}],{'tt':'good'},0.85,9,"info","Touch targets meet 44dp."),
    R("U25","usability","Small Touch",[{'p':'touch_dp','o':'<','v':44}],{'tt':'small'},0.85,7,"medium","Touch targets too small."),
    R("U26","usability","Readable Text",[{'p':'font_sp','o':'>=','v':14}],{'read':'good'},0.85,9,"info","Text readable (14sp+)."),
    R("U27","usability","Small Text",[{'p':'font_sp','o':'<','v':14}],{'read':'poor'},0.85,7,"medium","Text too small."),
    R("U28","usability","Good Contrast",[{'p':'contrast','o':'>=','v':4.5}],{'con':'wcag_aa'},0.90,9,"info","Meets WCAG AA."),
    R("U29","usability","Poor Contrast",[{'p':'contrast','o':'<','v':4.5}],{'con':'fail'},0.90,7,"medium","Fails WCAG contrast."),
    R("U30","usability","A11y Support",[{'p':'a11y','o':'==','v':True}],{'a11y_s':'yes'},0.85,9,"info","Screen reader compatible."),
    R("U31","usability","No A11y",[{'p':'a11y','o':'==','v':False}],{'a11y_s':'no'},0.85,7,"medium","No screen reader support."),
    R("U32","usability","Loading Shown",[{'p':'loading_ind','o':'==','v':True}],{'load_ux':'good'},0.85,9,"info","Loading indicators present."),
    R("U33","usability","No Loading",[{'p':'loading_ind','o':'==','v':False}],{'load_ux':'poor'},0.85,7,"medium","No loading indicators."),
    R("U34","usability","Friendly Errors",[{'p':'friendly_err','o':'==','v':True}],{'err_ux':'good'},0.85,9,"info","User-friendly errors."),
    R("U35","usability","Technical Errors",[{'p':'friendly_err','o':'==','v':False}],{'err_ux':'poor'},0.85,7,"medium","Technical errors shown."),
    R("U36","usability","Has Onboarding",[{'p':'onboard','o':'==','v':True}],{'onb':'yes'},0.80,8,"info","Onboarding present."),
    R("U37","usability","No Onboarding",[{'p':'onboard','o':'==','v':False}],{'onb':'no'},0.80,7,"low","No onboarding."),
    R("U38","usability","Has Search",[{'p':'search','o':'==','v':True}],{'srch':'yes'},0.80,8,"info","Search available."),
    R("U39","usability","No Search",[{'p':'search','o':'==','v':False}],{'srch':'no'},0.80,7,"low","No search function."),
    R("U40","usability","Consistent Design",[{'p':'design_score','o':'>=','v':0.8}],{'des':'consistent'},0.85,9,"info","Consistent design."),
    R("U41","usability","Inconsistent",[{'p':'design_score','o':'<','v':0.8}],{'des':'inconsistent'},0.85,7,"medium","Inconsistent design."),
    R("U42","usability","Has Undo",[{'p':'undo','o':'==','v':True}],{'undo_s':'yes'},0.80,8,"info","Undo available."),
    R("U43","usability","No Undo",[{'p':'undo','o':'==','v':False}],{'undo_s':'no'},0.80,7,"low","No undo function."),
    R("U44","usability","Haptic FB",[{'p':'haptic','o':'==','v':True}],{'hap':'yes'},0.75,8,"info","Haptic feedback enabled."),
    R("U45","usability","Gesture Nav",[{'p':'gesture','o':'==','v':True}],{'gest':'yes'},0.75,8,"info","Gesture navigation."),
    R("U46","usability","Dark Mode",[{'p':'dark_mode','o':'==','v':True}],{'dm':'yes'},0.80,8,"info","Dark mode available."),
    R("U47","usability","No Dark Mode",[{'p':'dark_mode','o':'==','v':False}],{'dm':'no'},0.80,7,"low","No dark mode."),
    R("U48","usability","Multi-Lang",[{'p':'langs','o':'>=','v':2}],{'l10n':'multi'},0.80,8,"info","Multi-language support."),
    R("U49","usability","Single Lang",[{'p':'langs','o':'==','v':1}],{'l10n':'single'},0.80,7,"low","Single language only."),
    R("U50","usability","Inline Validation",[{'p':'inline_val','o':'==','v':True}],{'form':'good'},0.85,8,"info","Inline form validation."),
    R("U51","usability","No Validation",[{'p':'inline_val','o':'==','v':False}],{'form':'poor'},0.85,7,"medium","No inline validation."),

    # FAULT TOLERANCE (35 rules)
    R("F01","fault_tolerance","Instant Recovery",[{'p':'mrt','o':'<','v':0.5}],{'rr':'instant','rs':100},0.95,10,"info","Instant recovery (<0.5s)."),
    R("F02","fault_tolerance","Fast Recovery",[{'p':'mrt','o':'>=','v':0.5},{'p':'mrt','o':'<','v':1.0}],{'rr':'fast','rs':90},0.90,9,"info","Fast recovery (0.5-1s)."),
    R("F03","fault_tolerance","Good Recovery",[{'p':'mrt','o':'>=','v':1.0},{'p':'mrt','o':'<','v':2.0}],{'rr':'good','rs':80},0.85,9,"info","Good recovery (1-2s)."),
    R("F04","fault_tolerance","Moderate Recovery",[{'p':'mrt','o':'>=','v':2.0},{'p':'mrt','o':'<','v':3.0}],{'rr':'moderate','rs':65},0.85,8,"low","Moderate recovery."),
    R("F05","fault_tolerance","Slow Recovery",[{'p':'mrt','o':'>=','v':3.0},{'p':'mrt','o':'<','v':5.0}],{'rr':'slow','rs':45},0.90,7,"medium","Slow recovery (3-5s)."),
    R("F06","fault_tolerance","Very Slow Recovery",[{'p':'mrt','o':'>=','v':5.0},{'p':'mrt','o':'<','v':10.0}],{'rr':'very_slow','rs':25},0.90,6,"high","Very slow recovery."),
    R("F07","fault_tolerance","Failed Recovery",[{'p':'mrt','o':'>=','v':10.0}],{'rr':'failed','rs':10},0.95,5,"critical","Recovery >10s. Unusable."),
    R("F08","fault_tolerance","Excellent Offline",[{'p':'offline','o':'>=','v':0.8}],{'oc':'excellent','os':100},0.90,10,"info","Excellent offline (80%+)."),
    R("F09","fault_tolerance","Good Offline",[{'p':'offline','o':'>=','v':0.5},{'p':'offline','o':'<','v':0.8}],{'oc':'good','os':75},0.85,9,"info","Good offline (50-80%)."),
    R("F10","fault_tolerance","Limited Offline",[{'p':'offline','o':'>=','v':0.2},{'p':'offline','o':'<','v':0.5}],{'oc':'limited','os':50},0.85,8,"low","Limited offline. Cache more."),
    R("F11","fault_tolerance","Minimal Offline",[{'p':'offline','o':'>=','v':0.01},{'p':'offline','o':'<','v':0.2}],{'oc':'minimal','os':30},0.85,7,"medium","Minimal offline."),
    R("F12","fault_tolerance","No Offline",[{'p':'offline','o':'<','v':0.01}],{'oc':'none','os':10},0.90,7,"medium","No offline support."),
    R("F13","fault_tolerance","State Preserved",[{'p':'state_pres','o':'>=','v':0.95}],{'sh':'excellent','st_sc':100},0.90,10,"info","State preserved (95%+)."),
    R("F14","fault_tolerance","Good State",[{'p':'state_pres','o':'>=','v':0.8},{'p':'state_pres','o':'<','v':0.95}],{'sh':'good','st_sc':75},0.85,8,"low","Good state handling."),
    R("F15","fault_tolerance","Poor State",[{'p':'state_pres','o':'<','v':0.8}],{'sh':'poor','st_sc':40},0.90,7,"medium","Poor state preservation."),
    R("F16","fault_tolerance","Auto Retry OK",[{'p':'retry_succ','o':'>=','v':0.9}],{'rm':'effective'},0.85,9,"info","Auto-retry effective."),
    R("F17","fault_tolerance","Poor Retry",[{'p':'retry_succ','o':'<','v':0.9}],{'rm':'ineffective'},0.85,7,"medium","Poor auto-retry."),
    R("F18","fault_tolerance","Good Cache",[{'p':'cache_hit','o':'>=','v':0.8}],{'ch':'effective'},0.85,9,"info","Good cache (80%+ hit)."),
    R("F19","fault_tolerance","Poor Cache",[{'p':'cache_hit','o':'<','v':0.8}],{'ch':'ineffective'},0.85,7,"medium","Poor cache hit rate."),
    R("F20","fault_tolerance","Net Switch OK",[{'p':'net_switch','o':'==','v':True}],{'ns_h':'handled'},0.85,9,"info","Network transitions smooth."),
    R("F21","fault_tolerance","Net Switch Fail",[{'p':'net_switch','o':'==','v':False}],{'ns_h':'fails'},0.85,7,"medium","Network transitions fail."),
    R("F22","fault_tolerance","Graceful Timeout",[{'p':'timeout_g','o':'==','v':True}],{'to':'graceful'},0.85,9,"info","Graceful timeouts."),
    R("F23","fault_tolerance","Abrupt Timeout",[{'p':'timeout_g','o':'==','v':False}],{'to':'abrupt'},0.85,7,"medium","Abrupt timeouts."),
    R("F24","fault_tolerance","Sync Reliable",[{'p':'sync','o':'==','v':True}],{'sync_s':'reliable'},0.85,9,"info","Data sync reliable."),
    R("F25","fault_tolerance","No Sync",[{'p':'sync','o':'==','v':False}],{'sync_s':'unreliable'},0.85,7,"medium","No sync conflict resolution."),
    R("F26","fault_tolerance","Battery Save OK",[{'p':'bat_save','o':'==','v':True}],{'bsm':'handled'},0.80,8,"info","Battery save mode handled."),
    R("F27","fault_tolerance","No Battery Save",[{'p':'bat_save','o':'==','v':False}],{'bsm':'unhandled'},0.80,7,"low","No battery save handling."),
    R("F28","fault_tolerance","Perm Deny OK",[{'p':'perm_deny','o':'==','v':True}],{'pd':'graceful'},0.85,9,"info","Permission denials handled."),
    R("F29","fault_tolerance","Perm Deny Crash",[{'p':'perm_deny','o':'==','v':False}],{'pd':'crashes'},0.90,6,"high","Crashes on permission deny."),
    R("F30","fault_tolerance","Low Mem Handle",[{'p':'low_mem','o':'==','v':True}],{'lm':'handled'},0.85,9,"info","Low memory handled."),
    R("F31","fault_tolerance","No Low Mem",[{'p':'low_mem','o':'==','v':False}],{'lm':'unhandled'},0.85,7,"medium","No low memory handling."),
    R("F32","fault_tolerance","Interrupt OK",[{'p':'interrupt','o':'>=','v':0.9}],{'int':'good'},0.85,9,"info","Handles interrupts well."),
    R("F33","fault_tolerance","Poor Interrupt",[{'p':'interrupt','o':'<','v':0.9}],{'int':'poor'},0.85,7,"medium","Poor interrupt recovery."),
    R("F34","fault_tolerance","BG Refresh OK",[{'p':'bg_refresh','o':'==','v':True}],{'bgr':'reliable'},0.80,8,"info","Background refresh reliable."),
    R("F35","fault_tolerance","BG Refresh Fail",[{'p':'bg_refresh','o':'==','v':False}],{'bgr':'unreliable'},0.80,7,"medium","Background refresh unreliable."),
]

print(f"DiagNova loaded {len(RULES)} rules")

def forward_chain(facts, max_iter=1000):
    wm = facts.copy()
    fired = set()
    fired_det = []
    i = 0
    while i < max_iter:
        app = [r for r in RULES if r.matches(wm) and r.rule_id not in fired]
        if not app: break
        sel = max(app, key=lambda r: r.priority)
        wm.update(sel.consequences)
        fired.add(sel.rule_id)
        fired_det.append({'rule_id':sel.rule_id,'name':sel.name,'dimension':sel.dimension,'severity':sel.severity,'confidence':sel.confidence,'recommendation':sel.recommendation})
        i += 1
    wm['fired_rules'] = fired_det
    wm['iterations'] = i
    wm['total_rules_fired'] = len(fired)
    return wm

@app.route('/')
def index():
    return jsonify({'service':'DiagNova Expert System API','version':'1.0.0','rules_loaded':len(RULES),'status':'running'})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status':'healthy','rules_loaded':len(RULES),'version':'1.0.0'})

@app.route('/api/rules', methods=['GET'])
def get_rules():
    dims = {}
    for r in RULES:
        dims[r.dimension] = dims.get(r.dimension, 0) + 1
    return jsonify({'total':len(RULES), 'by_dimension':dims})

@app.route('/api/assess', methods=['POST'])
def assess():
    data = request.json
    if not data: return jsonify({'error':'No data'}), 400
    perf = data.get('performance', {})
    stab = data.get('stability', {})
    usa = data.get('usability', {})
    ft = data.get('fault_tolerance', {})
    for d in [perf, stab, usa]:
        for k in list(d.keys()):
            try: d[k] = float(d[k])
            except: pass
    rts_raw = ft.get('recovery_times', [0])
    rts = []
    for x in rts_raw:
        try: rts.append(float(x))
        except: pass
    if not rts: rts = [0]
    mem_avail = max(perf.get('memory_available', 1), 1)
    sessions = max(stab.get('sessions', 1), 1)
    comp_rate = max(usa.get('completion_rate', 0.01), 0.01)
    facts = {
        'st': perf.get('startup_time', 0),
        'mer': (perf.get('memory_used', 0) / mem_avail) * 100,
        'frc': (perf.get('frame_rate', 60) / 60) * 100,
        'cr': (stab.get('crashes', 0) / sessions) * 100,
        'icc': (usa.get('screens', 1) * usa.get('interactions_per_task', 1)) / comp_rate,
        'mrt': sum(rts) / len(rts),
    }
    result = forward_chain(facts)
    ps = [result.get('ss', 50), result.get('ms', 50), result.get('fs', 50)]
    perf_avg = round(sum(ps)/len(ps), 2)
    stab_sc = result.get('ss', 50)
    if 'sr' in result: stab_sc = result.get('ss', 50)
    usa_sc = result.get('us', 50)
    ft_sc = result.get('rs', 50)
    crs = round((perf_avg + stab_sc + usa_sc + ft_sc) / 4, 2)
    issues = []
    recs = []
    seen = set()
    for fr in result.get('fired_rules', []):
        if fr['severity'] in ['critical','high','medium']:
            issues.append({'dimension':fr['dimension'],'severity':fr['severity'],'issue':fr['name'],'rule_id':fr['rule_id']})
        if fr['recommendation'] not in seen:
            seen.add(fr['recommendation'])
            recs.append(fr['recommendation'])
    return jsonify({
        'app_name': data.get('app_name','Unknown'),
        'platform': data.get('platform','Android'),
        'composite_score': crs,
        'dimensions': {'performance':perf_avg,'stability':stab_sc,'usability':usa_sc,'fault_tolerance':ft_sc},
        'metrics': {'startup_time_ms':facts['st'],'memory_efficiency_ratio':round(facts['mer'],2),'frame_rate_consistency':round(facts['frc'],2),'crash_rate':round(facts['cr'],4),'interface_complexity':round(facts['icc'],2),'mean_recovery_time':round(facts['mrt'],2)},
        'issues': issues,
        'recommendations': recs[:10],
        'rules_fired': result.get('total_rules_fired',0),
        'timestamp': datetime.utcnow().isoformat()+'Z'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')
