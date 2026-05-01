"""
Playwright 渲染脚本 · 把 216 张 HTML 渲染成 1080×1440 PNG
跟小红书 / Chromium 显示一致

使用方法:
1. 安装依赖
   pip install playwright pillow
   playwright install chromium

2. 在 csp-s 项目根目录运行
   python 渲染_playwright.py

3. 输出到 导出图片_chromium/ 目录,跟 HTML 同结构

可选参数 (在脚本里改):
- DPR  · device pixel ratio (1=1080×1440 / 2=2160×2880 高清)
- WAIT · 每张图等待加载毫秒数,字体加载慢可调到 1500
- THREADS · 并行渲染数,默认 4
"""

from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys, time

# 配置
DPR = 1                  # 1 = 标准 / 2 = 高清 (文件更大)
WAIT = 800               # 字体 / 渐变加载等待 (毫秒)
THREADS = 4              # 并行
ROOT = Path(__file__).parent
SRC_DIRS = ['设计', 'GESP设计', '零基础', 'ai课程', '机构宣传']
OUT = ROOT / '导出图片_chromium'

def collect_files():
    files = []
    for d in SRC_DIRS:
        files.extend((ROOT / d).rglob('*.html'))
    return sorted(files)

def render_one(playwright, html_file):
    rel = html_file.relative_to(ROOT)
    out_path = OUT / rel.with_suffix('.png')
    out_path.parent.mkdir(parents=True, exist_ok=True)

    browser = playwright.chromium.launch()
    page = browser.new_page(
        viewport={'width': 1080, 'height': 1440},
        device_scale_factor=DPR,
    )
    page.goto(html_file.as_uri(), wait_until='networkidle')
    page.wait_for_timeout(WAIT)
    page.screenshot(
        path=str(out_path),
        clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1440},
        omit_background=False,
    )
    browser.close()
    return rel

def main():
    files = collect_files()
    total = len(files)
    print(f'共 {total} 张 HTML · 开始 Chromium 渲染 (DPR={DPR}, 并行={THREADS})\n')
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    done = 0
    with sync_playwright() as p:
        # Playwright 浏览器实例不能跨线程共享 · 每线程一个
        def worker(f):
            with sync_playwright() as pw:
                return render_one(pw, f)

        with ThreadPoolExecutor(max_workers=THREADS) as ex:
            futures = {ex.submit(worker, f): f for f in files}
            for fut in as_completed(futures):
                done += 1
                try:
                    rel = fut.result()
                    if done % 10 == 0 or done == total:
                        elapsed = time.time() - t0
                        eta = elapsed / done * (total - done)
                        print(f'  [{done}/{total}] 用时 {elapsed:.0f}s · 剩 {eta:.0f}s')
                except Exception as e:
                    print(f'  ERR: {futures[fut]}: {e}')

    print(f'\n✓ 全部完成 · 用时 {time.time()-t0:.0f}s')
    print(f'输出目录: {OUT}')

if __name__ == '__main__':
    main()
