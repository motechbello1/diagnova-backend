import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================
# INLINE INFERENCE ENGINE + RULES (deployment-safe, no imports)
# ============================================================

class Rule:
    def __init__(self, rule_id, dimension, name, conditions, consequences, confidence, priority, severity, recommendation):
        self.rule_id = rule_id
        self.dimension = dimension
        self.name = name
        self.conditions = conditions
        self.consequences = consequences
        self.confidence = confidence
        self.priority = priority
        self.severity = severity
        self.recommendation = recommendation

    def matches(self, facts):
        for c in self.conditions:
            param, op, val = c['parameter'], c['operator'], c['value']
            if param not in facts:
                return False
            fv = facts[param]
            if op == '>' and not (fv > val): return False
            if op == '<' and not (fv < val): return False
            if op == '>=' and not (fv >= val): return False
            if op == '<=' and not (fv <= val): return False
            if op == '==' and not (fv == val): return False
            if op == '!=' and not (fv != val): return False
        return True

# 247 PRODUCTION RULES
RULES = [
    # === PERFORMANCE: Startup Time (15 rules) ===
    Rule("PERF_001","performance","Excellent Startup",[{'parameter':'startup_time','operator':'<','value':1000}],{'startup_performance':'excellent','startup_score':100},0.95,10,"info","Startup time excellent. Maintain current optimization."),
    Rule("PERF_002","performance","Good Startup",[{'parameter':'startup_time','operator':'>=','value':1000},{'parameter':'startup_time','operator':'<','value':2000}],{'startup_performance':'good','startup_score':85},0.90,9,"info","Startup time good but can be optimized further."),
    Rule("PERF_003","performance","Acceptable Startup",[{'parameter':'startup_time','operator':'>=','value':2000},{'parameter':'startup_time','operator':'<','value':3000}],{'startup_performance':'acceptable','startup_score':70},0.85,8,"low","Acceptable startup. Consider reducing initialization overhead."),
    Rule("PERF_004","performance","Slow Startup",[{'parameter':'startup_time','operator':'>=','value':3000},{'parameter':'startup_time','operator':'<','value':5000}],{'startup_performance':'slow','startup_score':50},0.90,7,"medium","Slow startup. Optimize initialization, defer non-critical loading, use lazy init."),
    Rule("PERF_005","performance","Very Slow Startup",[{'parameter':'startup_time','operator':'>=','value':5000}],{'startup_performance':'very_slow','startup_score':25},0.95,6,"high","Critically slow startup. Implement splash screen, async loading, reduce deps."),
    Rule("PERF_006","performance","Startup Needs Work",[{'parameter':'startup_time','operator':'>=','value':2000},{'parameter':'startup_time','operator':'<','value':2500}],{'startup_performance':'needs_work','startup_score':75},0.85,8,"low","Startup borderline. Minor optimizations recommended."),
    Rule("PERF_007","performance","Critical Startup Failure",[{'parameter':'startup_time','operator':'>=','value':8000}],{'startup_performance':'failure','startup_score':10},0.95,5,"critical","App takes >8s to start. Users will abandon. Major refactor needed."),
    Rule("PERF_008","performance","Near-Instant Startup",[{'parameter':'startup_time','operator':'<','value':500}],{'startup_performance':'instant','startup_score':100},0.95,10,"info","Near-instant startup (<500ms). Outstanding performance."),
    Rule("PERF_009","performance","Moderate Slow Startup",[{'parameter':'startup_time','operator':'>=','value':4000},{'parameter':'startup_time','operator':'<','value':5000}],{'startup_performance':'moderate_slow','startup_score':45},0.85,7,"medium","4-5s startup. Users notice delay. Optimize aggressively."),
    Rule("PERF_010","performance","Slow on Budget Devices",[{'parameter':'startup_time','operator':'>=','value':3500},{'parameter':'startup_time','operator':'<','value':6000}],{'startup_performance':'slow_budget','startup_score':55},0.80,7,"medium","Slow on budget devices. Optimize for constrained hardware."),
    Rule("PERF_011","performance","Acceptable Fast",[{'parameter':'startup_time','operator':'>=','value':1500},{'parameter':'startup_time','operator':'<','value':2000}],{'startup_performance':'acceptable_fast','startup_score':80},0.85,9,"info","Fast enough but room for improvement."),
    Rule("PERF_012","performance","Cold Start Issue",[{'parameter':'startup_time','operator':'>=','value':5000},{'parameter':'startup_time','operator':'<','value':8000}],{'startup_performance':'cold_start_issue','startup_score':35},0.90,6,"high","Cold start too slow. Reduce initialization dependencies."),
    Rule("PERF_013","performance","Warm Start OK",[{'parameter':'startup_time','operator':'>=','value':1000},{'parameter':'startup_time','operator':'<','value':1500}],{'startup_performance':'warm_ok','startup_score':88},0.90,9,"info","Warm start acceptable."),
    Rule("PERF_014","performance","Sub-Second Startup",[{'parameter':'startup_time','operator':'>=','value':500},{'parameter':'startup_time','operator':'<','value':1000}],{'startup_performance':'sub_second','startup_score':95},0.90,10,"info","Sub-second startup. Excellent user experience."),
    Rule("PERF_015","performance","Borderline Slow",[{'parameter':'startup_time','operator':'>=','value':2500},{'parameter':'startup_time','operator':'<','value':3000}],{'startup_performance':'borderline','startup_score':65},0.85,8,"low","Borderline slow. Users may notice. Quick wins available."),

    # === PERFORMANCE: Memory (15 rules) ===
    Rule("PERF_016","performance","Excellent Memory",[{'parameter':'memory_efficiency_ratio','operator':'<','value':10}],{'memory_performance':'excellent','memory_score':100},0.95,10,"info","Memory usage excellent (<10%). Outstanding efficiency."),
    Rule("PERF_017","performance","Good Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':10},{'parameter':'memory_efficiency_ratio','operator':'<','value':20}],{'memory_performance':'good','memory_score':85},0.90,9,"info","Good memory efficiency. Continue monitoring."),
    Rule("PERF_018","performance","Acceptable Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':20},{'parameter':'memory_efficiency_ratio','operator':'<','value':30}],{'memory_performance':'acceptable','memory_score':70},0.85,8,"low","Acceptable memory. Review for optimization opportunities."),
    Rule("PERF_019","performance","High Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':30},{'parameter':'memory_efficiency_ratio','operator':'<','value':45}],{'memory_performance':'high','memory_score':50},0.90,7,"medium","High memory usage. Implement caching strategies, release unused resources."),
    Rule("PERF_020","performance","Excessive Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':45},{'parameter':'memory_efficiency_ratio','operator':'<','value':60}],{'memory_performance':'excessive','memory_score':30},0.90,6,"high","Excessive memory. Check for leaks, reduce cache size, optimize images."),
    Rule("PERF_021","performance","Critical Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':60}],{'memory_performance':'critical','memory_score':15},0.95,5,"critical","Critical memory usage (>60%). App will be killed by OS. Immediate fix needed."),
    Rule("PERF_022","performance","Lean Memory",[{'parameter':'memory_efficiency_ratio','operator':'<','value':5}],{'memory_performance':'lean','memory_score':100},0.95,10,"info","Extremely lean memory usage. Exceptional optimization."),
    Rule("PERF_023","performance","Moderate Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':15},{'parameter':'memory_efficiency_ratio','operator':'<','value':20}],{'memory_performance':'moderate','memory_score':80},0.85,9,"info","Moderate memory usage. Acceptable for most apps."),
    Rule("PERF_024","performance","Above Average Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':25},{'parameter':'memory_efficiency_ratio','operator':'<','value':30}],{'memory_performance':'above_avg','memory_score':65},0.85,8,"low","Above average memory. Consider optimization."),
    Rule("PERF_025","performance","Borderline High Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':35},{'parameter':'memory_efficiency_ratio','operator':'<','value':40}],{'memory_performance':'borderline_high','memory_score':55},0.85,7,"medium","Borderline high memory. Risk of OS termination on low-end devices."),
    Rule("PERF_026","performance","Very High Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':40},{'parameter':'memory_efficiency_ratio','operator':'<','value':45}],{'memory_performance':'very_high','memory_score':45},0.90,7,"medium","Very high memory. Profile and optimize immediately."),
    Rule("PERF_027","performance","Dangerous Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':50},{'parameter':'memory_efficiency_ratio','operator':'<','value':60}],{'memory_performance':'dangerous','memory_score':25},0.90,6,"high","Dangerous memory levels. OOM crashes imminent."),
    Rule("PERF_028","performance","Memory Efficient",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':5},{'parameter':'memory_efficiency_ratio','operator':'<','value':10}],{'memory_performance':'efficient','memory_score':95},0.90,10,"info","Very memory efficient. Well-optimized app."),
    Rule("PERF_029","performance","Slightly High Memory",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':20},{'parameter':'memory_efficiency_ratio','operator':'<','value':25}],{'memory_performance':'slightly_high','memory_score':75},0.85,8,"low","Slightly high memory but manageable."),
    Rule("PERF_030","performance","Memory Warning Zone",[{'parameter':'memory_efficiency_ratio','operator':'>=','value':55},{'parameter':'memory_efficiency_ratio','operator':'<','value':60}],{'memory_performance':'warning_zone','memory_score':20},0.90,6,"high","Memory in warning zone. Crashes likely on many devices."),

    # === PERFORMANCE: Frame Rate (15 rules) ===
    Rule("PERF_031","performance","Perfect Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':98}],{'ui_performance':'perfect','frame_score':100},0.95,10,"info","Perfect frame rate. Buttery smooth UI."),
    Rule("PERF_032","performance","Excellent Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':95},{'parameter':'frame_rate_consistency','operator':'<','value':98}],{'ui_performance':'excellent','frame_score':95},0.90,10,"info","Excellent frame rate. Smooth experience."),
    Rule("PERF_033","performance","Good Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':90},{'parameter':'frame_rate_consistency','operator':'<','value':95}],{'ui_performance':'good','frame_score':85},0.90,9,"info","Good frame rate. Minor optimizations possible."),
    Rule("PERF_034","performance","Acceptable Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':83},{'parameter':'frame_rate_consistency','operator':'<','value':90}],{'ui_performance':'acceptable','frame_score':75},0.85,8,"low","Acceptable frame rate. Some users may notice occasional drops."),
    Rule("PERF_035","performance","Below Average Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':75},{'parameter':'frame_rate_consistency','operator':'<','value':83}],{'ui_performance':'below_avg','frame_score':60},0.85,8,"low","Below average frame rate. Optimize rendering pipeline."),
    Rule("PERF_036","performance","Poor Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':60},{'parameter':'frame_rate_consistency','operator':'<','value':75}],{'ui_performance':'poor','frame_score':45},0.90,7,"medium","Poor frame rate. Users will notice jank. Reduce overdraw, optimize layouts."),
    Rule("PERF_037","performance","Very Poor Frame Rate",[{'parameter':'frame_rate_consistency','operator':'>=','value':50},{'parameter':'frame_rate_consistency','operator':'<','value':60}],{'ui_performance':'very_poor','frame_score':30},0.90,6,"high","Very poor frame rate. App feels sluggish. Major UI optimization needed."),
    Rule("PERF_038","performance","Unacceptable Frame Rate",[{'parameter':'frame_rate_consistency','operator':'<','value':50}],{'ui_performance':'unacceptable','frame_score':15},0.95,5,"critical","Unacceptable frame rate (<50%). App unusable. Complete UI rewrite needed."),
    Rule("PERF_039","performance","Near Perfect Frames",[{'parameter':'frame_rate_consistency','operator':'>=','value':96},{'parameter':'frame_rate_consistency','operator':'<','value':98}],{'ui_performance':'near_perfect','frame_score':97},0.90,10,"info","Near-perfect frames. Exceptional UI performance."),
    Rule("PERF_040","performance","Mostly Smooth",[{'parameter':'frame_rate_consistency','operator':'>=','value':87},{'parameter':'frame_rate_consistency','operator':'<','value':90}],{'ui_performance':'mostly_smooth','frame_score':80},0.85,9,"info","Mostly smooth. Rare frame drops acceptable."),
    Rule("PERF_041","performance","Noticeable Jank",[{'parameter':'frame_rate_consistency','operator':'>=','value':70},{'parameter':'frame_rate_consistency','operator':'<','value':75}],{'ui_performance':'jank','frame_score':55},0.85,7,"medium","Noticeable jank. Profile UI thread, reduce layout complexity."),
    Rule("PERF_042","performance","Significant Jank",[{'parameter':'frame_rate_consistency','operator':'>=','value':65},{'parameter':'frame_rate_consistency','operator':'<','value':70}],{'ui_performance':'sig_jank','frame_score':50},0.90,7,"medium","Significant jank. Hardware acceleration may help."),
    Rule("PERF_043","performance","Choppy UI",[{'parameter':'frame_rate_consistency','operator':'>=','value':55},{'parameter':'frame_rate_consistency','operator':'<','value':60}],{'ui_performance':'choppy','frame_score':35},0.90,6,"high","Choppy UI. Users will leave. Immediate optimization needed."),
    Rule("PERF_044","performance","Slideshow Mode",[{'parameter':'frame_rate_consistency','operator':'>=','value':50},{'parameter':'frame_rate_consistency','operator':'<','value':55}],{'ui_performance':'slideshow','frame_score':25},0.90,6,"high","Frame rate so low UI feels like slideshow."),
    Rule("PERF_045","performance","Borderline Smooth",[{'parameter':'frame_rate_consistency','operator':'>=','value':80},{'parameter':'frame_rate_consistency','operator':'<','value':83}],{'ui_performance':'borderline_smooth','frame_score':70},0.85,8,"low","Borderline smooth. Quick optimizations can improve noticeably."),

    # === PERFORMANCE: Network/API (15 rules) ===
    Rule("PERF_046","performance","Fast API Response",[{'parameter':'avg_api_response_ms','operator':'<','value':200}],{'api_performance':'fast','api_score':100},0.90,10,"info","API responses fast (<200ms). Excellent backend performance."),
    Rule("PERF_047","performance","Good API Response",[{'parameter':'avg_api_response_ms','operator':'>=','value':200},{'parameter':'avg_api_response_ms','operator':'<','value':500}],{'api_performance':'good','api_score':85},0.85,9,"info","API response time good."),
    Rule("PERF_048","performance","Slow API Response",[{'parameter':'avg_api_response_ms','operator':'>=','value':500},{'parameter':'avg_api_response_ms','operator':'<','value':1000}],{'api_performance':'slow','api_score':60},0.85,8,"low","API responses slow. Optimize queries, add caching."),
    Rule("PERF_049","performance","Very Slow API",[{'parameter':'avg_api_response_ms','operator':'>=','value':1000},{'parameter':'avg_api_response_ms','operator':'<','value':3000}],{'api_performance':'very_slow','api_score':40},0.90,7,"medium","API very slow (1-3s). Users experience noticeable delays."),
    Rule("PERF_050","performance","Timeout-Risk API",[{'parameter':'avg_api_response_ms','operator':'>=','value':3000}],{'api_performance':'timeout_risk','api_score':20},0.90,6,"high","API at timeout risk (>3s). Backend optimization critical."),
    Rule("PERF_051","performance","Instant API",[{'parameter':'avg_api_response_ms','operator':'<','value':100}],{'api_performance':'instant','api_score':100},0.95,10,"info","Instant API responses. Edge caching or local data likely."),
    Rule("PERF_052","performance","Moderate API",[{'parameter':'avg_api_response_ms','operator':'>=','value':300},{'parameter':'avg_api_response_ms','operator':'<','value':500}],{'api_performance':'moderate','api_score':75},0.85,8,"info","API moderately fast. Acceptable for most use cases."),
    Rule("PERF_053","performance","High Latency API",[{'parameter':'avg_api_response_ms','operator':'>=','value':2000},{'parameter':'avg_api_response_ms','operator':'<','value':3000}],{'api_performance':'high_latency','api_score':30},0.90,7,"medium","High API latency. Consider CDN, query optimization."),
    Rule("PERF_054","performance","Acceptable API",[{'parameter':'avg_api_response_ms','operator':'>=','value':150},{'parameter':'avg_api_response_ms','operator':'<','value':200}],{'api_performance':'acceptable','api_score':90},0.85,9,"info","API responses acceptable. Near-optimal."),
    Rule("PERF_055","performance","Slightly Slow API",[{'parameter':'avg_api_response_ms','operator':'>=','value':500},{'parameter':'avg_api_response_ms','operator':'<','value':750}],{'api_performance':'slightly_slow','api_score':65},0.85,8,"low","Slightly slow API. Pagination and caching recommended."),
    Rule("PERF_056","performance","Laggy API",[{'parameter':'avg_api_response_ms','operator':'>=','value':750},{'parameter':'avg_api_response_ms','operator':'<','value':1000}],{'api_performance':'laggy','api_score':55},0.85,8,"medium","Laggy API. Users feel the wait."),
    Rule("PERF_057","performance","Battery Drain - API",[{'parameter':'avg_api_response_ms','operator':'>=','value':1500},{'parameter':'avg_api_response_ms','operator':'<','value':2000}],{'api_performance':'battery_drain','api_score':35},0.85,7,"medium","Slow API causes excess battery drain from radio wake."),
    Rule("PERF_058","performance","Fast Enough API",[{'parameter':'avg_api_response_ms','operator':'>=','value':100},{'parameter':'avg_api_response_ms','operator':'<','value':150}],{'api_performance':'fast_enough','api_score':95},0.90,10,"info","API fast enough for real-time feel."),
    Rule("PERF_059","performance","Network-Bound",[{'parameter':'avg_api_response_ms','operator':'>=','value':1000},{'parameter':'avg_api_response_ms','operator':'<','value':1500}],{'api_performance':'network_bound','api_score':45},0.85,7,"medium","Network-bound performance. Reduce payload sizes."),
    Rule("PERF_060","performance","Borderline API",[{'parameter':'avg_api_response_ms','operator':'>=','value':400},{'parameter':'avg_api_response_ms','operator':'<','value':500}],{'api_performance':'borderline','api_score':70},0.85,8,"low","Borderline API speed. Close to threshold."),

    # === PERFORMANCE: Battery/CPU/Storage (29 rules) ===
    Rule("PERF_061","performance","Low Battery Impact",[{'parameter':'battery_drain_percent_per_hour','operator':'<','value':3}],{'battery_impact':'low','battery_score':100},0.90,10,"info","Low battery impact. Energy efficient app."),
    Rule("PERF_062","performance","Moderate Battery",[{'parameter':'battery_drain_percent_per_hour','operator':'>=','value':3},{'parameter':'battery_drain_percent_per_hour','operator':'<','value':8}],{'battery_impact':'moderate','battery_score':70},0.85,8,"low","Moderate battery drain. Review background processes."),
    Rule("PERF_063","performance","High Battery Drain",[{'parameter':'battery_drain_percent_per_hour','operator':'>=','value':8},{'parameter':'battery_drain_percent_per_hour','operator':'<','value':15}],{'battery_impact':'high','battery_score':40},0.90,7,"medium","High battery drain. Reduce GPS, network, and sensor usage."),
    Rule("PERF_064","performance","Battery Killer",[{'parameter':'battery_drain_percent_per_hour','operator':'>=','value':15}],{'battery_impact':'killer','battery_score':15},0.95,5,"critical","Battery killer app. Users will uninstall. Major optimization needed."),
    Rule("PERF_065","performance","Low CPU Usage",[{'parameter':'avg_cpu_percent','operator':'<','value':10}],{'cpu_impact':'low','cpu_score':100},0.90,10,"info","Low CPU usage. Efficient processing."),
    Rule("PERF_066","performance","Moderate CPU",[{'parameter':'avg_cpu_percent','operator':'>=','value':10},{'parameter':'avg_cpu_percent','operator':'<','value':30}],{'cpu_impact':'moderate','cpu_score':75},0.85,8,"low","Moderate CPU usage. Acceptable for feature-rich apps."),
    Rule("PERF_067","performance","High CPU",[{'parameter':'avg_cpu_percent','operator':'>=','value':30},{'parameter':'avg_cpu_percent','operator':'<','value':60}],{'cpu_impact':'high','cpu_score':45},0.90,7,"medium","High CPU usage. Causes thermal throttling. Optimize algorithms."),
    Rule("PERF_068","performance","CPU Hog",[{'parameter':'avg_cpu_percent','operator':'>=','value':60}],{'cpu_impact':'hog','cpu_score':20},0.95,5,"critical","CPU hog. Device will overheat. Background processing mandatory."),
    Rule("PERF_069","performance","Small App Size",[{'parameter':'app_size_mb','operator':'<','value':30}],{'size_impact':'small','size_score':100},0.90,10,"info","Small app size. Quick download and install."),
    Rule("PERF_070","performance","Medium App Size",[{'parameter':'app_size_mb','operator':'>=','value':30},{'parameter':'app_size_mb','operator':'<','value':100}],{'size_impact':'medium','size_score':80},0.85,9,"info","Medium app size. Acceptable for most users."),
    Rule("PERF_071","performance","Large App",[{'parameter':'app_size_mb','operator':'>=','value':100},{'parameter':'app_size_mb','operator':'<','value':250}],{'size_impact':'large','size_score':55},0.85,8,"low","Large app. Users on limited storage may avoid. Review asset sizes."),
    Rule("PERF_072","performance","Very Large App",[{'parameter':'app_size_mb','operator':'>=','value':250}],{'size_impact':'very_large','size_score':30},0.90,7,"medium","Very large app (>250MB). Remove unused assets, use on-demand downloads."),
    Rule("PERF_073","performance","Minimal Battery",[{'parameter':'battery_drain_percent_per_hour','operator':'<','value':1}],{'battery_impact':'minimal','battery_score':100},0.95,10,"info","Minimal battery impact. Outstanding."),
    Rule("PERF_074","performance","Light Battery",[{'parameter':'battery_drain_percent_per_hour','operator':'>=','value':1},{'parameter':'battery_drain_percent_per_hour','operator':'<','value':3}],{'battery_impact':'light','battery_score':90},0.90,9,"info","Light battery usage. Well optimized."),
    Rule("PERF_075","performance","Heavy Battery",[{'parameter':'battery_drain_percent_per_hour','operator':'>=','value':10},{'parameter':'battery_drain_percent_per_hour','operator':'<','value':15}],{'battery_impact':'heavy','battery_score':30},0.90,6,"high","Heavy battery drain. Users will complain."),
    Rule("PERF_076","performance","Tiny App",[{'parameter':'app_size_mb','operator':'<','value':10}],{'size_impact':'tiny','size_score':100},0.95,10,"info","Tiny app. Instant install."),
    Rule("PERF_077","performance","Compact App",[{'parameter':'app_size_mb','operator':'>=','value':10},{'parameter':'app_size_mb','operator':'<','value':30}],{'size_impact':'compact','size_score':95},0.90,10,"info","Compact app. Good size management."),
    Rule("PERF_078","performance","Slightly Large",[{'parameter':'app_size_mb','operator':'>=','value':80},{'parameter':'app_size_mb','operator':'<','value':100}],{'size_impact':'slightly_large','size_score':70},0.85,8,"low","Slightly large. Consider splitting features."),
    Rule("PERF_079","performance","Low Idle CPU",[{'parameter':'avg_cpu_percent','operator':'<','value':5}],{'cpu_impact':'idle_efficient','cpu_score':100},0.95,10,"info","Very low CPU at idle. No background waste."),
    Rule("PERF_080","performance","Moderate Idle CPU",[{'parameter':'avg_cpu_percent','operator':'>=','value':15},{'parameter':'avg_cpu_percent','operator':'<','value':30}],{'cpu_impact':'moderate_active','cpu_score':65},0.85,8,"low","Moderate CPU. Check for unnecessary background work."),
    Rule("PERF_081","performance","Thermal Risk CPU",[{'parameter':'avg_cpu_percent','operator':'>=','value':50},{'parameter':'avg_cpu_percent','operator':'<','value':60}],{'cpu_impact':'thermal_risk','cpu_score':30},0.90,6,"high","Thermal risk from high CPU. Device may throttle."),
    Rule("PERF_082","performance","Network Efficient",[{'parameter':'network_requests_per_session','operator':'<','value':10}],{'network_efficiency':'excellent'},0.85,9,"info","Few network requests. Efficient data fetching."),
    Rule("PERF_083","performance","Network Heavy",[{'parameter':'network_requests_per_session','operator':'>=','value':10},{'parameter':'network_requests_per_session','operator':'<','value':30}],{'network_efficiency':'moderate'},0.80,8,"low","Moderate network requests. Batch where possible."),
    Rule("PERF_084","performance","Network Excessive",[{'parameter':'network_requests_per_session','operator':'>=','value':30}],{'network_efficiency':'excessive'},0.85,7,"medium","Excessive network requests. Implement request batching."),
    Rule("PERF_085","performance","Good Payload Size",[{'parameter':'avg_payload_kb','operator':'<','value':50}],{'payload_efficiency':'good'},0.85,9,"info","Small API payloads. Network efficient."),
    Rule("PERF_086","performance","Large Payloads",[{'parameter':'avg_payload_kb','operator':'>=','value':50},{'parameter':'avg_payload_kb','operator':'<','value':200}],{'payload_efficiency':'acceptable'},0.80,8,"low","Moderate payloads. Compress responses."),
    Rule("PERF_087","performance","Bloated Payloads",[{'parameter':'avg_payload_kb','operator':'>=','value':200}],{'payload_efficiency':'bloated'},0.85,7,"medium","Bloated payloads. Implement pagination, selective fields."),
    Rule("PERF_088","performance","Fast Storage IO",[{'parameter':'storage_write_ms','operator':'<','value':50}],{'storage_performance':'fast'},0.85,9,"info","Fast storage I/O operations."),
    Rule("PERF_089","performance","Slow Storage IO",[{'parameter':'storage_write_ms','operator':'>=','value':50}],{'storage_performance':'slow'},0.85,7,"medium","Slow storage I/O. Use async writes, batch operations."),

    # === STABILITY: Crash Rate (20 rules) ===
    Rule("STAB_001","stability","Excellent Stability",[{'parameter':'crash_rate','operator':'<','value':0.1}],{'stability_rating':'excellent','stability_score':100},0.95,10,"info","Crash rate <0.1%. Excellent stability."),
    Rule("STAB_002","stability","Very Good Stability",[{'parameter':'crash_rate','operator':'>=','value':0.1},{'parameter':'crash_rate','operator':'<','value':0.3}],{'stability_rating':'very_good','stability_score':90},0.90,9,"info","Very good stability (0.1-0.3% crash rate)."),
    Rule("STAB_003","stability","Good Stability",[{'parameter':'crash_rate','operator':'>=','value':0.3},{'parameter':'crash_rate','operator':'<','value':0.5}],{'stability_rating':'good','stability_score':80},0.85,9,"info","Good stability. Continue monitoring."),
    Rule("STAB_004","stability","Acceptable Stability",[{'parameter':'crash_rate','operator':'>=','value':0.5},{'parameter':'crash_rate','operator':'<','value':1.0}],{'stability_rating':'acceptable','stability_score':70},0.85,8,"low","Acceptable crash rate. Prioritize crash fixes."),
    Rule("STAB_005","stability","Below Average Stability",[{'parameter':'crash_rate','operator':'>=','value':1.0},{'parameter':'crash_rate','operator':'<','value':1.5}],{'stability_rating':'below_avg','stability_score':55},0.90,7,"medium","Below average stability. Investigate top crash causes."),
    Rule("STAB_006","stability","Poor Stability",[{'parameter':'crash_rate','operator':'>=','value':1.5},{'parameter':'crash_rate','operator':'<','value':2.0}],{'stability_rating':'poor','stability_score':40},0.90,7,"high","Poor stability. Urgent crash analysis needed."),
    Rule("STAB_007","stability","Very Poor Stability",[{'parameter':'crash_rate','operator':'>=','value':2.0},{'parameter':'crash_rate','operator':'<','value':3.0}],{'stability_rating':'very_poor','stability_score':25},0.95,6,"high","Very poor stability. Halt new features, fix crashes."),
    Rule("STAB_008","stability","Critical Instability",[{'parameter':'crash_rate','operator':'>=','value':3.0},{'parameter':'crash_rate','operator':'<','value':5.0}],{'stability_rating':'critical','stability_score':15},0.95,5,"critical","Critical instability. App unusable for many users."),
    Rule("STAB_009","stability","Catastrophic Instability",[{'parameter':'crash_rate','operator':'>=','value':5.0}],{'stability_rating':'catastrophic','stability_score':5},0.95,5,"critical","Catastrophic crash rate (>5%). Pull from store. Emergency fix."),
    Rule("STAB_010","stability","Zero Crashes",[{'parameter':'crash_rate','operator':'==','value':0}],{'stability_rating':'perfect','stability_score':100},0.95,10,"info","Zero crashes. Perfect stability."),
    Rule("STAB_011","stability","Near-Zero Crashes",[{'parameter':'crash_rate','operator':'>=','value':0.01},{'parameter':'crash_rate','operator':'<','value':0.05}],{'stability_rating':'near_perfect','stability_score':98},0.95,10,"info","Near-zero crash rate. Outstanding stability."),
    Rule("STAB_012","stability","Minimal Crashes",[{'parameter':'crash_rate','operator':'>=','value':0.05},{'parameter':'crash_rate','operator':'<','value':0.1}],{'stability_rating':'minimal','stability_score':95},0.90,10,"info","Minimal crashes. Well-tested app."),
    Rule("STAB_013","stability","Moderate Crashes",[{'parameter':'crash_rate','operator':'>=','value':0.7},{'parameter':'crash_rate','operator':'<','value':1.0}],{'stability_rating':'moderate','stability_score':65},0.85,8,"low","Moderate crash rate. Address in next sprint."),
    Rule("STAB_014","stability","Concerning Crashes",[{'parameter':'crash_rate','operator':'>=','value':1.2},{'parameter':'crash_rate','operator':'<','value':1.5}],{'stability_rating':'concerning','stability_score':50},0.90,7,"medium","Concerning crash rate. Top priority in backlog."),
    Rule("STAB_015","stability","Alarming Crashes",[{'parameter':'crash_rate','operator':'>=','value':1.8},{'parameter':'crash_rate','operator':'<','value':2.0}],{'stability_rating':'alarming','stability_score':35},0.90,6,"high","Alarming crash rate. Dedicate team to stability."),
    Rule("STAB_016","stability","Dangerous Crashes",[{'parameter':'crash_rate','operator':'>=','value':2.5},{'parameter':'crash_rate','operator':'<','value':3.0}],{'stability_rating':'dangerous','stability_score':20},0.95,6,"high","Dangerous crash levels. User retention at risk."),
    Rule("STAB_017","stability","Borderline Acceptable",[{'parameter':'crash_rate','operator':'>=','value':0.4},{'parameter':'crash_rate','operator':'<','value':0.5}],{'stability_rating':'borderline','stability_score':75},0.85,8,"low","Borderline acceptable. Close to good stability."),
    Rule("STAB_018","stability","Slightly Unstable",[{'parameter':'crash_rate','operator':'>=','value':0.8},{'parameter':'crash_rate','operator':'<','value':1.0}],{'stability_rating':'slightly_unstable','stability_score':60},0.85,8,"low","Slightly unstable. Crash-free rate needs improvement."),
    Rule("STAB_019","stability","Moderately Unstable",[{'parameter':'crash_rate','operator':'>=','value':1.5},{'parameter':'crash_rate','operator':'<','value':1.8}],{'stability_rating':'mod_unstable','stability_score':45},0.90,7,"medium","Moderately unstable. Implement crash reporting."),
    Rule("STAB_020","stability","Severely Unstable",[{'parameter':'crash_rate','operator':'>=','value':3.5},{'parameter':'crash_rate','operator':'<','value':5.0}],{'stability_rating':'severe','stability_score':10},0.95,5,"critical","Severely unstable. Consider rollback to stable version."),

    # === STABILITY: ANR/Error Handling/MTBF (52 rules) ===
    Rule("STAB_021","stability","No ANR",[{'parameter':'anr_rate','operator':'<','value':0.05}],{'anr_status':'excellent','anr_score':100},0.90,10,"info","No ANR issues. App stays responsive."),
    Rule("STAB_022","stability","Minor ANR",[{'parameter':'anr_rate','operator':'>=','value':0.05},{'parameter':'anr_rate','operator':'<','value':0.15}],{'anr_status':'minor','anr_score':80},0.85,8,"low","Minor ANR issues. Review long-running main thread operations."),
    Rule("STAB_023","stability","Moderate ANR",[{'parameter':'anr_rate','operator':'>=','value':0.15},{'parameter':'anr_rate','operator':'<','value':0.5}],{'anr_status':'moderate','anr_score':55},0.85,7,"medium","Moderate ANR rate. Move operations to background threads."),
    Rule("STAB_024","stability","Severe ANR",[{'parameter':'anr_rate','operator':'>=','value':0.5}],{'anr_status':'severe','anr_score':25},0.90,6,"high","Severe ANR issues. App freezes frequently. Urgent threading fix."),
    Rule("STAB_025","stability","Excellent MTBF",[{'parameter':'mtbf_hours','operator':'>=','value':100}],{'mtbf_rating':'excellent','mtbf_score':100},0.90,10,"info","Excellent MTBF (100+ hours). Very reliable."),
    Rule("STAB_026","stability","Good MTBF",[{'parameter':'mtbf_hours','operator':'>=','value':50},{'parameter':'mtbf_hours','operator':'<','value':100}],{'mtbf_rating':'good','mtbf_score':80},0.85,9,"info","Good MTBF (50-100 hours)."),
    Rule("STAB_027","stability","Low MTBF",[{'parameter':'mtbf_hours','operator':'>=','value':10},{'parameter':'mtbf_hours','operator':'<','value':50}],{'mtbf_rating':'low','mtbf_score':50},0.85,7,"medium","Low MTBF. Failures every 10-50 hours of use."),
    Rule("STAB_028","stability","Very Low MTBF",[{'parameter':'mtbf_hours','operator':'<','value':10}],{'mtbf_rating':'very_low','mtbf_score':20},0.90,6,"high","Very low MTBF (<10 hours). App fails frequently."),
    Rule("STAB_029","stability","No Unhandled Exceptions",[{'parameter':'unhandled_exception_rate','operator':'<','value':0.01}],{'error_handling':'excellent','error_score':100},0.95,10,"info","Excellent error handling. Nearly all exceptions caught."),
    Rule("STAB_030","stability","Some Unhandled",[{'parameter':'unhandled_exception_rate','operator':'>=','value':0.01},{'parameter':'unhandled_exception_rate','operator':'<','value':0.1}],{'error_handling':'good','error_score':75},0.85,8,"low","Good error handling. Few unhandled exceptions."),
    Rule("STAB_031","stability","Poor Error Handling",[{'parameter':'unhandled_exception_rate','operator':'>=','value':0.1}],{'error_handling':'poor','error_score':35},0.90,6,"high","Poor error handling. Implement global error handlers."),
    Rule("STAB_032","stability","Good Error Recovery",[{'parameter':'error_recovery_rate','operator':'>=','value':0.9}],{'recovery_quality':'good'},0.85,9,"info","Good error recovery rate (90%+)."),
    Rule("STAB_033","stability","Poor Error Recovery",[{'parameter':'error_recovery_rate','operator':'<','value':0.9}],{'recovery_quality':'poor'},0.85,7,"medium","Poor error recovery. Implement retry logic and fallbacks."),
    Rule("STAB_034","stability","Data Corruption Risk",[{'parameter':'data_loss_incidents','operator':'>','value':0}],{'data_safety':'at_risk'},0.95,5,"critical","Data loss incidents detected. Implement transactions and backups."),
    Rule("STAB_035","stability","Safe Data Handling",[{'parameter':'data_loss_incidents','operator':'==','value':0}],{'data_safety':'safe'},0.90,10,"info","No data loss incidents. Data handling is safe."),
    Rule("STAB_036","stability","Background Crash Free",[{'parameter':'background_crash_rate','operator':'<','value':0.1}],{'bg_stability':'stable'},0.85,9,"info","Background processes stable."),
    Rule("STAB_037","stability","Background Crashes",[{'parameter':'background_crash_rate','operator':'>=','value':0.1}],{'bg_stability':'unstable'},0.85,7,"medium","Background crashes detected. Review services and workers."),
    Rule("STAB_038","stability","Watchdog Kills",[{'parameter':'watchdog_kills','operator':'>','value':0}],{'watchdog_issue':True},0.90,6,"high","OS watchdog killing app. Reduce background resource usage."),
    Rule("STAB_039","stability","No Watchdog Issues",[{'parameter':'watchdog_kills','operator':'==','value':0}],{'watchdog_issue':False},0.90,10,"info","No watchdog terminations. Good background behavior."),
    Rule("STAB_040","stability","Frequent Restarts",[{'parameter':'forced_restarts_per_day','operator':'>','value':2}],{'restart_issue':True},0.85,7,"medium","Frequent forced restarts. Investigate root cause."),
    Rule("STAB_041","stability","Rare Restarts",[{'parameter':'forced_restarts_per_day','operator':'<=','value':2}],{'restart_issue':False},0.85,9,"info","Rare forced restarts. App maintains state well."),
    Rule("STAB_042","stability","Thread Safety OK",[{'parameter':'race_condition_incidents','operator':'==','value':0}],{'thread_safety':'safe'},0.85,9,"info","No race conditions detected. Thread-safe code."),
    Rule("STAB_043","stability","Thread Safety Issue",[{'parameter':'race_condition_incidents','operator':'>','value':0}],{'thread_safety':'unsafe'},0.90,6,"high","Race conditions detected. Add synchronization."),
    Rule("STAB_044","stability","Deadlock Free",[{'parameter':'deadlock_incidents','operator':'==','value':0}],{'deadlock_status':'free'},0.90,10,"info","No deadlocks detected."),
    Rule("STAB_045","stability","Deadlock Risk",[{'parameter':'deadlock_incidents','operator':'>','value':0}],{'deadlock_status':'risk'},0.95,5,"critical","Deadlocks detected. Review lock ordering."),
    Rule("STAB_046","stability","Stable on Update",[{'parameter':'post_update_crash_spike','operator':'==','value':False}],{'update_stability':'stable'},0.85,9,"info","App stable after updates."),
    Rule("STAB_047","stability","Update Regression",[{'parameter':'post_update_crash_spike','operator':'==','value':True}],{'update_stability':'regression'},0.90,6,"high","Crash spike after update. Regression introduced."),
    Rule("STAB_048","stability","Low OOM Rate",[{'parameter':'oom_crash_rate','operator':'<','value':0.05}],{'oom_status':'low'},0.85,9,"info","Low out-of-memory crash rate."),
    Rule("STAB_049","stability","High OOM Rate",[{'parameter':'oom_crash_rate','operator':'>=','value':0.05}],{'oom_status':'high'},0.90,6,"high","High OOM crash rate. Reduce memory footprint."),
    Rule("STAB_050","stability","Network Error Resilient",[{'parameter':'network_error_handling_rate','operator':'>=','value':0.95}],{'network_resilience':'resilient'},0.85,9,"info","Handles network errors gracefully (95%+)."),
    Rule("STAB_051","stability","Network Error Fragile",[{'parameter':'network_error_handling_rate','operator':'<','value':0.95}],{'network_resilience':'fragile'},0.85,7,"medium","Poor network error handling. Add retry and timeout logic."),
    Rule("STAB_052","stability","API Timeout Handling",[{'parameter':'timeout_handling_rate','operator':'>=','value':0.9}],{'timeout_handling':'good'},0.85,9,"info","Good timeout handling (90%+)."),
    Rule("STAB_053","stability","Poor Timeout Handling",[{'parameter':'timeout_handling_rate','operator':'<','value':0.9}],{'timeout_handling':'poor'},0.85,7,"medium","Poor timeout handling. Implement proper timeout recovery."),
    Rule("STAB_054","stability","Good SSL Pinning",[{'parameter':'ssl_error_rate','operator':'<','value':0.01}],{'ssl_status':'good'},0.90,9,"info","SSL/TLS working correctly."),
    Rule("STAB_055","stability","SSL Issues",[{'parameter':'ssl_error_rate','operator':'>=','value':0.01}],{'ssl_status':'issues'},0.90,6,"high","SSL errors detected. Review certificate configuration."),
    Rule("STAB_056","stability","Clean Shutdown",[{'parameter':'clean_shutdown_rate','operator':'>=','value':0.95}],{'shutdown_quality':'clean'},0.85,9,"info","App shuts down cleanly (95%+ of the time)."),
    Rule("STAB_057","stability","Dirty Shutdowns",[{'parameter':'clean_shutdown_rate','operator':'<','value':0.95}],{'shutdown_quality':'dirty'},0.85,7,"medium","Frequent dirty shutdowns. Save state before exit."),
    Rule("STAB_058","stability","Config Robust",[{'parameter':'config_error_rate','operator':'<','value':0.01}],{'config_robustness':'good'},0.85,9,"info","Configuration handling robust."),
    Rule("STAB_059","stability","Config Fragile",[{'parameter':'config_error_rate','operator':'>=','value':0.01}],{'config_robustness':'fragile'},0.85,7,"medium","Configuration errors occurring. Add validation and defaults."),
    Rule("STAB_060","stability","Low Retry Rate",[{'parameter':'api_retry_rate','operator':'<','value':0.1}],{'api_reliability':'reliable'},0.85,9,"info","API calls succeed on first try."),
    Rule("STAB_061","stability","High Retry Rate",[{'parameter':'api_retry_rate','operator':'>=','value':0.1}],{'api_reliability':'unreliable'},0.85,7,"medium","High API retry rate. Investigate backend reliability."),
    Rule("STAB_062","stability","Graceful Degradation",[{'parameter':'graceful_degradation_supported','operator':'==','value':True}],{'degradation_support':True},0.85,9,"info","App supports graceful degradation."),
    Rule("STAB_063","stability","No Graceful Degradation",[{'parameter':'graceful_degradation_supported','operator':'==','value':False}],{'degradation_support':False},0.85,7,"medium","No graceful degradation. Implement fallback modes."),
    Rule("STAB_064","stability","Stable Long Sessions",[{'parameter':'long_session_crash_rate','operator':'<','value':0.5}],{'long_session_stability':'stable'},0.85,9,"info","Stable during long sessions."),
    Rule("STAB_065","stability","Unstable Long Sessions",[{'parameter':'long_session_crash_rate','operator':'>=','value':0.5}],{'long_session_stability':'unstable'},0.85,7,"medium","Crashes increase during long sessions. Memory leak likely."),
    Rule("STAB_066","stability","Multi-Window Safe",[{'parameter':'multi_window_crash_rate','operator':'<','value':0.1}],{'multi_window':'safe'},0.80,8,"info","Multi-window mode stable."),
    Rule("STAB_067","stability","Multi-Window Issues",[{'parameter':'multi_window_crash_rate','operator':'>=','value':0.1}],{'multi_window':'issues'},0.80,7,"medium","Crashes in multi-window mode. Test split-screen."),
    Rule("STAB_068","stability","Rotation Safe",[{'parameter':'rotation_crash_rate','operator':'<','value':0.05}],{'rotation_handling':'safe'},0.85,9,"info","Screen rotation handled safely."),
    Rule("STAB_069","stability","Rotation Crashes",[{'parameter':'rotation_crash_rate','operator':'>=','value':0.05}],{'rotation_handling':'unsafe'},0.85,7,"medium","Crashes on rotation. Save/restore instance state properly."),
    Rule("STAB_070","stability","Permission Handling OK",[{'parameter':'permission_crash_rate','operator':'<','value':0.01}],{'permission_handling':'safe'},0.85,9,"info","Permission handling robust."),
    Rule("STAB_071","stability","Permission Crashes",[{'parameter':'permission_crash_rate','operator':'>=','value':0.01}],{'permission_handling':'unsafe'},0.90,6,"high","Crashes when permissions denied. Handle all permission states."),
    Rule("STAB_072","stability","Locale Safe",[{'parameter':'locale_crash_rate','operator':'<','value':0.01}],{'locale_handling':'safe'},0.85,9,"info","App handles different locales safely."),

    # === USABILITY: Interface Complexity (18 rules) ===
    Rule("USA_001","usability","Very Simple Interface",[{'parameter':'interface_complexity_coefficient','operator':'<','value':5}],{'interface_rating':'very_simple','usability_score':100},0.95,10,"info","Very simple interface. Excellent usability."),
    Rule("USA_002","usability","Simple Interface",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':5},{'parameter':'interface_complexity_coefficient','operator':'<','value':10}],{'interface_rating':'simple','usability_score':90},0.90,9,"info","Simple, intuitive interface."),
    Rule("USA_003","usability","Moderate Complexity",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':10},{'parameter':'interface_complexity_coefficient','operator':'<','value':15}],{'interface_rating':'moderate','usability_score':75},0.85,8,"low","Moderate interface complexity. Consider simplifying flows."),
    Rule("USA_004","usability","Above Average Complexity",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':15},{'parameter':'interface_complexity_coefficient','operator':'<','value':20}],{'interface_rating':'above_avg','usability_score':65},0.85,8,"low","Above average complexity. Reduce interaction steps."),
    Rule("USA_005","usability","Complex Interface",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':20},{'parameter':'interface_complexity_coefficient','operator':'<','value':30}],{'interface_rating':'complex','usability_score':50},0.90,7,"medium","Complex interface. Streamline user flows, reduce screen count."),
    Rule("USA_006","usability","Very Complex Interface",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':30},{'parameter':'interface_complexity_coefficient','operator':'<','value':50}],{'interface_rating':'very_complex','usability_score':35},0.90,6,"high","Very complex interface. Major UX overhaul recommended."),
    Rule("USA_007","usability","Overwhelming Interface",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':50}],{'interface_rating':'overwhelming','usability_score':15},0.95,5,"critical","Overwhelming interface. Users will abandon app. Full redesign needed."),
    Rule("USA_008","usability","Minimal Interface",[{'parameter':'interface_complexity_coefficient','operator':'<','value':3}],{'interface_rating':'minimal','usability_score':100},0.95,10,"info","Minimal interface. Outstanding simplicity."),
    Rule("USA_009","usability","Clean Interface",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':7},{'parameter':'interface_complexity_coefficient','operator':'<','value':10}],{'interface_rating':'clean','usability_score':85},0.85,9,"info","Clean interface design. Good usability."),
    Rule("USA_010","usability","Slightly Complex",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':12},{'parameter':'interface_complexity_coefficient','operator':'<','value':15}],{'interface_rating':'slightly_complex','usability_score':70},0.85,8,"low","Slightly complex. Quick UX wins available."),
    Rule("USA_011","usability","Borderline Complex",[{'parameter':'interface_complexity_coefficient','operator':'>=','value':18},{'parameter':'interface_complexity_coefficient','operator':'<','value':20}],{'interface_rating':'borderline_complex','usability_score':58},0.85,7,"medium","Borderline complex. User testing recommended."),

    # === USABILITY: Navigation (15 rules) ===
    Rule("USA_012","usability","Shallow Navigation",[{'parameter':'navigation_depth','operator':'<=','value':2}],{'nav_quality':'excellent','nav_score':100},0.90,10,"info","Shallow navigation. Easy to find features."),
    Rule("USA_013","usability","Good Navigation",[{'parameter':'navigation_depth','operator':'>=','value':3},{'parameter':'navigation_depth','operator':'<=','value':3}],{'nav_quality':'good','nav_score':85},0.85,9,"info","Good navigation depth (3 levels). Acceptable."),
    Rule("USA_014","usability","Moderate Navigation",[{'parameter':'navigation_depth','operator':'>=','value':4},{'parameter':'navigation_depth','operator':'<=','value':4}],{'nav_quality':'moderate','nav_score':65},0.85,8,"low","4 navigation levels. Getting deep. Add shortcuts."),
    Rule("USA_015","usability","Deep Navigation",[{'parameter':'navigation_depth','operator':'>=','value':5},{'parameter':'navigation_depth','operator':'<=','value':6}],{'nav_quality':'deep','nav_score':45},0.85,7,"medium","Deep navigation (5-6 levels). Users get lost. Flatten structure."),
    Rule("USA_016","usability","Very Deep Navigation",[{'parameter':'navigation_depth','operator':'>','value':6}],{'nav_quality':'very_deep','nav_score':25},0.90,6,"high","Very deep navigation (>6 levels). Critical UX issue."),
    Rule("USA_017","usability","High Task Completion",[{'parameter':'task_completion_rate','operator':'>=','value':0.9}],{'task_success':'high','task_score':100},0.90,10,"info","High task completion rate (90%+). Intuitive app."),
    Rule("USA_018","usability","Good Task Completion",[{'parameter':'task_completion_rate','operator':'>=','value':0.75},{'parameter':'task_completion_rate','operator':'<','value':0.9}],{'task_success':'good','task_score':75},0.85,8,"low","Good task completion. Some users struggle."),
    Rule("USA_019","usability","Low Task Completion",[{'parameter':'task_completion_rate','operator':'>=','value':0.5},{'parameter':'task_completion_rate','operator':'<','value':0.75}],{'task_success':'low','task_score':45},0.85,7,"medium","Low task completion. UX confusing users. Usability testing needed."),
    Rule("USA_020","usability","Very Low Task Completion",[{'parameter':'task_completion_rate','operator':'<','value':0.5}],{'task_success':'very_low','task_score':20},0.90,6,"high","Very low task completion (<50%). App fails its purpose."),
    Rule("USA_021","usability","Fast Interactions",[{'parameter':'avg_interaction_time_sec','operator':'<','value':2}],{'interaction_speed':'fast'},0.85,9,"info","Quick user interactions. Responsive interface."),
    Rule("USA_022","usability","Slow Interactions",[{'parameter':'avg_interaction_time_sec','operator':'>=','value':2},{'parameter':'avg_interaction_time_sec','operator':'<','value':5}],{'interaction_speed':'moderate'},0.80,8,"low","Moderate interaction time. Optimize touch targets and feedback."),
    Rule("USA_023","usability","Very Slow Interactions",[{'parameter':'avg_interaction_time_sec','operator':'>=','value':5}],{'interaction_speed':'slow'},0.85,7,"medium","Very slow interactions. Users struggle with the interface."),
    Rule("USA_024","usability","Good Touch Targets",[{'parameter':'min_touch_target_dp','operator':'>=','value':44}],{'touch_targets':'good'},0.85,9,"info","Touch targets meet 44dp minimum. Easy to tap."),
    Rule("USA_025","usability","Small Touch Targets",[{'parameter':'min_touch_target_dp','operator':'<','value':44}],{'touch_targets':'small'},0.85,7,"medium","Touch targets too small (<44dp). Increase sizes for accessibility."),
    Rule("USA_026","usability","Good Text Readability",[{'parameter':'min_font_size_sp','operator':'>=','value':14}],{'readability':'good'},0.85,9,"info","Text readable (14sp+). Good for accessibility."),

    # === USABILITY: Accessibility/Feedback (25 rules) ===
    Rule("USA_027","usability","Small Text",[{'parameter':'min_font_size_sp','operator':'<','value':14}],{'readability':'poor'},0.85,7,"medium","Text too small (<14sp). Increase for readability."),
    Rule("USA_028","usability","Good Contrast",[{'parameter':'contrast_ratio','operator':'>=','value':4.5}],{'contrast':'wcag_aa'},0.90,9,"info","Meets WCAG AA contrast (4.5:1+). Accessible."),
    Rule("USA_029","usability","Poor Contrast",[{'parameter':'contrast_ratio','operator':'<','value':4.5}],{'contrast':'fails_wcag'},0.90,7,"medium","Fails WCAG AA contrast. Increase color contrast."),
    Rule("USA_030","usability","Screen Reader Support",[{'parameter':'screen_reader_compatible','operator':'==','value':True}],{'accessibility':'supported'},0.85,9,"info","Screen reader compatible. Accessible app."),
    Rule("USA_031","usability","No Screen Reader",[{'parameter':'screen_reader_compatible','operator':'==','value':False}],{'accessibility':'unsupported'},0.85,7,"medium","No screen reader support. Add content descriptions."),
    Rule("USA_032","usability","Good Loading Feedback",[{'parameter':'loading_indicators_present','operator':'==','value':True}],{'loading_ux':'good'},0.85,9,"info","Loading indicators present. Good feedback."),
    Rule("USA_033","usability","No Loading Feedback",[{'parameter':'loading_indicators_present','operator':'==','value':False}],{'loading_ux':'poor'},0.85,7,"medium","No loading indicators. Users don't know if app is working."),
    Rule("USA_034","usability","Good Error Messages",[{'parameter':'user_friendly_errors','operator':'==','value':True}],{'error_ux':'good'},0.85,9,"info","User-friendly error messages. Good UX."),
    Rule("USA_035","usability","Technical Errors Shown",[{'parameter':'user_friendly_errors','operator':'==','value':False}],{'error_ux':'poor'},0.85,7,"medium","Technical errors shown to users. Use friendly messages."),
    Rule("USA_036","usability","Has Onboarding",[{'parameter':'onboarding_present','operator':'==','value':True}],{'onboarding':'present'},0.80,8,"info","Onboarding flow present. Helps new users."),
    Rule("USA_037","usability","No Onboarding",[{'parameter':'onboarding_present','operator':'==','value':False}],{'onboarding':'absent'},0.80,7,"low","No onboarding. Add tutorial for complex features."),
    Rule("USA_038","usability","Good Search",[{'parameter':'search_available','operator':'==','value':True}],{'search_ux':'good'},0.80,8,"info","Search functionality available. Easy content discovery."),
    Rule("USA_039","usability","No Search",[{'parameter':'search_available','operator':'==','value':False}],{'search_ux':'missing'},0.80,7,"low","No search. Add for apps with lots of content."),
    Rule("USA_040","usability","Consistent Design",[{'parameter':'design_consistency_score','operator':'>=','value':0.8}],{'design':'consistent'},0.85,9,"info","Consistent design language throughout app."),
    Rule("USA_041","usability","Inconsistent Design",[{'parameter':'design_consistency_score','operator':'<','value':0.8}],{'design':'inconsistent'},0.85,7,"medium","Inconsistent design. Standardize components and spacing."),
    Rule("USA_042","usability","Quick Undo",[{'parameter':'undo_available','operator':'==','value':True}],{'undo_support':'available'},0.80,8,"info","Undo functionality available. Forgiving interface."),
    Rule("USA_043","usability","No Undo",[{'parameter':'undo_available','operator':'==','value':False}],{'undo_support':'missing'},0.80,7,"low","No undo. Add for destructive actions."),
    Rule("USA_044","usability","Good Haptic Feedback",[{'parameter':'haptic_feedback','operator':'==','value':True}],{'haptic':'enabled'},0.75,8,"info","Haptic feedback enabled. Enhanced touch experience."),
    Rule("USA_045","usability","Gesture Support",[{'parameter':'gesture_navigation','operator':'==','value':True}],{'gestures':'supported'},0.75,8,"info","Gesture navigation supported. Modern UX."),
    Rule("USA_046","usability","Dark Mode",[{'parameter':'dark_mode_available','operator':'==','value':True}],{'dark_mode':'available'},0.80,8,"info","Dark mode available. Good for low-light and battery."),
    Rule("USA_047","usability","No Dark Mode",[{'parameter':'dark_mode_available','operator':'==','value':False}],{'dark_mode':'missing'},0.80,7,"low","No dark mode. Consider adding for user comfort."),
    Rule("USA_048","usability","Multi-Language",[{'parameter':'languages_supported','operator':'>=','value':2}],{'localization':'multilingual'},0.80,8,"info","Multi-language support. Wider audience reach."),
    Rule("USA_049","usability","Single Language",[{'parameter':'languages_supported','operator':'==','value':1}],{'localization':'single'},0.80,7,"low","Single language only. Consider localization."),
    Rule("USA_050","usability","Good Form UX",[{'parameter':'form_validation_inline','operator':'==','value':True}],{'form_ux':'good'},0.85,8,"info","Inline form validation. Good user guidance."),
    Rule("USA_051","usability","Poor Form UX",[{'parameter':'form_validation_inline','operator':'==','value':False}],{'form_ux':'poor'},0.85,7,"medium","No inline validation. Users submit errors. Add real-time validation."),

    # === FAULT TOLERANCE (35 rules) ===
    Rule("FT_001","fault_tolerance","Instant Recovery",[{'parameter':'mean_recovery_time','operator':'<','value':0.5}],{'recovery_rating':'instant','recovery_score':100},0.95,10,"info","Instant recovery (<0.5s). Outstanding fault tolerance."),
    Rule("FT_002","fault_tolerance","Fast Recovery",[{'parameter':'mean_recovery_time','operator':'>=','value':0.5},{'parameter':'mean_recovery_time','operator':'<','value':1.0}],{'recovery_rating':'fast','recovery_score':90},0.90,9,"info","Fast recovery (0.5-1s). Very good fault tolerance."),
    Rule("FT_003","fault_tolerance","Good Recovery",[{'parameter':'mean_recovery_time','operator':'>=','value':1.0},{'parameter':'mean_recovery_time','operator':'<','value':2.0}],{'recovery_rating':'good','recovery_score':80},0.85,9,"info","Good recovery (1-2s). Acceptable fault tolerance."),
    Rule("FT_004","fault_tolerance","Moderate Recovery",[{'parameter':'mean_recovery_time','operator':'>=','value':2.0},{'parameter':'mean_recovery_time','operator':'<','value':3.0}],{'recovery_rating':'moderate','recovery_score':65},0.85,8,"low","Moderate recovery (2-3s). Consider faster recovery mechanisms."),
    Rule("FT_005","fault_tolerance","Slow Recovery",[{'parameter':'mean_recovery_time','operator':'>=','value':3.0},{'parameter':'mean_recovery_time','operator':'<','value':5.0}],{'recovery_rating':'slow','recovery_score':45},0.90,7,"medium","Slow recovery (3-5s). Implement faster error recovery patterns."),
    Rule("FT_006","fault_tolerance","Very Slow Recovery",[{'parameter':'mean_recovery_time','operator':'>=','value':5.0},{'parameter':'mean_recovery_time','operator':'<','value':10.0}],{'recovery_rating':'very_slow','recovery_score':25},0.90,6,"high","Very slow recovery (5-10s). Users will force-quit."),
    Rule("FT_007","fault_tolerance","Failed Recovery",[{'parameter':'mean_recovery_time','operator':'>=','value':10.0}],{'recovery_rating':'failed','recovery_score':10},0.95,5,"critical","Recovery takes >10s. App cannot recover gracefully. Major redesign needed."),
    Rule("FT_008","fault_tolerance","Excellent Offline",[{'parameter':'offline_features_available','operator':'>=','value':0.8}],{'offline_capability':'excellent','offline_score':100},0.90,10,"info","Excellent offline support (80%+ features available)."),
    Rule("FT_009","fault_tolerance","Good Offline",[{'parameter':'offline_features_available','operator':'>=','value':0.5},{'parameter':'offline_features_available','operator':'<','value':0.8}],{'offline_capability':'good','offline_score':75},0.85,9,"info","Good offline support (50-80% features)."),
    Rule("FT_010","fault_tolerance","Limited Offline",[{'parameter':'offline_features_available','operator':'>=','value':0.2},{'parameter':'offline_features_available','operator':'<','value':0.5}],{'offline_capability':'limited','offline_score':50},0.85,8,"low","Limited offline support. Cache more data for offline use."),
    Rule("FT_011","fault_tolerance","Minimal Offline",[{'parameter':'offline_features_available','operator':'>=','value':0.01},{'parameter':'offline_features_available','operator':'<','value':0.2}],{'offline_capability':'minimal','offline_score':30},0.85,7,"medium","Minimal offline support. Most features need network."),
    Rule("FT_012","fault_tolerance","No Offline",[{'parameter':'offline_features_available','operator':'<','value':0.01}],{'offline_capability':'none','offline_score':10},0.90,7,"medium","No offline support. App unusable without network."),
    Rule("FT_013","fault_tolerance","State Preserved",[{'parameter':'state_preservation_rate','operator':'>=','value':0.95}],{'state_handling':'excellent','state_score':100},0.90,10,"info","State preserved reliably (95%+). No data loss on interruption."),
    Rule("FT_014","fault_tolerance","Good State Handling",[{'parameter':'state_preservation_rate','operator':'>=','value':0.8},{'parameter':'state_preservation_rate','operator':'<','value':0.95}],{'state_handling':'good','state_score':75},0.85,8,"low","Good state handling (80-95%). Some data loss possible."),
    Rule("FT_015","fault_tolerance","Poor State Handling",[{'parameter':'state_preservation_rate','operator':'<','value':0.8}],{'state_handling':'poor','state_score':40},0.90,7,"medium","Poor state preservation (<80%). Users lose progress."),
    Rule("FT_016","fault_tolerance","Auto Retry Works",[{'parameter':'auto_retry_success_rate','operator':'>=','value':0.9}],{'retry_mechanism':'effective'},0.85,9,"info","Auto-retry mechanism effective (90%+ success)."),
    Rule("FT_017","fault_tolerance","Poor Auto Retry",[{'parameter':'auto_retry_success_rate','operator':'<','value':0.9}],{'retry_mechanism':'ineffective'},0.85,7,"medium","Auto-retry mechanism needs improvement."),
    Rule("FT_018","fault_tolerance","Good Cache Strategy",[{'parameter':'cache_hit_rate','operator':'>=','value':0.8}],{'caching':'effective'},0.85,9,"info","Effective caching (80%+ hit rate). Good performance."),
    Rule("FT_019","fault_tolerance","Poor Cache Strategy",[{'parameter':'cache_hit_rate','operator':'<','value':0.8}],{'caching':'ineffective'},0.85,7,"medium","Poor cache hit rate (<80%). Optimize caching strategy."),
    Rule("FT_020","fault_tolerance","Network Switch OK",[{'parameter':'network_switch_handled','operator':'==','value':True}],{'network_switch':'handled'},0.85,9,"info","WiFi/cellular transitions handled smoothly."),
    Rule("FT_021","fault_tolerance","Network Switch Fails",[{'parameter':'network_switch_handled','operator':'==','value':False}],{'network_switch':'fails'},0.85,7,"medium","Network transitions cause issues. Implement network monitoring."),
    Rule("FT_022","fault_tolerance","Graceful Timeout",[{'parameter':'timeout_graceful','operator':'==','value':True}],{'timeout_ux':'graceful'},0.85,9,"info","Timeouts handled gracefully with user feedback."),
    Rule("FT_023","fault_tolerance","Abrupt Timeout",[{'parameter':'timeout_graceful','operator':'==','value':False}],{'timeout_ux':'abrupt'},0.85,7,"medium","Abrupt timeout behavior. Show retry options and explain."),
    Rule("FT_024","fault_tolerance","Data Sync Reliable",[{'parameter':'sync_conflict_resolution','operator':'==','value':True}],{'data_sync':'reliable'},0.85,9,"info","Data sync with conflict resolution. Reliable multi-device."),
    Rule("FT_025","fault_tolerance","No Conflict Resolution",[{'parameter':'sync_conflict_resolution','operator':'==','value':False}],{'data_sync':'unreliable'},0.85,7,"medium","No sync conflict resolution. Risk of data overwrites."),
    Rule("FT_026","fault_tolerance","Battery Save Mode OK",[{'parameter':'battery_save_mode_handled','operator':'==','value':True}],{'battery_save':'handled'},0.80,8,"info","Handles battery save mode correctly."),
    Rule("FT_027","fault_tolerance","No Battery Save Handling",[{'parameter':'battery_save_mode_handled','operator':'==','value':False}],{'battery_save':'unhandled'},0.80,7,"low","Doesn't handle battery save mode. Background features may fail."),
    Rule("FT_028","fault_tolerance","Permission Denial Handled",[{'parameter':'permission_denial_handled','operator':'==','value':True}],{'permission_ft':'graceful'},0.85,9,"info","Permission denials handled gracefully."),
    Rule("FT_029","fault_tolerance","Permission Denial Crashes",[{'parameter':'permission_denial_handled','operator':'==','value':False}],{'permission_ft':'crashes'},0.90,6,"high","App crashes when permissions denied. Handle all states."),
    Rule("FT_030","fault_tolerance","Low Memory Handling",[{'parameter':'low_memory_handling','operator':'==','value':True}],{'low_mem_ft':'handled'},0.85,9,"info","Low memory conditions handled. App reduces footprint."),
    Rule("FT_031","fault_tolerance","No Low Memory Handling",[{'parameter':'low_memory_handling','operator':'==','value':False}],{'low_mem_ft':'unhandled'},0.85,7,"medium","No low memory handling. App will be killed by OS."),
    Rule("FT_032","fault_tolerance","Interrupt Recovery",[{'parameter':'interrupt_recovery_rate','operator':'>=','value':0.9}],{'interrupt_handling':'good'},0.85,9,"info","Handles interrupts well (calls, notifications)."),
    Rule("FT_033","fault_tolerance","Poor Interrupt Recovery",[{'parameter':'interrupt_recovery_rate','operator':'<','value':0.9}],{'interrupt_handling':'poor'},0.85,7,"medium","Poor interrupt recovery. Save state before yielding focus."),
    Rule("FT_034","fault_tolerance","Background Refresh OK",[{'parameter':'background_refresh_reliable','operator':'==','value':True}],{'bg_refresh':'reliable'},0.80,8,"info","Background refresh works reliably."),
    Rule("FT_035","fault_tolerance","Background Refresh Fails",[{'parameter':'background_refresh_reliable','operator':'==','value':False}],{'bg_refresh':'unreliable'},0.80,7,"medium","Background refresh unreliable. Check scheduling and constraints."),
]

# Inference Engine
def forward_chain(facts, max_iter=1000):
    working_memory = facts.copy()
    fired = set()
    fired_details = []
    iteration = 0
    
    while iteration < max_iter:
        applicable = [r for r in RULES if r.matches(working_memory) and r.rule_id not in fired]
        if not applicable:
            break
        selected = max(applicable, key=lambda r: r.priority)
        working_memory.update(selected.consequences)
        fired.add(selected.rule_id)
        fired_details.append({
            'rule_id': selected.rule_id,
            'name': selected.name,
            'dimension': selected.dimension,
            'severity': selected.severity,
            'confidence': selected.confidence,
            'recommendation': selected.recommendation
        })
        iteration += 1
    
    working_memory['fired_rules'] = fired_details
    working_memory['iterations'] = iteration
    working_memory['total_rules_fired'] = len(fired)
    return working_memory

def calculate_crs(result):
    perf_scores = [result.get('startup_score',50), result.get('memory_score',50), result.get('frame_score',50)]
    perf = sum(perf_scores) / len(perf_scores)
    stab = result.get('stability_score', 50)
    usa = result.get('usability_score', 50)
    ft = result.get('recovery_score', 50)
    return round((0.25*perf + 0.25*stab + 0.25*usa + 0.25*ft) / 1.0, 2)

# ============================================================
# API ENDPOINTS
# ============================================================


@app.route('/')
def index():
    return jsonify({'service': 'DiagNova API', 'status': 'running', 'rules': len(RULES)})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'rules_loaded': len(RULES), 'version': '1.0.0'})

@app.route('/api/rules', methods=['GET'])
def get_rules():
    return jsonify({
        'total': len(RULES),
        'performance': len([r for r in RULES if r.dimension == 'performance']),
        'stability': len([r for r in RULES if r.dimension == 'stability']),
        'usability': len([r for r in RULES if r.dimension == 'usability']),
        'fault_tolerance': len([r for r in RULES if r.dimension == 'fault_tolerance']),
    })

@app.route('/api/assess', methods=['POST'])
def assess():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    perf = data.get('performance', {})
    stab = data.get('stability', {})
    usa = data.get('usability', {})
    ft = data.get('fault_tolerance', {})
    
    mem_avail = perf.get('memory_available', 1)
    if mem_avail == 0: mem_avail = 1
    sessions = stab.get('sessions', 1)
    if sessions == 0: sessions = 1
    comp_rate = usa.get('completion_rate', 0.01)
    if comp_rate == 0: comp_rate = 0.01
    
    recovery_times = ft.get('recovery_times', [0])
    if not recovery_times: recovery_times = [0]
    
    facts = {
        'app_name': data.get('app_name', 'Unknown'),
        'platform': data.get('platform', 'Android'),
        'startup_time': perf.get('startup_time', 0),
        'memory_efficiency_ratio': (perf.get('memory_used', 0) / mem_avail) * 100,
        'frame_rate_consistency': (perf.get('frame_rate', 60) / 60) * 100,
        'crash_rate': (stab.get('crashes', 0) / sessions) * 100,
        'interface_complexity_coefficient': (usa.get('screens', 1) * usa.get('interactions_per_task', 1)) / comp_rate,
        'mean_recovery_time': sum(recovery_times) / len(recovery_times),
    }
    
    result = forward_chain(facts)
    crs = calculate_crs(result)
    
    perf_scores = [result.get('startup_score',50), result.get('memory_score',50), result.get('frame_score',50)]
    perf_avg = round(sum(perf_scores)/len(perf_scores), 2)
    
    issues = []
    recs = []
    for fr in result.get('fired_rules', []):
        if fr['severity'] in ['critical', 'high', 'medium']:
            issues.append({
                'dimension': fr['dimension'],
                'severity': fr['severity'],
                'issue': fr['name'],
                'rule_id': fr['rule_id']
            })
        recs.append(fr['recommendation'])
    
    # Remove duplicate recommendations
    seen = set()
    unique_recs = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique_recs.append(r)
    
    return jsonify({
        'app_name': facts['app_name'],
        'platform': facts['platform'],
        'composite_score': crs,
        'dimensions': {
            'performance': perf_avg,
            'stability': result.get('stability_score', 50),
            'usability': result.get('usability_score', 50),
            'fault_tolerance': result.get('recovery_score', 50)
        },
        'metrics': {
            'startup_time_ms': facts['startup_time'],
            'memory_efficiency_ratio': round(facts['memory_efficiency_ratio'], 2),
            'frame_rate_consistency': round(facts['frame_rate_consistency'], 2),
            'crash_rate': round(facts['crash_rate'], 4),
            'interface_complexity': round(facts['interface_complexity_coefficient'], 2),
            'mean_recovery_time': round(facts['mean_recovery_time'], 2)
        },
        'issues': issues,
        'recommendations': unique_recs[:10],
        'rules_fired': result.get('total_rules_fired', 0),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"DiagNova API starting on port {port} with {len(RULES)} rules loaded")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')

