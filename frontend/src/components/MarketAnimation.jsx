import React, { useEffect, useRef, useState } from 'react';
import { useTheme } from '../hooks/useTheme';

export default function MarketAnimation() {
  const { theme } = useTheme();
  const svgRef = useRef(null);
  const animRef = useRef(null);
  const [demoPrice, setDemoPrice] = useState(148.20);
  const [pctChange, setPctChange] = useState(+4.2);
  const [activityCount, setActivityCount] = useState(1248);

  useEffect(() => {
    const isDark = theme === 'dark' || document.documentElement.classList.contains('dark');
    const stage = svgRef.current;
    if (!stage) return;

    // Remove previously generated elements
    const candleGroup = stage.querySelector('#candles-layer');
    const curvesGroup = stage.querySelector('#curves-layer');
    if (!candleGroup || !curvesGroup) return;

    candleGroup.innerHTML = '';
    curvesGroup.innerHTML = '';

    const NS = 'http://www.w3.org/2000/svg';
    const spacing = 24;
    const totalSlots = 28;
    const candles = [];
    let seed = 19;
    let lastClose = 145;

    function nextRand() {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    }

    function createCandle(xPos, idx) {
      const drift = Math.sin(idx * 0.42) * 14 + (nextRand() - 0.48) * 32;
      const open = lastClose;
      let close = Math.max(50, Math.min(220, open - drift));
      if (Math.abs(close - open) < 6) {
        close = open + (drift >= 0 ? -10 : 10);
        close = Math.max(50, Math.min(220, close));
      }
      const topBody = Math.min(open, close);
      const botBody = Math.max(open, close);
      const high = Math.max(20, topBody - (6 + nextRand() * 22));
      const low = Math.min(260, botBody + (6 + nextRand() * 22));
      const bull = close < open;
      lastClose = close;

      const g = document.createElementNS(NS, 'g');
      const wick = document.createElementNS(NS, 'line');
      const body = document.createElementNS(NS, 'rect');

      const color = bull
        ? (isDark ? '#34D399' : '#16805A')
        : (isDark ? '#FB7185' : '#C23548');

      wick.setAttribute('x1', '0');
      wick.setAttribute('x2', '0');
      wick.setAttribute('y1', high.toFixed(1));
      wick.setAttribute('y2', low.toFixed(1));
      wick.setAttribute('stroke', color);
      wick.setAttribute('stroke-width', '1.6');
      wick.setAttribute('stroke-linecap', 'round');
      wick.setAttribute('stroke-opacity', '0.75');

      const bodyH = Math.max(5, botBody - topBody);
      body.setAttribute('x', '-5');
      body.setAttribute('y', topBody.toFixed(1));
      body.setAttribute('width', '10');
      body.setAttribute('height', bodyH.toFixed(1));
      body.setAttribute('rx', '2');
      body.setAttribute('fill', color);
      body.setAttribute('fill-opacity', bull ? '0.75' : '0.70');
      body.setAttribute('stroke', color);
      body.setAttribute('stroke-width', '1');

      g.appendChild(wick);
      g.appendChild(body);
      candleGroup.appendChild(g);

      return {
        el: g,
        wick,
        body,
        x: xPos,
        bull,
        baseY: topBody,
        baseH: bodyH,
        high,
        low,
        phase: idx * 0.7
      };
    }

    for (let i = 0; i < totalSlots; i++) {
      candles.push(createCandle(i * spacing, i));
    }
    let nextIdx = totalSlots;

    // Dual Trend Lines Paths
    const pathPrimary = document.createElementNS(NS, 'path');
    const pathSecondary = document.createElementNS(NS, 'path');
    const primaryColor = isDark ? '#CE4DDB' : '#6EB8E1';
    const secondaryColor = isDark ? '#A59ADB' : '#C8ABE6';

    pathPrimary.setAttribute('fill', 'none');
    pathPrimary.setAttribute('stroke', primaryColor);
    pathPrimary.setAttribute('stroke-width', '2.5');
    pathPrimary.setAttribute('stroke-linecap', 'round');
    pathPrimary.setAttribute('stroke-linejoin', 'round');
    pathPrimary.setAttribute('stroke-opacity', '0.9');

    pathSecondary.setAttribute('fill', 'none');
    pathSecondary.setAttribute('stroke', secondaryColor);
    pathSecondary.setAttribute('stroke-width', '2');
    pathSecondary.setAttribute('stroke-dasharray', '5 4');
    pathSecondary.setAttribute('stroke-linecap', 'round');
    pathSecondary.setAttribute('stroke-opacity', '0.8');

    // Glowing signal points
    const signal1 = document.createElementNS(NS, 'circle');
    signal1.setAttribute('r', '5');
    signal1.setAttribute('fill', primaryColor);
    signal1.setAttribute('filter', isDark ? 'url(#glowDark)' : 'url(#glowLight)');

    const signal2 = document.createElementNS(NS, 'circle');
    signal2.setAttribute('r', '4');
    signal2.setAttribute('fill', secondaryColor);

    curvesGroup.appendChild(pathPrimary);
    curvesGroup.appendChild(pathSecondary);
    curvesGroup.appendChild(signal1);
    curvesGroup.appendChild(signal2);

    const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function render(t) {
      const bullCol = isDark ? '#34D399' : '#16805A';
      const bearCol = isDark ? '#FB7185' : '#C23548';

      // Update candles
      for (let i = 0; i < candles.length; i++) {
        const c = candles[i];
        const edgeFade = Math.max(0, Math.min(1, c.x / 45, (600 - c.x) / 45));
        const breath = Math.sin(t * 2.2 + c.phase) * 1.8;
        const h = Math.max(4, c.baseH + breath);
        const y = c.baseY - breath * 0.5;
        c.body.setAttribute('y', y.toFixed(1));
        c.body.setAttribute('height', h.toFixed(1));
        c.el.setAttribute('transform', `translate(${c.x.toFixed(2)}, 0)`);
        c.el.setAttribute('opacity', (edgeFade * 0.85).toFixed(3));
        const col = c.bull ? bullCol : bearCol;
        c.wick.setAttribute('stroke', col);
        c.body.setAttribute('fill', col);
        c.body.setAttribute('stroke', col);
      }

      // Generate dynamic dual curves
      const pts1 = [];
      const pts2 = [];
      const step = 20;
      for (let x = 0; x <= 600; x += step) {
        const y1 = 120 + Math.sin(x * 0.015 + t * 1.5) * 35 + Math.cos(x * 0.028 - t * 0.8) * 18;
        const y2 = 145 + Math.cos(x * 0.018 + t * 1.2) * 28 + Math.sin(x * 0.035 + t * 0.9) * 16;
        pts1.push(`${x.toFixed(1)},${y1.toFixed(1)}`);
        pts2.push(`${x.toFixed(1)},${y2.toFixed(1)}`);
      }
      pathPrimary.setAttribute('d', 'M ' + pts1.join(' L '));
      pathSecondary.setAttribute('d', 'M ' + pts2.join(' L '));

      // Signal 1 moves along primary curve
      const sig1X = (300 + Math.sin(t * 1.8) * 180 + 600) % 600;
      const sig1Y = 120 + Math.sin(sig1X * 0.015 + t * 1.5) * 35 + Math.cos(sig1X * 0.028 - t * 0.8) * 18;
      signal1.setAttribute('cx', sig1X.toFixed(1));
      signal1.setAttribute('cy', sig1Y.toFixed(1));

      // Signal 2 moves along secondary curve
      const sig2X = (150 + Math.cos(t * 1.4) * 200 + 600) % 600;
      const sig2Y = 145 + Math.cos(sig2X * 0.018 + t * 1.2) * 28 + Math.sin(sig2X * 0.035 + t * 0.9) * 16;
      signal2.setAttribute('cx', sig2X.toFixed(1));
      signal2.setAttribute('cy', sig2Y.toFixed(1));
    }

    if (reduceMotion) {
      render(0);
      return;
    }

    let lastTs = null;
    let elapsed = 0;
    const speed = 26; // px per second leftward

    function tick(ts) {
      if (lastTs === null) lastTs = ts;
      const dt = Math.min(0.05, (ts - lastTs) / 1000);
      lastTs = ts;
      elapsed += dt;

      const dx = speed * dt;
      let maxX = -Infinity;
      for (let i = 0; i < candles.length; i++) {
        candles[i].x -= dx;
        if (candles[i].x > maxX) maxX = candles[i].x;
      }

      for (let j = 0; j < candles.length; j++) {
        if (candles[j].x < -spacing) {
          candleGroup.removeChild(candles[j].el);
          maxX += spacing;
          candles[j] = createCandle(maxX, nextIdx++);
        }
      }

      render(elapsed);
      animRef.current = requestAnimationFrame(tick);
    }

    animRef.current = requestAnimationFrame(tick);

    // Periodically update subtle synthetic indicator metrics
    const interval = setInterval(() => {
      setDemoPrice(prev => +(prev + (Math.random() - 0.48) * 0.6).toFixed(2));
      setPctChange(prev => +(prev + (Math.random() - 0.49) * 0.2).toFixed(1));
      setActivityCount(prev => prev + (Math.random() > 0.6 ? 1 : 0));
    }, 2800);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      clearInterval(interval);
    };
  }, [theme]);

  return (
    <div className="relative w-full flex flex-col gap-gutter-md">
      {/* SVG Animation Stage */}
      <div className="relative w-full rounded-lg bg-light-surface/40 dark:bg-dark-surface-container-low/40 border border-light-outline-variant/60 dark:border-dark-outline-variant/60 p-2 overflow-hidden">
        <svg
          ref={svgRef}
          viewBox="0 0 600 280"
          className="w-full h-52 sm:h-64 lg:h-72 overflow-hidden"
          role="img"
          aria-label="Continuous animated financial market demonstration"
        >
          <defs>
            <filter id="glowLight" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="glowDark" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <g id="candles-layer" opacity="0.65" />
          <g id="curves-layer" />
        </svg>

        {/* Floating Financial Information Cards (Section 5 requirement) */}
        <div className="pointer-events-none absolute top-4 left-4 z-20">
          <div className="float-card-a p-2.5 rounded-DEFAULT bg-light-surface/90 dark:bg-dark-surface-container/90 backdrop-blur-md border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5 font-mono text-mono-sm">
                <span className="font-bold text-light-on-surface dark:text-dark-on-surface">MGS (DEMO)</span>
                <span className="tabular-nums text-emerald-600 dark:text-emerald-400 font-semibold">${demoPrice.toFixed(2)}</span>
                <span className={`text-[10px] font-semibold px-1 rounded ${pctChange >= 0 ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-rose-500/15 text-rose-600 dark:text-rose-400'}`}>
                  {pctChange >= 0 ? `+${pctChange}%` : `${pctChange}%`}
                </span>
              </div>
              <span className="text-[10px] uppercase font-mono tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant">
                SYNTHETIC DEMO PRICE
              </span>
            </div>
          </div>
        </div>

        <div className="pointer-events-none absolute bottom-5 right-4 z-20 hidden sm:block">
          <div className="float-card-b p-2.5 rounded-DEFAULT bg-light-surface/90 dark:bg-dark-surface-container/90 backdrop-blur-md border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-light-primary-container dark:bg-dark-primary-container flex items-center justify-center text-light-on-primary-container dark:text-dark-on-primary-container">
              <span className="material-symbols-outlined text-[16px]">show_chart</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2 font-mono text-mono-sm">
                <span className="text-light-on-surface dark:text-dark-on-surface font-semibold">Signal Volatility: 0.34</span>
                <svg className="w-12 h-4 text-light-primary dark:text-dark-primary" viewBox="0 0 50 15">
                  <path d="M0,12 Q12,2 25,9 T50,4" fill="none" stroke="currentColor" strokeWidth="2" />
                </svg>
              </div>
              <span className="text-[10px] uppercase font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                DEMONSTRATION MOVEMENT INDICATOR
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Synthetic Demonstration Counter & Notice */}
      <div className="flex flex-wrap items-center justify-between gap-gutter-sm">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded-sm font-mono text-mono-sm bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container">
            SYNTHETIC / DEMONSTRATION DATA
          </span>
          <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant font-mono tabular-nums">
            {activityCount.toLocaleString()} demo signals processed
          </span>
        </div>
        <span className="text-[11px] text-light-on-surface-variant dark:text-dark-on-surface-variant italic">
          Never real-time financial advice
        </span>
      </div>
    </div>
  );
}
