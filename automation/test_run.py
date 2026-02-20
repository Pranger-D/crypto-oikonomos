import sys; import traceback; sys.stdout.reconfigure(encoding='utf-8'); import v3_auto_blogger
try:
    v3_auto_blogger.run_v3_automation()
except Exception as e:
    with open('out.log', 'w', encoding='utf-8') as f:
        f.write(traceback.format_exc())
